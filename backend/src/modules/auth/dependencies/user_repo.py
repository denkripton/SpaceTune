from src.dependencies import RepoFactory
from src.modules.auth.repository import UserRepository

user_repository = RepoFactory(repo=UserRepository)
