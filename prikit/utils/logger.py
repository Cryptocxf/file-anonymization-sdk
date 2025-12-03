"""
日志配置工具
"""

import logging
import sys
from typing import Optional
from pathlib import Path

# 默认日志格式
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 颜色配置（用于控制台输出）
COLORS = {
    'DEBUG': '\033[94m',     # 蓝色
    'INFO': '\033[92m',      # 绿色
    'WARNING': '\033[93m',   # 黄色
    'ERROR': '\033[91m',     # 红色
    'CRITICAL': '\033[91m',  # 红色
    'RESET': '\033[0m'       # 重置
}


class ColorFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    def format(self, record):
        # 获取原始格式
        message = super().format(record)
        
        # 添加颜色
        if record.levelname in COLORS:
            color = COLORS[record.levelname]
            reset = COLORS['RESET']
            message = f"{color}{message}{reset}"
        
        return message


def setup_logger(name: str = None, level: str = "INFO", 
                log_file: Optional[str] = None, 
                console: bool = True, 
                color: bool = True) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        log_file: 日志文件路径（可选）
        console: 是否输出到控制台
        color: 是否使用颜色（仅控制台有效）
    
    Returns:
        配置好的日志记录器
    """
    # 获取或创建日志记录器
    logger = logging.getLogger(name or __name__)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if color:
            # 使用颜色格式化器
            color_formatter = ColorFormatter(
                fmt=DEFAULT_LOG_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT
            )
            console_handler.setFormatter(color_formatter)
        else:
            console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        try:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.error(f"创建文件日志处理器失败: {e}")
    
    # 防止日志传播到根记录器
    logger.propagate = False
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器
    """
    return logging.getLogger(name or __name__)


def log_execution_time(func):
    """
    记录函数执行时间的装饰器
    
    Usage:
        @log_execution_time
        def my_function():
            pass
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        start_time = time.time()
        logger.debug(f"开始执行: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"执行完成: {func.__name__}, 耗时: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行失败: {func.__name__}, 耗时: {execution_time:.3f}秒, 错误: {e}")
            raise
    
    return wrapper


class LoggerMixin:
    """日志混合类，可以添加到任何类中"""
    
    @property
    def logger(self):
        """获取类特定的日志记录器"""
        if not hasattr(self, '_logger'):
            class_name = self.__class__.__name__
            self._logger = get_logger(class_name)
        return self._logger


# 预配置的日志记录器
def get_package_logger():
    """获取包级别的日志记录器"""
    return get_logger("prikit")


def get_core_logger():
    """获取核心模块的日志记录器"""
    return get_logger("prikit.core")


def get_api_logger():
    """获取API模块的日志记录器"""
    return get_logger("prikit.api")


def get_utils_logger():
    """获取工具模块的日志记录器"""
    return get_logger("prikit.utils")


# 初始化默认日志记录器
def init_default_logging(level: str = "INFO"):
    """初始化默认日志记录"""
    return setup_logger("prikit", level=level)