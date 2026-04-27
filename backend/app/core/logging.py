"""日志配置模块"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import structlog


def setup_logging(
    level: str = "INFO",
    console: bool = True,
    file: bool = False,
    file_path: str = "logs/app.log",
    error_file: bool = False,
):
    """
    统一日志配置

    Args:
        level: 日志级别
        console: 是否输出到控制台
        file: 是否输出到文件
        file_path: 日志文件路径
        error_file: 是否单独记录错误日志
    """
    # 创建日志目录
    if console or file or error_file:
        Path("logs").mkdir(exist_ok=True)

    # 处理器列表
    handlers = []

    # 控制台 Handler
    if console:
        handlers.append(logging.StreamHandler())

    # 应用日志文件 Handler
    if file:
        handlers.append(
            RotatingFileHandler(
                filename=file_path,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=10,
                encoding="utf-8",
            )
        )

    # 错误日志文件 Handler（仅 ERROR 及以上）
    if error_file:
        error_handler = RotatingFileHandler(
            filename="logs/error.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=30,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        handlers.append(error_handler)

    # 配置 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置根日志
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(message)s", handlers=handlers)


def get_logger(name: str = None):
    """
    获取日志器

    Args:
        name: 模块名称，可选

    Returns:
        structlog.BoundLogger
    """
    return structlog.get_logger() if name is None else structlog.get_logger(name)
