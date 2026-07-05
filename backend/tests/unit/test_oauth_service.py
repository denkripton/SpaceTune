from unittest.mock import AsyncMock

import pytest
import respx
from httpx import Response

from src.config import settings
from src.utils.exceptions import ServiceError
from src.modules.auth.services.oauth import OAuthService
from tests.factories import make_fake_user


@pytest.fixture
def oauth_service(user_repo, fake_jwt):
    return OAuthService(repo=user_repo, jwt=fake_jwt)


def mock_google_token_endpoint(
    access_token="fake-google-access-token", status_code=200
):
    return respx.post(OAuthService.GOOGLE_TOKEN_URL).mock(
        return_value=Response(status_code, json={"access_token": access_token})
    )


def mock_google_userinfo_endpoint(
    sub="google-sub-123",
    email="oauthuser@gmail.com",
    name="OAuth User",
    status_code=200,
):
    return respx.get(settings.GOOGLE_USERINFO_URL).mock(
        return_value=Response(
            status_code, json={"sub": sub, "email": email, "name": name}
        )
    )


@respx.mock
async def test_login_raises_422_when_token_exchange_fails(oauth_service):
    mock_google_token_endpoint(status_code=400)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(code="expired-or-invalid-code")

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Failed to exchange OAuth code"


@respx.mock
async def test_login_raises_422_when_userinfo_fetch_fails(oauth_service):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(status_code=401)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(code="some-code")

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Failed to exchange OAuth code"


@respx.mock
async def test_login_does_not_create_duplicate_when_google_id_already_linked(
    oauth_service, user_repo, fake_jwt
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(sub="google-sub-123", email="oauthuser@gmail.com")

    existing_user = make_fake_user(
        username="oauthuser", email="oauthuser@gmail.com", google_id="google-sub-123"
    )
    user_repo.get_one = AsyncMock(return_value=existing_user)

    result = await oauth_service.login(code="valid-code")

    user_repo.create.assert_not_called()
    user_repo.session.commit.assert_not_called()

    assert result == {"access": "fake.access.token", "refresh": "fake.refresh.token"}
    fake_jwt.create_access_token.assert_called_once_with(str(existing_user.id))


@respx.mock
async def test_login_links_google_id_to_existing_account_with_same_email(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(sub="new-google-sub", email="existing@example.com")

    existing_user = make_fake_user(
        username="existinguser", email="existing@example.com", google_id=None
    )
    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=existing_user)

    await oauth_service.login(code="valid-code")

    user_repo.create.assert_not_called()
    assert existing_user.google_id == "new-google-sub"
    user_repo.session.commit.assert_awaited_once()


@respx.mock
async def test_login_creates_new_user_when_no_existing_account_found(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="brand-new-sub", email="brandnew@example.com", name="Brand New"
    )

    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=None)

    created_user = make_fake_user(
        username="Brand New", email="brandnew@example.com", google_id="brand-new-sub"
    )
    user_repo.create = AsyncMock(return_value=created_user)

    await oauth_service.login(code="valid-code")

    user_repo.create.assert_awaited_once()
    _, create_kwargs = user_repo.create.call_args
    assert create_kwargs["email"] == "brandnew@example.com"
    assert create_kwargs["google_id"] == "brand-new-sub"
    assert create_kwargs["password"] is None
    user_repo.session.commit.assert_awaited_once()


@respx.mock
async def test_login_falls_back_to_email_prefix_when_google_name_is_missing(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    respx.get(settings.GOOGLE_USERINFO_URL).mock(
        return_value=Response(
            200, json={"sub": "no-name-sub", "email": "justanemail@example.com"}
        )
    )

    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value=make_fake_user())

    await oauth_service.login(code="valid-code")

    _, create_kwargs = user_repo.create.call_args
    assert create_kwargs["username"] == "justanemail"


@respx.mock
async def test_login_truncates_username_to_twenty_characters(oauth_service, user_repo):
    long_name = "A Very Long Display Name From Google"
    assert len(long_name) > 20

    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="long-name-sub", email="longname@example.com", name=long_name
    )

    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value=make_fake_user())

    await oauth_service.login(code="valid-code")

    _, create_kwargs = user_repo.create.call_args
    assert len(create_kwargs["username"]) == 20
    assert create_kwargs["username"] == long_name[:20]


def test_get_redirect_url_includes_required_google_oauth_params(oauth_service):
    url = oauth_service.get_redirect_url()

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert f"client_id={settings.GOOGLE_CLIENT_ID}" in url
    assert f"redirect_uri={settings.GOOGLE_REDIRECT_URI}" in url
    assert "response_type=code" in url
    assert "scope=openid email profile" in url
    assert "access_type=offline" in url
