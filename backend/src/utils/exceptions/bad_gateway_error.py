from src.utils.exceptions.service_error import ServiceError


class BadGatewayError(ServiceError):
    def __init__(self, msg: str = "Bad Gateway", code: int = 502):
        super().__init__(msg, code)
