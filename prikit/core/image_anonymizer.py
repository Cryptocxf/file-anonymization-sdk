"""
图片文件脱敏器
基于PIL和Tesseract OCR实现图片敏感信息脱敏
"""

import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw
import pytesseract

from .base_anonymizer import BaseAnonymizer

logger = logging.getLogger(__name__)


class ImageAnonymizer(BaseAnonymizer):
    """图片文件脱敏器"""
    
    SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    SUPPORTED_METHODS = ['mask', 'color', 'char']
    
    def __init__(self, language: str = 'zh', verbose: bool = False, 
                 output_dir: str = "./anonymized-datas"):
        super().__init__(language, verbose, output_dir)
        
        # 配置Tesseract语言
        self.tesseract_lang = 'chi_sim+eng' if language == 'zh' else 'eng'
    
    def anonymize(self, input_path: str, output_path: Optional[str] = None, 
                 method: str = 'mask', color: str = 'white', 
                 char: Optional[str] = None, ocr_engine: str = 'tesseract',
                 **kwargs) -> str:
        """
        图片文件脱敏
        
        Args:
            input_path: 输入图片路径
            output_path: 输出路径（可选）
            method: 脱敏方法（mask, color, char）
            color: 填充颜色（仅color方法有效）
            char: 替换字符（仅char方法有效）
            ocr_engine: OCR引擎（目前只支持tesseract）
        
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
        
        logger.info(f"开始图片脱敏: {input_path} -> {output_path}")
        logger.info(f"脱敏方法: {method}, 颜色: {color}, 字符: {char}")
        
        try:
            # 根据方法选择处理方式
            if method == 'mask' or method == 'color':
                # 颜色填充脱敏
                fill_color = self._parse_color(color)
                redaction_count = self._anonymize_with_boxes(
                    input_path, output_path, fill_color=fill_color
                )
            elif method == 'char':
                # 字符替换脱敏
                fill_color = self._parse_color('black')  # 字符颜色
                redaction_count = self._anonymize_with_char(
                    input_path, output_path, char or '*', fill_color
                )
            else:
                raise MethodNotSupportedError(f"未知的脱敏方法: {method}")
            
            logger.info(f"图片脱敏完成，共掩盖 {redaction_count} 处敏感信息")
            return output_path
            
        except Exception as e:
            logger.error(f"图片脱敏失败: {e}")
            raise
    
    def _parse_color(self, color_str: str) -> str:
        """解析颜色字符串"""
        color_map = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'blue': (0, 0, 255),
            'green': (0, 255, 0),
            'gray': (128, 128, 128),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
        }
        return color_map.get(color_str.lower(), (255, 255, 255))  # 默认白色
    
    def _anonymize_with_boxes(self, input_path: str, output_path: str, 
                             fill_color: Tuple[int, int, int]) -> int:
        """使用颜色框脱敏"""
        try:
            # 打开图片
            image = Image.open(input_path)
            logger.debug(f"图片尺寸: {image.size}, 模式: {image.mode}")
            
            # 转换为RGB模式（确保颜色正确）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 使用OCR提取文本
            all_text = pytesseract.image_to_string(image, lang=self.tesseract_lang).strip()
            if not all_text:
                logger.info("OCR未识别到任何文字")
                image.save(output_path)
                return 0
            
            # 分析敏感信息
            analyzer_results = self.analyzer.analyze(all_text)
            if not analyzer_results:
                logger.info("未发现敏感信息")
                image.save(output_path)
                return 0
            
            logger.info(f"发现 {len(analyzer_results)} 处敏感信息")
            
            # 获取敏感词集合
            sensitive_words = {all_text[res.start:res.end] for res in analyzer_results}
            logger.debug(f"敏感词: {sensitive_words}")
            
            # 获取详细的OCR数据
            ocr_data = pytesseract.image_to_data(
                image, 
                lang=self.tesseract_lang, 
                output_type=pytesseract.Output.DICT
            )
            
            # 复制图像并绘制
            redacted_image = image.copy()
            draw = ImageDraw.Draw(redacted_image)
            redaction_count = 0
            
            # 遍历OCR识别的所有单词
            for i in range(len(ocr_data['text'])):
                word = ocr_data['text'][i].strip()
                if not word:
                    continue
                
                confidence = int(ocr_data['conf'][i])
                
                # 检查是否是敏感词
                is_sensitive = False
                for sensitive_word in sensitive_words:
                    if (word in sensitive_word or 
                        sensitive_word in word or 
                        any(word in sw for sw in sensitive_words) or
                        any(sw in word for sw in sensitive_words)):
                        is_sensitive = True
                        break
                
                if is_sensitive and confidence > 25:  # 置信度阈值
                    # 获取单词位置
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # 绘制矩形框
                    draw.rectangle((x, y, x + w, y + h), fill=fill_color)
                    redaction_count += 1
                    
                    if self.verbose:
                        logger.debug(f"掩盖单词: '{word}' 位置: ({x}, {y}, {w}, {h})")
            
            # 保存处理后的图片
            redacted_image.save(output_path)
            logger.debug(f"实际掩盖了 {redaction_count} 处敏感信息")
            return redaction_count
            
        except pytesseract.TesseractNotFoundError as e:
            logger.error("Tesseract OCR未安装或未配置")
            logger.error("安装指南:")
            logger.error("  Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim")
            logger.error("  macOS: brew install tesseract")
            logger.error("  Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载")
            raise
        except Exception as e:
            logger.error(f"颜色框脱敏失败: {e}")
            raise
    
    def _anonymize_with_char(self, input_path: str, output_path: str, 
                           char: str, text_color: Tuple[int, int, int]) -> int:
        """使用字符替换脱敏"""
        try:
            # 打开图片
            image = Image.open(input_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 使用OCR提取文本
            all_text = pytesseract.image_to_string(image, lang=self.tesseract_lang).strip()
            if not all_text:
                logger.info("OCR未识别到任何文字")
                image.save(output_path)
                return 0
            
            # 分析敏感信息
            analyzer_results = self.analyzer.analyze(all_text)
            if not analyzer_results:
                logger.info("未发现敏感信息")
                image.save(output_path)
                return 0
            
            logger.info(f"发现 {len(analyzer_results)} 处敏感信息")
            
            # 获取敏感词集合
            sensitive_words = {all_text[res.start:res.end] for res in analyzer_results}
            
            # 获取详细的OCR数据
            ocr_data = pytesseract.image_to_data(
                image, 
                lang=self.tesseract_lang, 
                output_type=pytesseract.Output.DICT
            )
            
            # 复制图像并绘制
            redacted_image = image.copy()
            draw = ImageDraw.Draw(redacted_image)
            redaction_count = 0
            
            # 遍历OCR识别的所有单词
            for i in range(len(ocr_data['text'])):
                word = ocr_data['text'][i].strip()
                if not word:
                    continue
                
                confidence = int(ocr_data['conf'][i])
                
                # 检查是否是敏感词
                is_sensitive = False
                for sensitive_word in sensitive_words:
                    if (word in sensitive_word or 
                        sensitive_word in word or 
                        any(word in sw for sw in sensitive_words) or
                        any(sw in word for sw in sensitive_words)):
                        is_sensitive = True
                        break
                
                if is_sensitive and confidence > 25:
                    # 获取单词位置
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # 白色背景
                    draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255))
                    
                    # 计算字符大小
                    char_count = min(max(1, w // 15), 20)  # 根据宽度计算字符数
                    font_size = max(8, min(h - 4, 24))  # 限制字体大小
                    
                    # 尝试绘制字符
                    try:
                        # 计算字符位置（居中）
                        from PIL import ImageFont
                        try:
                            font = ImageFont.truetype("arial.ttf", font_size)
                        except:
                            font = ImageFont.load_default()
                        
                        # 计算文本尺寸
                        text = char * char_count
                        
                        # 绘制文本
                        draw.text((x, y), text, fill=text_color, font=font)
                        
                    except Exception as font_error:
                        logger.warning(f"字体绘制失败，使用简单矩形: {font_error}")
                        # 如果字体失败，使用矩形块
                        draw.rectangle((x, y, x + w, y + h), fill=text_color)
                    
                    redaction_count += 1
            
            # 保存处理后的图片
            redacted_image.save(output_path)
            logger.debug(f"字符替换脱敏完成，掩盖了 {redaction_count} 处敏感信息")
            return redaction_count
            
        except Exception as e:
            logger.error(f"字符替换脱敏失败: {e}")
            raise
    
    def extract_text(self, input_path: str) -> str:
        """
        提取图片中的文本
        
        Args:
            input_path: 图片文件路径
        
        Returns:
            图片中的文本内容
        """
        try:
            image = Image.open(input_path)
            text = pytesseract.image_to_string(image, lang=self.tesseract_lang)
            return text.strip()
        except Exception as e:
            logger.error(f"提取图片文本失败: {e}")
            return ""
    
    def get_image_info(self, input_path: str) -> dict:
        """
        获取图片信息
        
        Args:
            input_path: 图片文件路径
        
        Returns:
            图片信息字典
        """
        try:
            with Image.open(input_path) as img:
                info = {
                    'format': img.format,
                    'size': img.size,  # (width, height)
                    'mode': img.mode,
                    'width': img.width,
                    'height': img.height,
                }
                return info
        except Exception as e:
            logger.error(f"获取图片信息失败: {e}")
            return {}