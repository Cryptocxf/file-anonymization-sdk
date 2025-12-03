"""
基础脱敏器抽象类
所有具体脱敏器的基类
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from ..utils.chinese_recognizer import ChineseAnalyzer
from ..utils.file_handler import FileHandler

logger = logging.getLogger(__name__)


class BaseAnonymizer(ABC):
    """基础脱敏器抽象类"""
    
    # 子类需要覆盖这些属性
    SUPPORTED_EXTENSIONS: List[str] = []
    SUPPORTED_METHODS: List[str] = []
    
    def __init__(self, language: str = 'zh', verbose: bool = False, 
                 output_dir: str = "./anonymized-datas"):
        """
        初始化脱敏器
        
        Args:
            language: 语言（zh/en）
            verbose: 详细输出模式
            output_dir: 输出目录
        """
        self.language = language
        self.verbose = verbose
        self.output_dir = output_dir
        
        # 初始化组件
        self.analyzer = ChineseAnalyzer(language=language, verbose=verbose)
        self.file_handler = FileHandler(output_dir)
        
        # 配置日志
        self._setup_logging()
        
        logger.debug(f"初始化 {self.__class__.__name__}, 语言: {language}, 输出目录: {output_dir}")
    
    def _setup_logging(self):
        """配置日志"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        if not logger.handlers:
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                ]
            )
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            Tuple[是否有效, 消息]
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        # 检查文件格式
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            return False, (
                f"不支持的文件格式: {file_ext}, "
                f"支持格式: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
        
        # 检查文件是否可读
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # 尝试读取一个字节
        except IOError as e:
            return False, f"文件无法读取: {e}"
        
        return True, "验证通过"
    
    def validate_method(self, method: str) -> Tuple[bool, str]:
        """
        验证脱敏方法
        
        Args:
            method: 脱敏方法
        
        Returns:
            Tuple[是否有效, 消息]
        """
        if method not in self.SUPPORTED_METHODS:
            return False, (
                f"不支持的脱敏方法: {method}, "
                f"支持方法: {', '.join(self.SUPPORTED_METHODS)}"
            )
        return True, "验证通过"
    
    def get_output_path(self, input_path: str, method: str, 
                       color: Optional[str] = None, 
                       char: Optional[str] = None) -> str:
        """
        生成输出文件路径
        
        Args:
            input_path: 输入文件路径
            method: 脱敏方法
            color: 颜色（可选）
            char: 字符（可选）
        
        Returns:
            输出文件路径
        """
        return self.file_handler.generate_output_path(
            input_path=input_path,
            method=method,
            color=color,
            char=char
        )
    
    @abstractmethod
    def anonymize(self, input_path: str, output_path: Optional[str] = None, 
                 method: str = 'mask', **kwargs) -> str:
        """
        执行脱敏操作
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（可选，自动生成）
            method: 脱敏方法
            **kwargs: 其他参数
        
        Returns:
            str: 输出文件路径
        
        Raises:
            FileValidationError: 文件验证失败
            MethodNotSupportedError: 方法不支持
            Exception: 其他处理错误
        """
        pass
    
    def anonymize_batch(self, input_paths: List[str], method: str = 'mask', 
                       **kwargs) -> Dict[str, str]:
        """
        批量脱敏
        
        Args:
            input_paths: 输入文件路径列表
            method: 脱敏方法
            **kwargs: 其他参数
        
        Returns:
            Dict[str, str]: {输入文件路径: 输出文件路径} 的映射
        
        Raises:
            ValueError: 输入参数错误
        """
        if not isinstance(input_paths, list):
            raise ValueError("input_paths 必须是列表")
        
        if not input_paths:
            raise ValueError("input_paths 不能为空")
        
        results = {}
        total = len(input_paths)
        
        logger.info(f"开始批量处理 {total} 个文件")
        
        for i, input_path in enumerate(input_paths, 1):
            try:
                logger.info(f"处理文件 {i}/{total}: {Path(input_path).name}")
                
                # 验证文件
                is_valid, message = self.validate_file(input_path)
                if not is_valid:
                    logger.warning(f"文件验证失败: {input_path} - {message}")
                    results[input_path] = None
                    continue
                
                # 执行脱敏
                output_path = self.anonymize(
                    input_path=input_path,
                    method=method,
                    **kwargs
                )
                
                results[input_path] = output_path
                logger.info(f"文件脱敏成功: {input_path} -> {output_path}")
                
            except Exception as e:
                logger.error(f"文件脱敏失败: {input_path}, 错误: {e}")
                results[input_path] = None
        
        # 统计结果
        successful = sum(1 for r in results.values() if r is not None)
        failed = total - successful
        
        logger.info(f"批量处理完成: 成功 {successful}, 失败 {failed}")
        
        return results
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件信息字典
        """
        path = Path(file_path)
        
        try:
            size = os.path.getsize(file_path)
        except:
            size = 0
        
        return {
            'filename': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': size,
            'size_mb': round(size / (1024 * 1024), 2) if size > 0 else 0,
            'exists': os.path.exists(file_path),
            'readable': os.access(file_path, os.R_OK),
        }
    
    def cleanup(self):
        """清理资源"""
        # 子类可以重写此方法以清理特定资源
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
    
    def __repr__(self):
        return f"{self.__class__.__name__}(language={self.language}, verbose={self.verbose})"