from src.utils.exceptions.service_error import ServiceError


class FileSizeLimitExceeded(ServiceError):
    def __init__(self, msg: str = "Content Too Large", code: int = 413):
        super().__init__(msg, code)
