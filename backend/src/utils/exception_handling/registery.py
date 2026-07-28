from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.utils.exceptions import ServiceError
from src.utils.exception_handling.handlers.http_exception import http_exception_handler
from src.utils.exception_handling.handlers.service_error import service_error_handler
from src.utils.exception_handling.handlers.unhandled import unhandled_exception_handler
from src.utils.exception_handling.handlers.validation import validation_exception_handler


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
