"""
异常模块
定义SDK中的所有异常类
"""


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


class OCRNotAvailableError(AnonymizationError):
    """OCR不可用异常"""
    pass


class FormatPreservationError(AnonymizationError):
    """格式保留异常"""
    pass


class ResourceNotFoundError(AnonymizationError):
    """资源未找到异常"""
    pass


class ConfigurationError(AnonymizationError):
    """配置错误异常"""
    pass


class ProcessingTimeoutError(AnonymizationError):
    """处理超时异常"""
    pass


class BatchProcessingError(AnonymizationError):
    """批量处理异常"""
    def __init__(self, message, failed_files=None):
        super().__init__(message)
        self.failed_files = failed_files or []