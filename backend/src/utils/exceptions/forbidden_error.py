from src.utils.exceptions.service_error import ServiceError


class ForbiddenError(ServiceError):
    def __init__(self, msg: str = "Forbidden", code: int = 403):
        super().__init__(msg, code)
