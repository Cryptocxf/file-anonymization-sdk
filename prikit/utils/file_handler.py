"""
文件处理工具
提供文件路径生成、验证等功能
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """文件处理工具类"""
    
    # 支持的文件格式映射
    FILE_TYPE_EXTENSIONS = {
        'pdf': ['.pdf'],
        'word': ['.docx', '.doc'],
        'excel': ['.xlsx', '.xls'],
        'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'],
        'ppt': ['.pptx', '.ppt']
    }
    
    # 脱敏方法后缀映射
    METHOD_SUFFIXES = {
        'mask': 'mask',
        'color': 'color',
        'char': 'char',
        'fake': 'fake',
        'encrypt': 'encrypted'
    }
    
    def __init__(self, output_dir: str = "./anonymized-datas"):
        """
        初始化文件处理器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """确保目录存在"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"输出目录: {self.output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            raise
    
    def generate_output_path(self, input_path: str, method: str, 
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
        try:
            # 解析输入路径
            input_path_obj = Path(input_path)
            
            # 获取原始文件名（去除可能的task_id前缀）
            original_stem = self._extract_original_stem(input_path_obj.stem)
            original_ext = input_path_obj.suffix
            
            # 根据方法生成基础文件名
            base_filename = self._generate_base_filename(
                original_stem, original_ext, method, color, char
            )
            
            # 确保文件名唯一
            output_filename = self._ensure_unique_filename(base_filename)
            
            # 构建完整输出路径
            output_path = self.output_dir / output_filename
            
            logger.debug(f"生成输出路径: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"生成输出路径失败: {e}")
            # 如果失败，返回默认路径
            default_name = f"anonymous_{uuid.uuid4().hex[:8]}{Path(input_path).suffix}"
            return str(self.output_dir / default_name)
    
    def _extract_original_stem(self, stem: str) -> str:
        """
        提取原始文件名（去除task_id前缀）
        
        Args:
            stem: 文件名（不含扩展名）
        
        Returns:
            原始文件名
        """
        # 如果包含下划线，尝试分割
        if '_' in stem:
            parts = stem.split('_', 1)  # 只分割第一个下划线
            if len(parts) > 1:
                # 检查第一部分是否是UUID格式
                first_part = parts[0]
                if self._is_uuid(first_part):
                    return parts[1]  # 返回第二部分
                else:
                    # 如果不是UUID，可能是其他前缀，返回整个文件名
                    return stem
        return stem
    
    def _is_uuid(self, text: str) -> bool:
        """检查字符串是否是UUID格式"""
        try:
            uuid.UUID(text)
            return True
        except ValueError:
            return False
    
    def _generate_base_filename(self, stem: str, ext: str, method: str,
                              color: Optional[str], char: Optional[str]) -> str:
        """
        生成基础文件名
        
        Args:
            stem: 文件名（不含扩展名）
            ext: 文件扩展名
            method: 脱敏方法
            color: 颜色
            char: 字符
        
        Returns:
            基础文件名
        """
        # 获取方法后缀
        method_suffix = self.METHOD_SUFFIXES.get(method, method)
        
        # 根据方法构建文件名
        if method == 'color' and color:
            # 颜色方法：filename_anonymous_color_颜色.扩展名
            return f"{stem}_anonymous_color_{color}{ext}"
        elif method == 'char':
            # 字符方法：filename_anonymous_char.扩展名
            # 如果需要，可以添加字符信息
            if char and char != '*':
                return f"{stem}_anonymous_char_{char}{ext}"
            else:
                return f"{stem}_anonymous_char{ext}"
        elif method in ['mask', 'fake', 'encrypt']:
            # 其他方法：filename_anonymous_方法.扩展名
            return f"{stem}_anonymous_{method_suffix}{ext}"
        else:
            # 默认
            return f"{stem}_anonymous_{method_suffix}{ext}"
    
    def _ensure_unique_filename(self, base_filename: str) -> str:
        """
        确保文件名唯一
        
        Args:
            base_filename: 基础文件名
        
        Returns:
            唯一文件名
        """
        # 检查文件是否已存在
        output_path = self.output_dir / base_filename
        
        if not output_path.exists():
            return base_filename
        
        # 如果已存在，添加序号
        name_without_ext = Path(base_filename).stem
        ext = Path(base_filename).suffix
        
        counter = 1
        while True:
            new_filename = f"{name_without_ext} ({counter}){ext}"
            new_path = self.output_dir / new_filename
            
            if not new_path.exists():
                return new_filename
            
            counter += 1
    
    def validate_file(self, file_path: str, expected_type: str = None) -> Tuple[bool, str]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            expected_type: 期望的文件类型（可选）
        
        Returns:
            Tuple[是否有效, 消息]
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}"
            
            # 检查文件是否可读
            if not os.access(file_path, os.R_OK):
                return False, f"文件不可读: {file_path}"
            
            # 检查文件大小
            try:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    return False, f"文件为空: {file_path}"
            except:
                pass
            
            # 检查文件类型
            if expected_type:
                ext = Path(file_path).suffix.lower()
                supported_exts = self.FILE_TYPE_EXTENSIONS.get(expected_type, [])
                
                if ext not in supported_exts:
                    return False, (
                        f"不支持的文件格式: {ext}, "
                        f"期望格式: {', '.join(supported_exts)}"
                    )
            
            return True, "验证通过"
            
        except Exception as e:
            return False, f"文件验证失败: {e}"
    
    def get_file_info(self, file_path: str) -> dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件信息字典
        """
        try:
            path = Path(file_path)
            stat = os.stat(file_path)
            
            info = {
                'filename': path.name,
                'extension': path.suffix.lower(),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'accessed_time': stat.st_atime,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'exists': path.exists(),
                'readable': os.access(file_path, os.R_OK),
                'writable': os.access(file_path, os.W_OK),
                'executable': os.access(file_path, os.X_OK),
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {}
    
    def cleanup_old_files(self, max_age_hours: int = 24, 
                         pattern: str = "*.pdf"):
        """
        清理旧文件
        
        Args:
            max_age_hours: 最大年龄（小时）
            pattern: 文件模式
        """
        import time
        import fnmatch
        
        try:
            current_time = time.time()
            deleted_count = 0
            
            for file_path in self.output_dir.glob(pattern):
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > (max_age_hours * 3600):
                        os.remove(file_path)
                        deleted_count += 1
                        logger.debug(f"删除旧文件: {file_path.name}")
                        
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个旧文件")
                
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
    
    def list_output_files(self, pattern: str = "*") -> List[str]:
        """
        列出输出目录中的文件
        
        Args:
            pattern: 文件模式
        
        Returns:
            文件路径列表
        """
        try:
            files = []
            for file_path in self.output_dir.glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))
            return files
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    def create_temp_file(self, content: bytes = None, 
                        extension: str = ".tmp") -> str:
        """
        创建临时文件
        
        Args:
            content: 文件内容（可选）
            extension: 文件扩展名
        
        Returns:
            临时文件路径
        """
        try:
            temp_dir = self.output_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            temp_filename = f"temp_{uuid.uuid4().hex}{extension}"
            temp_path = temp_dir / temp_filename
            
            if content:
                with open(temp_path, 'wb') as f:
                    f.write(content)
            
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"创建临时文件失败: {e}")
            raise
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dir = self.output_dir / "temp"
            if temp_dir.exists():
                for file_path in temp_dir.glob("*"):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                
                # 删除空目录
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")