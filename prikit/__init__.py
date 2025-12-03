"""
PriKit SDK
======================

基于Presidio的多格式文件脱敏工具包，支持PDF、Word、Excel、图片、PPT文件的敏感信息脱敏处理。

版本: 1.0.0
作者: Cryptocxf
许可证: MIT
"""

__version__ = "1.0.0"
__author__ = "Cryptocxf"
__email__ = "cryptocxf@163.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Cryptocxf"

# 核心模块
from .core.pdf_anonymizer import PDFAnonymizer
from .core.word_anonymizer import WordAnonymizer
from .core.excel_anonymizer import ExcelAnonymizer
from .core.image_anonymizer import ImageAnonymizer
from .core.ppt_anonymizer import PPTAnonymizer

# API模块
from .api.api_server import run_api_server

# 工具模块
from .utils.chinese_recognizer import ChineseAnalyzer
from .utils.file_handler import FileHandler
from .utils.logger import setup_logger

# 命令行接口
from .cli import main as cli_main

# 异常类
class AnonymizationError(Exception):
    """脱敏异常基类"""
    pass

class FileValidationError(AnonymizationError):
    """文件验证异常"""
    pass

class MethodNotSupportedError(AnonymizationError):
    """方法不支持异常"""
    pass

class EncryptionKeyError(AnonymizationError):
    """加密密钥异常"""
    pass

# 导出所有公共类
__all__ = [
    # 核心类
    'PDFAnonymizer',
    'WordAnonymizer', 
    'ExcelAnonymizer',
    'ImageAnonymizer',
    'PPTAnonymizer',
    
    # API
    'run_api_server',
    
    # 工具类
    'ChineseAnalyzer',
    'FileHandler',
    'setup_logger',
    
    # 命令行
    'cli_main',
    
    # 异常类
    'AnonymizationError',
    'FileValidationError',
    'MethodNotSupportedError',
    'EncryptionKeyError',
    
    # 元数据
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    '__copyright__',
]

# 包初始化
def init_sdk(log_level="INFO", log_file=None):
    """
    初始化SDK
    
    Args:
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        log_file: 日志文件路径（可选）
    
    Returns:
        logger: 配置好的日志记录器
    """
    return setup_logger(level=log_level, log_file=log_file)

# 便捷函数
def get_version():
    """获取SDK版本"""
    return __version__

def get_supported_formats():
    """获取支持的文件格式"""
    return {
        'pdf': ['.pdf'],
        'word': ['.docx', '.doc'],
        'excel': ['.xlsx', '.xls'],
        'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
        'ppt': ['.pptx', '.ppt']
    }

def get_supported_methods():
    """获取支持的脱敏方法"""
    return {
        'pdf': ['mask', 'color', 'char'],
        'word': ['fake', 'mask', 'encrypt'],
        'excel': ['fake', 'mask', 'encrypt'],
        'image': ['mask', 'color', 'char'],
        'ppt': ['mask']
    }