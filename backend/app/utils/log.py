# -*- coding: utf-8 -*-
import logging
import os
import re
import structlog
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


_TS_RE = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_LOGGING_CONFIGURED = False


class _StructlogFormatter(logging.Formatter):
    """structlog 消息自带格式；外来日志补时间戳和级别前缀。"""

    def format(self, record):
        record.exc_info = None
        record.exc_text = None
        msg = super().format(record)
        if not _TS_RE.match(_ANSI_RE.sub('', msg)):
            msg = f"{self.formatTime(record)} [{record.levelname:<8s}] {record.name}: {msg}"
        return msg


class StripAnsiFormatter(_StructlogFormatter):
    """文件输出不需要 ANSI 颜色码。"""
    _ansi_re = re.compile(r'\x1b\[[0-9;]*m')

    def format(self, record):
        record.msg = self._ansi_re.sub('', str(record.msg))
        return super().format(record)


def setup_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    env = os.getenv("ENV", "development").lower()
    log_dir = os.getenv(
        "LOG_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "logs")
    )
    is_prod = env in ("production", "prod")

    # 日志加工流水线
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if is_prod:
        processors = shared_processors + [
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                pad_level=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 控制台 —— 用 _StructlogFormatter 防止 traceback 重复
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(_StructlogFormatter("%(message)s"))
    root_logger.addHandler(console)

    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            Path(log_dir) / "rag_agent.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StripAnsiFormatter("%(message)s"))
        root_logger.addHandler(file_handler)
    except OSError:
        root_logger.warning("file_logging_unavailable log_dir=%s", log_dir)

    # 第三方日志降噪
    for ext in ("uvicorn", "uvicorn.error", "mcp", "mcp.server", "mcp.client"):
        _lg = logging.getLogger(ext)
        _lg.handlers.clear()
        _lg.propagate = True
        _lg.setLevel(log_level)


    for name in ("httpx", "langchain_core", "langchain_classic", "sqlalchemy.engine", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)


    _log = structlog.get_logger(__name__)
    _log.info(
        "logging_initialized",
        log_level=log_level,
        env=env,
        log_dir=str(log_dir) if Path(log_dir).exists() else None,
    )
    _LOGGING_CONFIGURED = True


def get_logger(name: str | None = None):
    """各模块用 __name__ 调用，日志自动带上模块来源。"""
    return structlog.get_logger(name)


logger = get_logger(__name__)

if __name__ == "__main__":
    setup_logging()
    logger.info("test_start")
    logger.info("with_params", request_id="test001", duration_ms=456)
    logger.warning("warning_test")
    logger.error("error_test")
    try:
        1 / 0
    except Exception:
        logger.exception("exception_test")
    logger.info("test_complete")
    print(os.getenv("LOG_PATH", str(Path(__file__).resolve().parent.parent.parent / "logs")))
