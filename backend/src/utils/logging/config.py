import logging
import sys
from typing import Callable

import structlog

from src.utils.logging.constants import DEFAULT_QUIETED_LOGGERS
from src.utils.logging.processors import StructlogRedactionProcessor
from src.utils.logging.strategies import is_sensitive_key


class LoggingConfigurator:
    def __init__(
        self,
        stream = sys.stdout,
        is_sensitive_key: Callable[[str], bool] = is_sensitive_key,
        level: int = logging.INFO,
        quieted_loggers = DEFAULT_QUIETED_LOGGERS,
    ):
        self._stream = stream
        self._is_sensitive_key = is_sensitive_key
        self._level = level
        self._quieted_loggers = quieted_loggers

    def configure(self) -> None:
        shared_processors = self._build_shared_processors()
        handler = self._build_handler(shared_processors)
        self._install_root_handler(handler)
        self._quiet_third_party_loggers()
        self._configure_structlog(shared_processors)

    def _build_shared_processors(self) -> list:
        return [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            StructlogRedactionProcessor(self._is_sensitive_key),
        ]

    def _build_handler(self, shared_processors: list) -> logging.Handler:
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=shared_processors,
        )
        handler = logging.StreamHandler(self._stream)
        handler.setFormatter(formatter)
        return handler

    def _install_root_handler(self, handler: logging.Handler) -> None:
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(self._level)

    def _quiet_third_party_loggers(self) -> None:
        for logger_name in self._quieted_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    def _configure_structlog(self, shared_processors: list) -> None:
        structlog.configure(
            processors=shared_processors
            + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def configure_logging() -> None:
    LoggingConfigurator().configure()