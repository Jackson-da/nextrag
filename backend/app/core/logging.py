"""日志配置模块 - 企业级结构化日志（统一格式）"""
import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
import structlog
from uuid import uuid4


# 服务信息
SERVICE_NAME = "smart-qa-system"
SERVICE_VERSION = "1.0.0"

# 固定日志字段（每条日志都会包含）
LOG_FIELDS = ["timestamp", "level", "trace_id", "service", "env", "logger", "message"]


def add_service_info(logger, method_name, event_dict):
    """添加服务信息和环境标识"""
    event_dict["service"] = SERVICE_NAME
    event_dict["env"] = os.getenv("ENVIRONMENT", "development")
    return event_dict


def add_trace_id(logger, method_name, event_dict):
    """添加或获取 trace_id"""
    if "trace_id" not in event_dict:
        event_dict["trace_id"] = event_dict.get("_trace_id") or str(uuid4())[:8]
    event_dict.pop("_trace_id", None)
    return event_dict


def standardize_log_structure(logger, method_name, event_dict):
    """
    标准化日志结构 - 确保所有日志都有统一的字段格式
    
    标准格式:
    {
        "timestamp": "2026-04-27T15:30:00.000000+08:00",
        "level": "INFO",
        "trace_id": "a1b2c3d4",
        "service": "smart-qa-system",
        "env": "development",
        "logger": "app.api.user",
        "message": "用户登录成功",
        "extra": {
            "user_id": "123",
            "ip": "192.168.1.1"
        }
    }
    """
    # 1. 确保 level 字段标准化
    if method_name == "warning":
        event_dict["level"] = "WARN"
    elif "level" not in event_dict:
        event_dict["level"] = method_name.upper()
    
    # 2. 提取 message（如果有的话）
    message = event_dict.pop("event", None)
    if message:
        event_dict["message"] = message
    
    # 3. 把非标准字段移到 extra 中
    extra = {}
    for key in list(event_dict.keys()):
        if key not in LOG_FIELDS and not key.startswith("_"):
            extra[key] = event_dict.pop(key)
    
    # 4. 只有 extra 有内容时才添加
    if extra:
        event_dict["extra"] = extra
    
    # 5. 确保时间戳是 ISO 格式
    if "timestamp" in event_dict and "T" not in str(event_dict["timestamp"]):
        try:
            dt = datetime.fromisoformat(event_dict["timestamp"])
            event_dict["timestamp"] = dt.isoformat()
        except (ValueError, TypeError):
            pass
    
    return event_dict


def console_renderer(logger, method_name, event_dict):
    """控制台友好格式渲染器"""
    # 提取固定字段
    level = event_dict.get("level", "INFO")
    timestamp = event_dict.pop("timestamp", "")
    trace_id = event_dict.pop("trace_id", "")
    service = event_dict.pop("service", "")
    logger_name = event_dict.pop("logger", "")
    message = event_dict.pop("message", "")
    event_dict.pop("level", None)
    
    # 提取 extra
    extra = event_dict.pop("extra", {})
    
    # 合并 extra 到 event_dict
    event_dict.update(extra)
    
    # 格式化额外字段
    extras = " ".join(f"{k}={v}" for k, v in event_dict.items() if v is not None and v != "")
    
    # 颜色
    colors = {
        "DEBUG": "\033[36m", "INFO": "\033[32m", "WARN": "\033[33m",
        "ERROR": "\033[31m", "CRITICAL": "\033[35m"
    }
    color = colors.get(level, "")
    reset = "\033[0m"
    
    # 构建输出
    parts = [f"{color}[{timestamp}]{reset}"]
    if trace_id:
        parts.append(f"[{trace_id}]")
    parts.append(f"{color}[{level}]{reset}")
    parts.append(f"[{service}]")
    parts.append(message)
    
    result = " ".join(parts)
    if extras:
        result += f" | {extras}"
    
    return result


def unified_json_renderer(logger, method_name, event_dict):
    """统一 JSON 渲染器 - 确保字段顺序和格式一致"""
    standardize_log_structure(logger, method_name, event_dict)
    
    # 确保字段顺序：timestamp, level, trace_id, service, env, logger, message, extra
    ordered = {}
    for key in LOG_FIELDS:
        if key in event_dict:
            ordered[key] = event_dict.pop(key)
    
    # 添加剩余字段
    ordered.update(event_dict)
    
    return json.dumps(ordered, ensure_ascii=False, default=str)


def setup_logging(
    level: str = "INFO",
    console: bool = True,
    file: bool = False,
    file_path: str = "logs/app.log",
    error_file: bool = False,
    file_max_bytes: int = 100 * 1024 * 1024,
    file_backup_count: int = 10,
    service_name: str = None,
    environment: str = None,
):
    """统一日志配置"""
    global SERVICE_NAME
    if service_name:
        SERVICE_NAME = service_name
    if environment:
        os.environ["ENVIRONMENT"] = environment

    if console or file or error_file:
        Path("logs").mkdir(exist_ok=True)

    handlers = []

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(console_handler)

    if file:
        handlers.append(
            RotatingFileHandler(
                filename=file_path,
                maxBytes=file_max_bytes,
                backupCount=file_backup_count,
                encoding="utf-8",
            )
        )

    if error_file:
        error_handler = RotatingFileHandler(
            filename="logs/error.log",
            maxBytes=50 * 1024 * 1024,
            backupCount=30,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        handlers.append(error_handler)

    # 处理器配置
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_service_info,
        add_trace_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # 根据输出目标选择渲染器
        unified_json_renderer if file else console_renderer,
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=handlers
    )


def get_logger(name: str = None, trace_id: str = None) -> structlog.BoundLogger:
    """获取日志器"""
    logger = structlog.get_logger() if name is None else structlog.get_logger(name)
    
    if trace_id:
        logger = logger.bind(_trace_id=trace_id)
    
    return logger


class LogContext:
    """日志上下文管理器"""
    
    _contexts: list[dict[str, Any]] = []
    
    def __init__(self, **kwargs):
        self.fields = kwargs
        self._previous_context = None
    
    def __enter__(self):
        self._previous_context = LogContext._contexts[-1] if LogContext._contexts else {}
        LogContext._contexts.append({**self._previous_context, **self.fields})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        LogContext._contexts.pop()
        if exc_type:
            logger = get_logger()
            logger.error(
                "异常发生在日志上下文中",
                exception_type=exc_type.__name__,
                exception_message=str(exc_val),
                **self.fields
            )
        return False
    
    @classmethod
    def get_context(cls) -> dict[str, Any]:
        """获取当前上下文"""
        return cls._contexts[-1] if cls._contexts else {}
