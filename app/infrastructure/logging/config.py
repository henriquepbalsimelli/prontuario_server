import logging
from pathlib import Path
import sys

import structlog

from app.infrastructure.security.log_masking import mask_event_dict


def _masking_processor(_, __, event_dict):
    return mask_event_dict(event_dict=event_dict)


def _trace_context_processor(_, __, event_dict):
    try:
        from opentelemetry.trace import get_current_span
    except ImportError:
        return event_dict

    span = get_current_span()
    if span is None:
        return event_dict

    span_context = span.get_span_context()
    if not span_context or not span_context.is_valid:
        return event_dict

    event_dict["trace_id"] = f"{span_context.trace_id:032x}"
    event_dict["span_id"] = f"{span_context.span_id:016x}"
    return event_dict


def configure_logging(
    level: str,
    json_logs: bool,
    trace_correlation_enabled: bool = True,
    log_file_path: str | None = None,
) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        *([_trace_context_processor] if trace_correlation_enabled else []),
        _masking_processor,
    ]

    stream_renderer = structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    file_renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    stream_formatter = structlog.stdlib.ProcessorFormatter(
        processor=stream_renderer,
        foreign_pre_chain=shared_processors,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(stream_formatter)
    root_logger.addHandler(stream_handler)

    if log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=file_renderer,
                foreign_pre_chain=shared_processors,
            )
        )
        root_logger.addHandler(file_handler)
