from src.utils.exceptions.service_error import ServiceError


class NotFoundError(ServiceError):
    def __init__(self, msg: str = "Not Found", code: int = 404):
        super().__init__(msg, code)
