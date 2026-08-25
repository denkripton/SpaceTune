from src.utils.exceptions.service_error import ServiceError


class ValidationError(ServiceError):
    def __init__(self, msg: str = "Unprocessable Entity", code: int = 422):
        super().__init__(msg, code)
