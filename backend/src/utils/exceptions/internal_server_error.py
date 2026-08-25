from src.utils.exceptions.service_error import ServiceError


class InternalServerError(ServiceError):
    def __init__(self, msg: str = "Internal Server Error", code: int = 500):
        super().__init__(msg, code)
