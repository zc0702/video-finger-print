"""
统一的日志配置模块
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    include_console: bool = True,
    log_format: str = 'standard'
) -> None:
    """
    配置统一的日志系统
    
    Args:
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: 日志文件路径，None表示不写文件
        include_console: 是否输出到控制台
        log_format: 日志格式 ('standard', 'detailed', 'simple')
    
    Example:
        >>> setup_logging('DEBUG', 'app.log', include_console=True)
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # 清除现有的handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    handlers = []
    
    # 选择格式
    formats = {
        'standard': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        'simple': '%(levelname)s: %(message)s'
    }
    
    fmt = formats.get(log_format, formats['standard'])
    date_fmt = '%Y-%m-%d %H:%M:%S'
    
    # 控制台输出
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(fmt, datefmt=date_fmt)
        )
        handlers.append(console_handler)
    
    # 文件输出
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter(formats['detailed'], datefmt=date_fmt)
        )
        handlers.append(file_handler)
    
    # 配置根logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True  # 强制重新配置
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取logger实例
    
    Args:
        name: logger名称，通常使用 __name__
        
    Returns:
        配置好的logger实例
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello World")
    """
    return logging.getLogger(name)


def setup_batch_logging(batch_name: str, log_dir: str = 'logs') -> logging.Logger:
    """
    为批处理任务设置日志
    
    Args:
        batch_name: 批处理任务名称
        log_dir: 日志目录
        
    Returns:
        配置好的logger
        
    Example:
        >>> logger = setup_batch_logging('video_processing')
        >>> logger.info("Batch processing started")
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = Path(log_dir) / f"{batch_name}_{timestamp}.log"
    
    setup_logging(
        level='INFO',
        log_file=str(log_file),
        include_console=True,
        log_format='detailed'
    )
    
    logger = get_logger(batch_name)
    logger.info(f"日志文件: {log_file}")
    
    return logger


class LoggerContext:
    """
    日志上下文管理器
    
    Example:
        >>> with LoggerContext('my_task', 'DEBUG'):
        ...     logger = logging.getLogger(__name__)
        ...     logger.debug("This is a debug message")
    """
    
    def __init__(
        self, 
        name: str, 
        level: str = 'INFO',
        log_file: Optional[str] = None
    ):
        self.name = name
        self.level = level
        self.log_file = log_file
        self.previous_level = None
    
    def __enter__(self):
        """进入上下文"""
        self.previous_level = logging.getLogger().level
        setup_logging(self.level, self.log_file, include_console=True)
        return get_logger(self.name)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.previous_level is not None:
            logging.getLogger().setLevel(self.previous_level)
        return False


# 预配置的日志器
def get_default_logger() -> logging.Logger:
    """获取默认配置的logger"""
    if not logging.getLogger().handlers:
        setup_logging()
    return get_logger('video_fingerprint')

