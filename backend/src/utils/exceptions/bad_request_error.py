from src.utils.exceptions.service_error import ServiceError


class BadRequestError(ServiceError):
    def __init__(self, msg: str = "Bad Request", code: int = 400):
        super().__init__(msg, code)
