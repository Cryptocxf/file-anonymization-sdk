"""
Excel文件脱敏器
基于pandas和openpyxl实现Excel文件敏感信息脱敏
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any
from faker import Faker
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

from .base_anonymizer import BaseAnonymizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities.engine import OperatorConfig

logger = logging.getLogger(__name__)


class ExcelAnonymizer(BaseAnonymizer):
    """Excel文件脱敏器"""
    
    SUPPORTED_EXTENSIONS = ['.xlsx', '.xls']
    SUPPORTED_METHODS = ['fake', 'mask', 'encrypt']
    
    def __init__(self, language: str = 'zh', verbose: bool = False, 
                 output_dir: str = "./anonymized-datas"):
        super().__init__(language, verbose, output_dir)
        
        # 初始化Faker
        if self.language == 'zh':
            self.faker = Faker(locale="zh_CN")
        else:
            self.faker = Faker(locale="en_US")
        
        # 初始化匿名化引擎
        self.anonymizer = AnonymizerEngine()
    
    def anonymize(self, input_path: str, output_path: Optional[str] = None, 
                 method: str = 'mask', encryption_key: Optional[str] = None, 
                 **kwargs) -> str:
        """
        Excel文件脱敏
        
        Args:
            input_path: 输入Excel路径
            output_path: 输出路径（可选）
            method: 脱敏方法（fake, mask, encrypt）
            encryption_key: 加密密钥（6位数字，仅encrypt方法需要）
        
        Returns:
            str: 输出文件路径
        
        Raises:
            FileValidationError: 文件验证失败
            MethodNotSupportedError: 方法不支持
            EncryptionKeyError: 加密密钥错误
            Exception: 处理错误
        """
        from ..exceptions import (
            FileValidationError, MethodNotSupportedError, EncryptionKeyError
        )
        
        # 验证文件
        is_valid, message = self.validate_file(input_path)
        if not is_valid:
            raise FileValidationError(message)
        
        # 验证方法
        is_valid, message = self.validate_method(method)
        if not is_valid:
            raise MethodNotSupportedError(message)
        
        # 验证加密密钥
        if method == 'encrypt':
            if not encryption_key:
                raise EncryptionKeyError("加密方法需要提供加密密钥")
            if not (len(encryption_key) == 6 and encryption_key.isdigit()):
                raise EncryptionKeyError("加密密钥必须是6位数字")
        
        # 生成输出路径
        if output_path is None:
            output_path = self.get_output_path(input_path, method)
        
        logger.info(f"开始Excel脱敏: {input_path} -> {output_path}")
        logger.info(f"脱敏方法: {method}")
        
        try:
            # 根据方法获取操作符配置
            operators = self._get_operators(method, encryption_key)
            
            # 执行脱敏
            total_redactions = self._anonymize_excel(
                input_path, output_path, operators
            )
            
            logger.info(f"Excel脱敏完成，共处理 {total_redactions} 处敏感信息")
            return output_path
            
        except Exception as e:
            logger.error(f"Excel脱敏失败: {e}")
            raise
    
    def _get_operators(self, method: str, encryption_key: Optional[str] = None) -> Dict[str, OperatorConfig]:
        """获取操作符配置"""
        if method == 'fake':
            return self._get_fake_operators()
        elif method == 'mask':
            return self._get_mask_operators()
        elif method == 'encrypt':
            if not encryption_key:
                raise ValueError("加密方法需要加密密钥")
            return self._get_encrypt_operators(encryption_key)
        else:
            raise ValueError(f"未知的脱敏方法: {method}")
    
    def _get_fake_operators(self) -> Dict[str, OperatorConfig]:
        """伪造数据操作符"""
        return {
            "PERSON": OperatorConfig("custom", {"lambda": lambda x: self.faker.name()}),
            "PHONE_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self.faker.phone_number()}),
            "LOCATION": OperatorConfig("custom", {"lambda": lambda x: f"{self.faker.province()}{self.faker.city()}"}),
            "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self.faker.safe_email()}),
            "DATE_TIME": OperatorConfig("custom", {"lambda": lambda x: self.faker.past_date().strftime('%Y-%m-%d')}),
            "CREDIT_CARD": OperatorConfig("custom", {"lambda": lambda x: self.faker.credit_card_number()}),
            "US_BANK_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self.faker.credit_card_number()}),
            "DEFAULT": OperatorConfig("replace", {"new_value": "***"}),
        }
    
    def _get_mask_operators(self) -> Dict[str, OperatorConfig]:
        """打码操作符"""
        return {
            "PERSON": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 1)}),
            "PHONE_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 3)}),
            "LOCATION": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 2)}),
            "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self._mask_email(x)}),
            "DATE_TIME": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 4)}),
            "CREDIT_CARD": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 4)}),
            "US_BANK_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 4)}),
            "DEFAULT": OperatorConfig("custom", {"lambda": lambda x: self._mask_text(x, 2)}),
        }
    
    def _get_encrypt_operators(self, key: str) -> Dict[str, OperatorConfig]:
        """加密操作符"""
        return {
            "PERSON": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "PHONE_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "LOCATION": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "DATE_TIME": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "CREDIT_CARD": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "US_BANK_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
            "DEFAULT": OperatorConfig("custom", {"lambda": lambda x: self._encrypt_text(x, key)}),
        }
    
    def _mask_text(self, text: str, keep_chars: int = 3) -> str:
        """打码处理"""
        if not text or len(text) <= keep_chars:
            return str(text) if text is not None else ""
        
        text_str = str(text)
        return text_str[:keep_chars] + '*' * (len(text_str) - keep_chars)
    
    def _mask_email(self, email: str) -> str:
        """邮箱打码处理"""
        if not email or '@' not in str(email):
            return self._mask_text(str(email), 2) if email is not None else ""
        
        email_str = str(email)
        local, domain = email_str.split('@', 1)
        masked_local = self._mask_text(local, 2)
        return f"{masked_local}@{domain}"
    
    def _encrypt_text(self, text: str, key: str) -> str:
        """加密文本"""
        if not text:
            return str(text) if text is not None else ""
        
        try:
            text_str = str(text)
            
            # 使用PBKDF2从密钥派生加密密钥
            salt = b'excel_anonymizer_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key_bytes = key.encode()
            derived_key = kdf.derive(key_bytes)
            
            # 使用AES ECB模式进行确定性加密
            cipher = Cipher(algorithms.AES(derived_key), modes.ECB(), backend=default_backend())
            encryptor = cipher.encryptor()
            
            # 对文本进行填充
            block_size = 16
            padded_text = text_str.encode()
            padding_length = block_size - (len(padded_text) % block_size)
            padded_text += bytes([padding_length] * padding_length)
            
            # 加密
            encrypted_data = encryptor.update(padded_text) + encryptor.finalize()
            
            return f"ENC:{base64.urlsafe_b64encode(encrypted_data).decode()}"
            
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return str(text) if text is not None else ""
    
    def _anonymize_excel(self, input_path: str, output_path: str, 
                        operators: Dict[str, OperatorConfig]) -> int:
        """执行Excel文件脱敏"""
        try:
            # 读取Excel文件
            df = pd.read_excel(input_path)
            
            logger.debug(f"读取Excel成功: {len(df)} 行, {len(df.columns)} 列")
            logger.debug(f"列名: {list(df.columns)}")
            
            total_redactions = 0
            processed_cells = 0
            
            # 遍历所有单元格
            for col in df.columns:
                for idx, value in df[col].items():
                    processed_cells += 1
                    
                    # 跳过空值
                    if pd.isna(value) or value == "":
                        continue
                    
                    try:
                        # 分析敏感信息
                        analyzer_results = self.analyzer.analyze(str(value))
                        
                        if analyzer_results:
                            # 使用匿名化器处理
                            anonymized_results = self.anonymizer.anonymize(
                                text=str(value),
                                analyzer_results=analyzer_results,
                                operators=operators,
                            )
                            
                            anonymized_value = anonymized_results.text
                            
                            if anonymized_value != str(value):
                                total_redactions += len(analyzer_results)
                                df.at[idx, col] = anonymized_value
                                
                    except Exception as e:
                        logger.warning(f"处理单元格({idx}, {col})失败: {e}")
                        # 保留原值
            
            # 保存处理后的Excel
            df.to_excel(output_path, index=False)
            
            logger.debug(f"处理完成: {processed_cells} 个单元格, {total_redactions} 处敏感信息")
            return total_redactions
            
        except Exception as e:
            logger.error(f"处理Excel失败: {e}")
            raise
    
    def get_sheet_names(self, input_path: str) -> list:
        """
        获取Excel工作表名称
        
        Args:
            input_path: Excel文件路径
        
        Returns:
            工作表名称列表
        """
        try:
            excel_file = pd.ExcelFile(input_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"获取工作表名称失败: {e}")
            return []
    
    def read_sheet(self, input_path: str, sheet_name: str = None) -> pd.DataFrame:
        """
        读取Excel工作表
        
        Args:
            input_path: Excel文件路径
            sheet_name: 工作表名称（可选）
        
        Returns:
            DataFrame
        """
        try:
            if sheet_name:
                df = pd.read_excel(input_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(input_path)
            return df
        except Exception as e:
            logger.error(f"读取工作表失败: {e}")
            return pd.DataFrame()
    
    def anonymize_specific_columns(self, input_path: str, output_path: str, 
                                  columns: list, method: str = 'mask', 
                                  encryption_key: Optional[str] = None) -> str:
        """
        脱敏特定列
        
        Args:
            input_path: 输入Excel路径
            output_path: 输出路径
            columns: 需要脱敏的列名列表
            method: 脱敏方法
            encryption_key: 加密密钥（仅encrypt方法需要）
        
        Returns:
            输出文件路径
        """
        try:
            df = pd.read_excel(input_path)
            
            # 验证列名
            valid_columns = [col for col in columns if col in df.columns]
            if not valid_columns:
                logger.warning("没有有效的列名，跳过脱敏")
                df.to_excel(output_path, index=False)
                return output_path
            
            # 获取操作符
            operators = self._get_operators(method, encryption_key)
            
            total_redactions = 0
            
            # 只处理指定列
            for col in valid_columns:
                logger.info(f"处理列: {col}")
                
                for idx, value in df[col].items():
                    if pd.isna(value) or value == "":
                        continue
                    
                    try:
                        analyzer_results = self.analyzer.analyze(str(value))
                        
                        if analyzer_results:
                            anonymized_results = self.anonymizer.anonymize(
                                text=str(value),
                                analyzer_results=analyzer_results,
                                operators=operators,
                            )
                            
                            anonymized_value = anonymized_results.text
                            
                            if anonymized_value != str(value):
                                total_redactions += len(analyzer_results)
                                df.at[idx, col] = anonymized_value
                                
                    except Exception as e:
                        logger.warning(f"处理单元格({idx}, {col})失败: {e}")
            
            df.to_excel(output_path, index=False)
            logger.info(f"列脱敏完成，共处理 {total_redactions} 处敏感信息")
            return output_path
            
        except Exception as e:
            logger.error(f"列脱敏失败: {e}")
            raise