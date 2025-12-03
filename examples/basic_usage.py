#!/usr/bin/env python3
"""
基础使用示例
展示如何使用PriKit SDK进行各种文件脱敏
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入SDK
sys.path.append(str(Path(__file__).parent.parent))

from prikit import (
    PDFAnonymizer,
    WordAnonymizer,
    ExcelAnonymizer,
    ImageAnonymizer,
    PPTAnonymizer
)


def setup_test_files():
    """创建测试文件目录"""
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)
    return test_dir


def demo_pdf_anonymization():
    """PDF文件脱敏示例"""
    print("=" * 60)
    print("PDF文件脱敏示例")
    print("=" * 60)
    
    # 创建PDF脱敏器
    pdf_anonymizer = PDFAnonymizer(
        language='zh',
        verbose=True,
        output_dir="./anonymized/pdf"
    )
    
    # 示例1：颜色填充脱敏
    print("\n1. 颜色填充脱敏（白色）:")
    try:
        result = pdf_anonymizer.anonymize(
            "test_files/sample.pdf",  # 请替换为实际文件路径
            method="color",
            color="white"
        )
        print(f"   ✓ 脱敏完成: {result}")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")
    
    # 示例2：字符替换脱敏
    print("\n2. 字符替换脱敏（*号替换）:")
    try:
        result = pdf_anonymizer.anonymize(
            "test_files/sample.pdf",
            method="char",
            char="*"
        )
        print(f"   ✓ 脱敏完成: {result}")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")
    
    # 示例3：批量脱敏
    print("\n3. 批量PDF脱敏:")
    pdf_files = [
        "test_files/doc1.pdf",
        "test_files/doc2.pdf"
    ]
    # 过滤不存在的文件
    existing_files = [f for f in pdf_files if os.path.exists(f)]
    if existing_files:
        results = pdf_anonymizer.anonymize_batch(
            existing_files,
            method="mask"
        )
        for input_file, output_file in results.items():
            if output_file:
                print(f"   ✓ {Path(input_file).name} -> {Path(output_file).name}")
            else:
                print(f"   ✗ {Path(input_file).name} 脱敏失败")
    else:
        print("   ℹ️ 没有找到测试文件，跳过批量脱敏示例")


def demo_word_anonymization():
    """Word文件脱敏示例"""
    print("\n" + "=" * 60)
    print("Word文件脱敏示例")
    print("=" * 60)
    
    # 创建Word脱敏器
    word_anonymizer = WordAnonymizer(
        language='zh',
        verbose=True,
        output_dir="./anonymized/word"
    )
    
    # 示例1：打码脱敏
    print("\n1. 打码脱敏:")
    try:
        result = word_anonymizer.anonymize(
            "test_files/sample.docx",
            method="mask"
        )
        print(f"   ✓ 脱敏完成: {result}")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")
    
    # 示例2：加密脱敏
    print("\n2. 加密脱敏:")
    try:
        result = word_anonymizer.anonymize(
            "test_files/sample.docx",
            method="encrypt",
            encryption_key="123456"
        )
        print(f"   ✓ 脱敏完成: {result}")
        print(f"   加密密钥: 123456 (请妥善保管)")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")
    
    # 示例3：伪造数据脱敏
    print("\n3. 伪造数据脱敏:")
    try:
        result = word_anonymizer.anonymize(
            "test_files/sample.docx",
            method="fake"
        )
        print(f"   ✓ 脱敏完成: {result}")
        print(f"   注: 使用伪造数据替换敏感信息")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")


def demo_excel_anonymization():
    """Excel文件脱敏示例"""
    print("\n" + "=" * 60)
    print("Excel文件脱敏示例")
    print("=" * 60)
    
    # 创建Excel脱敏器
    excel_anonymizer = ExcelAnonymizer(
        language='zh',
        verbose=True,
        output_dir="./anonymized/excel"
    )
    
    # 示例1：伪造数据脱敏
    print("\n1. 伪造数据脱敏:")
    try:
        result = excel_anonymizer.anonymize(
            "test_files/sample.xlsx",
            method="fake"
        )
        print(f"   ✓ 脱敏完成: {result}")
        print(f"   注: 生成符合统计规律的伪造数据")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")
    
    # 示例2：加密脱敏
    print("\n2. 加密脱敏:")
    try:
        result = excel_anonymizer.anonymize(
            "test_files/sample.xlsx",
            method="encrypt",
            encryption_key="654321"
        )
        print(f"   ✓ 脱敏完成: {result}")
        print(f"   加密密钥: 654321")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")


def demo_image_anonymization():
    """图片文件脱敏示例"""
    print("\n" + "=" * 60)
    print("图片文件脱敏示例")
    print("=" * 60)
    
    # 创建图片脱敏器
    image_anonymizer = ImageAnonymizer(
        language='zh',
        verbose=True,
        output_dir="./anonymized/image"
    )
    
    # 示例1：颜色填充脱敏
    print("\n1. 颜色填充脱敏（黑色）:")
    try:
        result = image_anonymizer.anonymize(
            "test_files/sample.jpg",
            method="color",
            color="black"
        )
        print(f"   ✓ 脱敏完成: {result}")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")
    
    # 示例2：字符替换脱敏
    print("\n2. 字符替换脱敏:")
    try:
        result = image_anonymizer.anonymize(
            "test_files/sample.jpg",
            method="char",
            char="X"
        )
        print(f"   ✓ 脱敏完成: {result}")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")


def demo_ppt_anonymization():
    """PPT文件脱敏示例"""
    print("\n" + "=" * 60)
    print("PPT文件脱敏示例")
    print("=" * 60)
    
    # 创建PPT脱敏器
    ppt_anonymizer = PPTAnonymizer(
        language='zh',
        verbose=True,
        output_dir="./anonymized/ppt"
    )
    
    # 示例：打码脱敏
    print("\n1. 打码脱敏（保留格式）:")
    try:
        result = ppt_anonymizer.anonymize(
            "test_files/sample.pptx",
            method="mask"
        )
        print(f"   ✓ 脱敏完成: {result}")
        print(f"   注: 完整保留原始PPT格式")
    except Exception as e:
        print(f"   ✗ 脱敏失败: {e}")


def demo_comprehensive():
    """综合示例：处理多种文件类型"""
    print("\n" + "=" * 60)
    print("综合示例：批量处理多种文件类型")
    print("=" * 60)
    
    # 准备测试文件
    test_files = []
    
    # PDF文件
    if os.path.exists("test_files/sample.pdf"):
        test_files.append(("pdf", "test_files/sample.pdf"))
    
    # Word文件
    if os.path.exists("test_files/sample.docx"):
        test_files.append(("word", "test_files/sample.docx"))
    
    # Excel文件
    if os.path.exists("test_files/sample.xlsx"):
        test_files.append(("excel", "test_files/sample.xlsx"))
    
    if not test_files:
        print("ℹ️ 没有找到测试文件")
        return
    
    print(f"\n找到 {len(test_files)} 个测试文件:")
    for file_type, file_path in test_files:
        print(f"  - {file_type.upper()}: {file_path}")
    
    # 创建各种脱敏器
    anonymizers = {
        'pdf': PDFAnonymizer(),
        'word': WordAnonymizer(),
        'excel': ExcelAnonymizer(),
        'image': ImageAnonymizer(),
        'ppt': PPTAnonymizer()
    }
    
    print("\n开始批量脱敏...")
    
    for file_type, file_path in test_files:
        anonymizer = anonymizers.get(file_type)
        if anonymizer:
            try:
                print(f"\n处理 {file_type.upper()} 文件: {Path(file_path).name}")
                result = anonymizer.anonymize(
                    file_path,
                    method="mask"  # 统一使用mask方法
                )
                print(f"  ✓ 脱敏成功: {Path(result).name}")
            except Exception as e:
                print(f"  ✗ 脱敏失败: {e}")


def demo_advanced_features():
    """高级功能示例"""
    print("\n" + "=" * 60)
    print("高级功能示例")
    print("=" * 60)
    
    # 示例1：自定义输出目录
    print("\n1. 自定义输出目录:")
    custom_anonymizer = PDFAnonymizer(
        output_dir="./custom_output/processed_files"
    )
    print(f"   输出目录: {custom_anonymizer.output_dir}")
    
    # 示例2：详细日志模式
    print("\n2. 详细日志模式:")
    verbose_anonymizer = WordAnonymizer(verbose=True)
    print(f"   日志级别: DEBUG")
    
    # 示例3：英文脱敏
    print("\n3. 英文敏感信息识别:")
    english_anonymizer = ExcelAnonymizer(language='en')
    print(f"   语言: English")
    
    print("\n高级功能说明：")
    print("  - 自定义配置: 可通过配置文件或环境变量配置")
    print("  - 插件扩展: 支持自定义识别器和脱敏算法")
    print("  - 性能优化: 支持多线程和流式处理")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("File Anonymization SDK - 基础使用示例")
    print("=" * 60)
    
    # 创建测试文件目录
    test_dir = setup_test_files()
    print(f"测试文件目录: {test_dir}")
    print("注：请将测试文件放置在 test_files/ 目录下")
    print("=" * 60)
    
    # 执行各个示例
    demo_pdf_anonymization()
    demo_word_anonymization()
    demo_excel_anonymization()
    demo_image_anonymization()
    demo_ppt_anonymization()
    demo_comprehensive()
    demo_advanced_features()
    
    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 查看 examples/ 目录下的更多示例")
    print("2. 运行命令行工具: file-anonymizer --help")
    print("3. 启动API服务器: file-anonymizer api")
    print("4. 参考 README.md 获取完整文档")
    print("=" * 60)


if __name__ == "__main__":
    main()