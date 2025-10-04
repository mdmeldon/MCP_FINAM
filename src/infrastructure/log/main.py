import logging.config

import structlog
from structlog.processors import (
    CallsiteParameter,
    CallsiteParameterAdder,
)

from src.configs import LoggerConfig

from .processors import get_render_processor


def configure_logging(cfg: LoggerConfig) -> None:
    common_processors = (
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f", utc=True),
        structlog.contextvars.merge_contextvars,
        structlog.processors.format_exc_info,  # print exceptions from event dict
        CallsiteParameterAdder(
            (
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ),
        ),
    )
    structlog_processors = (
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.UnicodeDecoder(),  # convert bytes to str
        # structlog.stdlib.render_to_log_kwargs,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    )
    logging_processors = (structlog.stdlib.ProcessorFormatter.remove_processors_meta,)
    logging_console_processors = (
        *logging_processors,
        get_render_processor(render_json_logs=cfg.RENDER_JSON_LOGS, colors=True),
    )
    logging_file_processors = (
        *logging_processors,
        get_render_processor(render_json_logs=cfg.RENDER_JSON_LOGS, colors=False),
    )

    handler = logging.StreamHandler()
    handler.set_name("default")
    handler.setLevel(cfg.LEVEL)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=common_processors,  # type: ignore
        processors=logging_console_processors,
    )
    handler.setFormatter(console_formatter)

    handlers: list[logging.Handler] = [handler]
    if cfg.FILE_PATH:
        cfg.FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        log_path = (
            cfg.FILE_PATH / "logs.log" if cfg.FILE_PATH.is_dir() else cfg.FILE_PATH
        )

        file_handler = logging.FileHandler(log_path)
        file_handler.set_name("file")
        file_handler.setLevel(cfg.LEVEL)
        file_formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=common_processors,  # type: ignore
            processors=logging_file_processors,
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    logging.basicConfig(handlers=handlers, level=cfg.LEVEL)
    structlog.configure(
        processors=common_processors + structlog_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        # wrapper_class=structlog.stdlib.AsyncBoundLoggerd,  # type: ignore  # noqa: RUF100
        wrapper_class=structlog.stdlib.BoundLogger,  # type: ignore
        cache_logger_on_first_use=True,
    )
