from src.utils.exceptions.service_error import ServiceError


class UnauthorizedError(ServiceError):
    def __init__(self, msg: str = "Unauthorized", code: int = 401):
        super().__init__(msg, code)
