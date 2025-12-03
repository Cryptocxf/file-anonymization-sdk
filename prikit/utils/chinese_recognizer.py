"""
中文敏感信息识别器
基于Presidio的中文敏感信息识别
"""

import logging
from typing import List, Optional
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

logger = logging.getLogger(__name__)


class ChineseAnalyzer:
    """中文敏感信息分析器"""
    
    def __init__(self, language: str = 'zh', verbose: bool = False):
        """
        初始化分析器
        
        Args:
            language: 语言（zh/en）
            verbose: 详细输出模式
        """
        self.language = language
        self.verbose = verbose
        self.analyzer = self._setup_chinese_analyzer()
        self._setup_chinese_recognizers()
        
        if verbose:
            logger.info(f"中文分析器初始化完成，语言: {language}")
    
    def _setup_chinese_analyzer(self) -> AnalyzerEngine:
        """
        设置支持中文的分析器
        
        Returns:
            AnalyzerEngine实例
        """
        try:
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "zh", "model_name": "zh_core_web_trf"}],
            }
            
            provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = provider.create_engine()
            
            analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=["zh", "en"]
            )
            
            return analyzer
            
        except Exception as e:
            logger.warning(f"中文分析器设置失败，使用默认分析器: {e}")
            
            # 回退到默认分析器
            return AnalyzerEngine()
    
    def _setup_chinese_recognizers(self):
        """添加中文特定的识别模式"""
        try:
            # 中文手机号识别
            chinese_phone_pattern = Pattern(
                "Chinese Phone", 
                r"\b1[3-9]\d{9}\b",  # 中国手机号模式
                0.8
            )
            chinese_phone_recognizer = PatternRecognizer(
                supported_entity="PHONE_NUMBER",
                patterns=[chinese_phone_pattern],
                supported_language="zh"
            )
            
            # 中文身份证号识别
            chinese_id_pattern = Pattern(
                "Chinese ID", 
                r"\b[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
                0.9
            )
            chinese_id_recognizer = PatternRecognizer(
                supported_entity="CREDIT_CARD",  # 使用CREDIT_CARD作为身份证的替代
                patterns=[chinese_id_pattern],
                supported_language="zh"
            )
            
            # 中文姓名识别（简单模式）
            #chinese_name_pattern = Pattern(
            #    "Chinese Name",
            #    r"[\u4e00-\u9fa5]{2,4}",  # 2-4个中文字符
            #    0.6
            #)
            #chinese_name_recognizer = PatternRecognizer(
            #    supported_entity="PERSON",
            #    patterns=[chinese_name_pattern],
            #    supported_language="zh"
            #)
            
            # 中文地址识别
            #chinese_address_pattern = Pattern(
            #    "Chinese Address",
            #    r"[\u4e00-\u9fa5]{2,10}(省|市|区|县|街道|路|号)",
            #    0.7
            #)
            #chinese_address_recognizer = PatternRecognizer(
            #    supported_entity="LOCATION",
            #    patterns=[chinese_address_pattern],
            #    supported_language="zh"
            #)
            
            # 中文邮箱识别
            #chinese_email_pattern = Pattern(
            #    "Chinese Email",
            #    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            #    0.8
            #)
            #chinese_email_recognizer = PatternRecognizer(
            #    supported_entity="EMAIL_ADDRESS",
            #    patterns=[chinese_email_pattern],
            #    supported_language="zh"
            #)
            
            # 中文银行卡号识别（简单模式）
            #chinese_bank_pattern = Pattern(
            #    "Chinese Bank Card",
            #    r"\b\d{16,19}\b",
            #    0.7
            #)
            #chinese_bank_recognizer = PatternRecognizer(
            #    supported_entity="US_BANK_NUMBER",
            #    patterns=[chinese_bank_pattern],
            #    supported_language="zh"
            #)
            
            # 添加到分析器
            self.analyzer.registry.add_recognizer(chinese_phone_recognizer)
            self.analyzer.registry.add_recognizer(chinese_id_recognizer)
            #self.analyzer.registry.add_recognizer(chinese_name_recognizer)
            #self.analyzer.registry.add_recognizer(chinese_address_recognizer)
            #self.analyzer.registry.add_recognizer(chinese_email_recognizer)
            #self.analyzer.registry.add_recognizer(chinese_bank_recognizer)
            
            if self.verbose:
                logger.info("中文识别器设置完成")
                
        except Exception as e:
            logger.error(f"设置中文识别器失败: {e}")
    
    def analyze(self, text: str, language: Optional[str] = None) -> List:
        """
        分析文本中的敏感信息
        
        Args:
            text: 要分析的文本
            language: 语言（默认使用初始化时设置的语言）
        
        Returns:
            敏感信息识别结果列表
        """
        if not text or not text.strip():
            return []
        
        try:
            analysis_language = language or self.language
            
            results = self.analyzer.analyze(
                text=text,
                language=analysis_language,
                entities=None,  # 分析所有实体
                score_threshold=0.4  # 置信度阈值
            )
            
            if self.verbose and results:
                logger.debug(f"分析文本发现 {len(results)} 处敏感信息")
                for res in results:
                    logger.debug(f"  实体: {res.entity_type}, 文本: '{text[res.start:res.end]}', 置信度: {res.score:.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"分析文本失败: {e}")
            return []
    
    def add_custom_recognizer(self, entity_type: str, pattern: str, 
                            score: float = 0.8, language: str = "zh"):
        """
        添加自定义识别器
        
        Args:
            entity_type: 实体类型
            pattern: 正则表达式模式
            score: 置信度分数
            language: 语言
        """
        try:
            custom_pattern = Pattern(f"Custom {entity_type}", pattern, score)
            custom_recognizer = PatternRecognizer(
                supported_entity=entity_type,
                patterns=[custom_pattern],
                supported_language=language
            )
            
            self.analyzer.registry.add_recognizer(custom_recognizer)
            
            if self.verbose:
                logger.info(f"添加自定义识别器: {entity_type}")
                
        except Exception as e:
            logger.error(f"添加自定义识别器失败: {e}")
    
    def remove_recognizer(self, entity_type: str, language: str = "zh"):
        """
        移除识别器
        
        Args:
            entity_type: 实体类型
            language: 语言
        """
        try:
            self.analyzer.registry.remove_recognizer(entity_type, language)
            
            if self.verbose:
                logger.info(f"移除识别器: {entity_type} ({language})")
                
        except Exception as e:
            logger.error(f"移除识别器失败: {e}")
    
    def get_supported_entities(self, language: str = None) -> List[str]:
        """
        获取支持的实体类型
        
        Args:
            language: 语言
        
        Returns:
            实体类型列表
        """
        try:
            analysis_language = language or self.language
            entities = self.analyzer.get_supported_entities(language=analysis_language)
            return entities
        except Exception as e:
            logger.error(f"获取支持的实体失败: {e}")
            return []
    
    def test_pattern(self, text: str, pattern: str) -> bool:
        """
        测试正则表达式模式
        
        Args:
            text: 测试文本
            pattern: 正则表达式模式
        
        Returns:
            是否匹配
        """
        import re
        try:
            match = re.search(pattern, text)
            return match is not None
        except Exception as e:
            logger.error(f"测试正则表达式失败: {e}")
            return False