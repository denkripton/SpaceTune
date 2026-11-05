from src.utils.exceptions.service_error import ServiceError


class ConflictError(ServiceError):
    def __init__(self, msg: str = "Conflict", code: int = 409):
        super().__init__(msg, code)
