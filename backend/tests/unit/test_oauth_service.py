from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import pytest
import respx
from httpx import Response
from sqlalchemy.exc import IntegrityError
from src.config import settings
from src.modules.auth.services.oauth import OAuthService
from src.utils.exceptions import ServiceError

from tests.factories import make_fake_user


@pytest.fixture
def oauth_service(user_repo, fake_jwt, fake_uow):
    return OAuthService(repo=user_repo, jwt=fake_jwt, uow=fake_uow)


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
    email_verified=True,
    status_code=200,
):
    payload = {"sub": sub, "email": email, "name": name}
    if email_verified is not None:
        payload["email_verified"] = email_verified
    return respx.get(settings.GOOGLE_USERINFO_URL).mock(
        return_value=Response(status_code, json=payload)
    )


@respx.mock
async def test_login_raises_422_when_token_exchange_fails(oauth_service):
    mock_google_token_endpoint(status_code=400)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="expired-or-invalid-code",
            state="matching-state",
            expected_state="matching-state",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Failed to exchange OAuth code"


@respx.mock
async def test_login_raises_422_when_userinfo_fetch_fails(oauth_service):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(status_code=401)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="some-code", state="matching-state", expected_state="matching-state"
        )

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

    result = await oauth_service.login(
        code="valid-code", state="matching-state", expected_state="matching-state"
    )

    user_repo.create.assert_not_called()
    user_repo.session.commit.assert_not_called()

    assert result == {"access": "fake.access.token", "refresh": "fake.refresh.token"}
    fake_jwt.create_access_token.assert_called_once_with(str(existing_user.id))


@respx.mock
async def test_login_links_google_id_to_existing_account_when_email_verified(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="new-google-sub", email="existing@example.com", email_verified=True
    )

    existing_user = make_fake_user(
        username="existinguser", email="existing@example.com", google_id=None
    )
    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=existing_user)

    await oauth_service.login(
        code="valid-code", state="matching-state", expected_state="matching-state"
    )

    user_repo.create.assert_not_called()
    assert existing_user.google_id == "new-google-sub"
    user_repo.session.commit.assert_awaited_once()


@respx.mock
async def test_login_rejects_linking_when_email_not_verified(oauth_service, user_repo):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="attacker-sub", email="victim@example.com", email_verified=False
    )

    victim = make_fake_user(
        username="victim", email="victim@example.com", google_id=None
    )
    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=victim)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    assert victim.google_id is None
    user_repo.create.assert_not_called()
    user_repo.session.commit.assert_not_called()


@respx.mock
async def test_login_rejects_linking_when_email_verified_claim_is_missing(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="attacker-sub", email="victim@example.com", email_verified=None
    )

    victim = make_fake_user(
        username="victim", email="victim@example.com", google_id=None
    )
    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=victim)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    assert victim.google_id is None
    user_repo.session.commit.assert_not_called()


@respx.mock
async def test_login_rejects_linking_when_email_verified_is_truthy_non_bool_string(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="attacker-sub", email="victim@example.com", email_verified="true"
    )

    victim = make_fake_user(
        username="victim", email="victim@example.com", google_id=None
    )
    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=victim)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    assert victim.google_id is None


@respx.mock
async def test_login_rejects_creating_new_account_when_email_not_verified(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="brand-new-sub", email="unverified@example.com", email_verified=False
    )

    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.create.assert_not_called()
    user_repo.session.commit.assert_not_called()


@respx.mock
async def test_login_raises_422_when_concurrent_request_creates_account_first(
    oauth_service, user_repo
):
    """
    Simulates the race window: two concurrent OAuth logins for a brand-new
    email both pass the pre-checks (get_one/get_by_email both return None),
    but the second one's commit() hits the unique constraint because the
    first request already committed. This must surface as a clean 422,
    not an unhandled IntegrityError bubbling up as a 500.
    """
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="racing-sub", email="racing@example.com", name="Racer"
    )

    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(
        return_value=make_fake_user(email="racing@example.com")
    )
    user_repo.session.commit = AsyncMock(
        side_effect=IntegrityError("duplicate key value", {}, Exception())
    )

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.session.rollback.assert_awaited_once()


@respx.mock
async def test_login_raises_422_when_concurrent_request_links_account_first(
    oauth_service, user_repo
):
    """
    Same race, but on the linking path: two concurrent logins for the same
    already-registered email both see google_id unset, but the second
    commit() collides on the unique google_id constraint.
    """
    mock_google_token_endpoint()
    mock_google_userinfo_endpoint(
        sub="racing-sub", email="existing@example.com", email_verified=True
    )

    existing_user = make_fake_user(email="existing@example.com", google_id=None)
    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=existing_user)
    user_repo.session.commit = AsyncMock(
        side_effect=IntegrityError("duplicate key value", {}, Exception())
    )

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.session.rollback.assert_awaited_once()


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

    await oauth_service.login(
        code="valid-code", state="matching-state", expected_state="matching-state"
    )

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
            200,
            json={
                "sub": "no-name-sub",
                "email": "justanemail@example.com",
                "email_verified": True,
            },
        )
    )

    user_repo.get_one = AsyncMock(return_value=None)
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value=make_fake_user())

    await oauth_service.login(
        code="valid-code", state="matching-state", expected_state="matching-state"
    )

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

    await oauth_service.login(
        code="valid-code", state="matching-state", expected_state="matching-state"
    )

    _, create_kwargs = user_repo.create.call_args
    assert len(create_kwargs["username"]) == 20
    assert create_kwargs["username"] == long_name[:20]


@respx.mock
async def test_login_raises_422_when_token_response_missing_access_token(
    oauth_service, user_repo
):
    respx.post(OAuthService.GOOGLE_TOKEN_URL).mock(
        return_value=Response(200, json={"token_type": "Bearer"})
    )

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.get_one.assert_not_called()


@respx.mock
async def test_login_raises_422_when_userinfo_missing_sub(oauth_service, user_repo):
    mock_google_token_endpoint()
    respx.get(settings.GOOGLE_USERINFO_URL).mock(
        return_value=Response(
            200, json={"email": "noSub@example.com", "email_verified": True}
        )
    )

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.get_one.assert_not_called()


@respx.mock
async def test_login_raises_422_when_userinfo_missing_email(oauth_service, user_repo):
    mock_google_token_endpoint()
    respx.get(settings.GOOGLE_USERINFO_URL).mock(
        return_value=Response(200, json={"sub": "sub-no-email", "email_verified": True})
    )

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.get_one.assert_not_called()


@respx.mock
async def test_login_raises_422_when_userinfo_sub_and_email_are_empty_strings(
    oauth_service, user_repo
):
    mock_google_token_endpoint()
    respx.get(settings.GOOGLE_USERINFO_URL).mock(
        return_value=Response(
            200, json={"sub": "", "email": "", "email_verified": True}
        )
    )

    with pytest.raises(ServiceError) as exc_info:
        await oauth_service.login(
            code="valid-code", state="matching-state", expected_state="matching-state"
        )

    assert exc_info.value.status_code == 422
    user_repo.get_one.assert_not_called()


def test_get_redirect_url_includes_required_google_oauth_params(oauth_service):
    url = oauth_service.get_redirect_url(state="test-state")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert parsed.path == "/o/oauth2/v2/auth"
    assert params["client_id"] == [settings.GOOGLE_CLIENT_ID]
    assert params["redirect_uri"] == [settings.GOOGLE_REDIRECT_URI]
    assert params["response_type"] == ["code"]
    assert params["scope"] == ["openid email profile"]
    assert params["access_type"] == ["offline"]
    assert params["state"] == ["test-state"]
