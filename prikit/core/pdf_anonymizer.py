"""
PDF文件脱敏器
基于PyMuPDF实现PDF文件敏感信息脱敏
"""

import logging
from typing import Optional, Tuple
import pymupdf

from .base_anonymizer import BaseAnonymizer

logger = logging.getLogger(__name__)


class PDFAnonymizer(BaseAnonymizer):
    """PDF文件脱敏器"""
    
    SUPPORTED_EXTENSIONS = ['.pdf']
    SUPPORTED_METHODS = ['mask', 'color', 'char']
    
    def __init__(self, language: str = 'zh', verbose: bool = False, 
                 output_dir: str = "./anonymized-datas"):
        super().__init__(language, verbose, output_dir)
    
    def anonymize(self, input_path: str, output_path: Optional[str] = None, 
                 method: str = 'mask', color: str = 'white', 
                 char: Optional[str] = None, **kwargs) -> str:
        """
        PDF文件脱敏
        
        Args:
            input_path: 输入PDF路径
            output_path: 输出路径（可选）
            method: 脱敏方法（mask, color, char）
            color: 填充颜色（仅color方法有效）
            char: 替换字符（仅char方法有效）
        
        Returns:
            str: 输出文件路径
        
        Raises:
            FileValidationError: 文件验证失败
            MethodNotSupportedError: 方法不支持
            Exception: 处理错误
        """
        from ..exceptions import FileValidationError, MethodNotSupportedError
        
        # 验证文件
        is_valid, message = self.validate_file(input_path)
        if not is_valid:
            raise FileValidationError(message)
        
        # 验证方法
        is_valid, message = self.validate_method(method)
        if not is_valid:
            raise MethodNotSupportedError(message)
        
        # 生成输出路径
        if output_path is None:
            output_path = self.get_output_path(input_path, method, color, char)
        
        # 处理颜色参数
        color_map = {
            'white': (1, 1, 1),   # 白色
            'black': (0, 0, 0),   # 黑色
            'red': (1, 0, 0),     # 红色
            'blue': (0, 0, 1),    # 蓝色
            'green': (0, 1, 0),   # 绿色
            'gray': (0.5, 0.5, 0.5),  # 灰色
        }
        
        fill_color = color_map.get(color.lower(), (1, 1, 1))
        
        logger.info(f"开始PDF脱敏: {input_path} -> {output_path}")
        logger.info(f"脱敏方法: {method}, 颜色: {color}, 字符: {char}")
        
        try:
            # 根据方法选择处理方式
            if method == 'mask' or method == 'color':
                # mask方法实际上也是颜色填充（白色）
                self._anonymize_with_color(input_path, output_path, fill_color)
            elif method == 'char':
                self._anonymize_with_char(input_path, output_path, char or '*')
            else:
                raise MethodNotSupportedError(f"未知的脱敏方法: {method}")
            
            logger.info(f"PDF脱敏完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF脱敏失败: {e}")
            raise
    
    def _anonymize_with_color(self, input_path: str, output_path: str, 
                            color: Tuple[float, float, float]):
        """使用颜色填充脱敏"""
        try:
            doc = pymupdf.open(input_path)
            total_redactions = 0
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if not text.strip():
                    logger.debug(f"第 {page_num} 页为空页，跳过")
                    continue
                
                # 分析敏感信息
                results = self.analyzer.analyze(text)
                if not results:
                    logger.debug(f"第 {page_num} 页未发现敏感信息")
                    continue
                
                logger.info(f"在第 {page_num} 页发现 {len(results)} 处敏感信息")
                total_redactions += len(results)
                
                for res in results:
                    sensitive = text[res.start:res.end]
                    logger.debug(f"  敏感信息: '{sensitive}' (置信度: {res.score:.2f})")
                    
                    # 搜索文本位置
                    rects = page.search_for(sensitive)
                    if not rects:
                        logger.warning(f"    未找到文本 '{sensitive}' 的位置")
                        continue
                    
                    for rect in rects:
                        # 添加红色标记（仅用于调试）
                        if self.verbose:
                            page.add_redact_annot(rect, fill=(1, 0, 0), text="敏感信息")
                        else:
                            page.add_redact_annot(rect, fill=color)
                
                # 应用红色标记
                page.apply_redactions()
            
            doc.save(output_path, garbage=3, deflate=True)
            doc.close()
            
            logger.info(f"颜色填充脱敏完成，共处理 {total_redactions} 处敏感信息")
            
        except Exception as e:
            logger.error(f"颜色填充脱敏失败: {e}")
            raise
    
    def _anonymize_with_char(self, input_path: str, output_path: str, char: str):
        """使用字符替换脱敏"""
        try:
            doc = pymupdf.open(input_path)
            font_name = "helv"  # 默认字体
            total_redactions = 0
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if not text.strip():
                    logger.debug(f"第 {page_num} 页为空页，跳过")
                    continue
                
                # 分析敏感信息
                results = self.analyzer.analyze(text)
                if not results:
                    logger.debug(f"第 {page_num} 页未发现敏感信息")
                    continue
                
                logger.info(f"在第 {page_num} 页发现 {len(results)} 处敏感信息")
                total_redactions += len(results)
                
                for res in results:
                    sensitive = text[res.start:res.end]
                    logger.debug(f"  敏感信息: '{sensitive}' (置信度: {res.score:.2f})")
                    
                    # 搜索文本位置
                    rects = page.search_for(sensitive)
                    if not rects:
                        logger.warning(f"    未找到文本 '{sensitive}' 的位置")
                        continue
                    
                    for rect in rects:
                        # 白色背景
                        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                        
                        # 计算字符数量
                        text_len = max(len(sensitive), 1)
                        char_count = min(text_len, 20)  # 限制最大字符数
                        
                        # 计算字体大小
                        font_size = rect.width / (char_count * 0.6)
                        font_size = min(font_size, 20)  # 限制最大字体
                        
                        # 计算垂直居中位置
                        y_center = (rect.y0 + rect.y1) / 2 + font_size * 0.35
                        
                        # 绘制字符
                        page.insert_text(
                            pymupdf.Point(rect.x0, y_center),
                            char * char_count,
                            fontname=font_name,
                            fontsize=font_size,
                            color=(0, 0, 0)  # 黑色字符
                        )
            
            doc.save(output_path, garbage=3, deflate=True)
            doc.close()
            
            logger.info(f"字符替换脱敏完成，共处理 {total_redactions} 处敏感信息")
            
        except Exception as e:
            logger.error(f"字符替换脱敏失败: {e}")
            raise
    
    def extract_text(self, input_path: str) -> str:
        """
        提取PDF文本内容
        
        Args:
            input_path: PDF文件路径
        
        Returns:
            PDF文本内容
        """
        try:
            doc = pymupdf.open(input_path)
            text = ""
            
            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text()
                if page_text.strip():
                    text += f"\n--- 第 {page_num} 页 ---\n{page_text}\n"
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"提取PDF文本失败: {e}")
            return ""
    
    def get_page_count(self, input_path: str) -> int:
        """
        获取PDF页数
        
        Args:
            input_path: PDF文件路径
        
        Returns:
            页数
        """
        try:
            doc = pymupdf.open(input_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"获取PDF页数失败: {e}")
            return 0