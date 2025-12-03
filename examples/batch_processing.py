#!/usr/bin/env python3
"""
批量处理示例
展示如何使用File Anonymization SDK进行批量文件脱敏
"""

import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from prikit import (
    PDFAnonymizer,
    WordAnonymizer,
    ExcelAnonymizer,
    ImageAnonymizer,
    PPTAnonymizer
)


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, output_base_dir="./batch_output"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各种脱敏器
        self.anonymizers = {
            '.pdf': PDFAnonymizer(output_dir=str(self.output_base_dir / "pdf")),
            '.docx': WordAnonymizer(output_dir=str(self.output_base_dir / "word")),
            '.doc': WordAnonymizer(output_dir=str(self.output_base_dir / "word")),
            '.xlsx': ExcelAnonymizer(output_dir=str(self.output_base_dir / "excel")),
            '.xls': ExcelAnonymizer(output_dir=str(self.output_base_dir / "excel")),
            '.jpg': ImageAnonymizer(output_dir=str(self.output_base_dir / "image")),
            '.jpeg': ImageAnonymizer(output_dir=str(self.output_base_dir / "image")),
            '.png': ImageAnonymizer(output_dir=str(self.output_base_dir / "image")),
            '.pptx': PPTAnonymizer(output_dir=str(self.output_base_dir / "ppt")),
            '.ppt': PPTAnonymizer(output_dir=str(self.output_base_dir / "ppt")),
        }
        
        # 默认脱敏方法
        self.default_methods = {
            '.pdf': 'mask',
            '.docx': 'mask',
            '.doc': 'mask',
            '.xlsx': 'fake',
            '.xls': 'fake',
            '.jpg': 'color',
            '.jpeg': 'color',
            '.png': 'color',
            '.pptx': 'mask',
            '.ppt': 'mask',
        }
    
    def find_files(self, input_dir, recursive=True):
        """查找目录中的所有支持文件"""
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"输入目录不存在: {input_dir}")
        
        all_files = []
        if recursive:
            for ext in self.anonymizers.keys():
                all_files.extend(input_path.rglob(f"*{ext}"))
        else:
            for ext in self.anonymizers.keys():
                all_files.extend(input_path.glob(f"*{ext}"))
        
        return [str(f) for f in all_files]
    
    def get_file_type(self, file_path):
        """获取文件类型"""
        ext = Path(file_path).suffix.lower()
        return ext
    
    def process_single_file(self, file_path, method=None, **kwargs):
        """处理单个文件"""
        ext = self.get_file_type(file_path)
        
        if ext not in self.anonymizers:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        anonymizer = self.anonymizers[ext]
        
        # 使用默认方法或指定方法
        if method is None:
            method = self.default_methods.get(ext, 'mask')
        
        try:
            # 根据不同文件类型设置参数
            if ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                if method == 'color':
                    kwargs.setdefault('color', 'white')
                elif method == 'char':
                    kwargs.setdefault('char', '*')
            
            # 执行脱敏
            output_path = anonymizer.anonymize(
                input_path=file_path,
                method=method,
                **kwargs
            )
            
            return {
                'input': file_path,
                'output': output_path,
                'success': True,
                'message': '脱敏成功'
            }
            
        except Exception as e:
            return {
                'input': file_path,
                'output': None,
                'success': False,
                'message': str(e)
            }
    
    def process_batch_sequential(self, file_paths, method=None, **kwargs):
        """顺序批量处理"""
        results = []
        
        print(f"开始顺序处理 {len(file_paths)} 个文件...")
        
        for file_path in tqdm(file_paths, desc="处理进度"):
            result = self.process_single_file(file_path, method, **kwargs)
            results.append(result)
        
        return results
    
    def process_batch_parallel(self, file_paths, method=None, max_workers=4, **kwargs):
        """并行批量处理"""
        results = []
        
        print(f"开始并行处理 {len(file_paths)} 个文件，工作线程数: {max_workers}...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self.process_single_file, file_path, method, **kwargs): file_path
                for file_path in file_paths
            }
            
            # 等待任务完成
            for future in tqdm(as_completed(future_to_file), total=len(file_paths), desc="处理进度"):
                file_path = future_to_file[future]
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    results.append(result)
                except Exception as e:
                    results.append({
                        'input': file_path,
                        'output': None,
                        'success': False,
                        'message': f"处理超时或异常: {str(e)}"
                    })
        
        return results
    
    def print_statistics(self, results):
        """打印处理统计信息"""
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success
        
        print("\n" + "=" * 60)
        print("批量处理统计")
        print("=" * 60)
        print(f"总文件数: {total}")
        print(f"成功: {success}")
        print(f"失败: {failed}")
        
        if failed > 0:
            print("\n失败文件列表:")
            for result in results:
                if not result['success']:
                    print(f"  - {Path(result['input']).name}: {result['message']}")
        
        # 按文件类型统计
        type_stats = {}
        for result in results:
            if result['success']:
                ext = self.get_file_type(result['input'])
                type_stats[ext] = type_stats.get(ext, 0) + 1
        
        print("\n按文件类型统计（成功）:")
        for ext, count in type_stats.items():
            print(f"  {ext}: {count} 个文件")
        
        print("=" * 60)


def example_simple_batch():
    """简单批量处理示例"""
    print("简单批量处理示例")
    print("-" * 40)
    
    processor = BatchProcessor(output_base_dir="./batch_output_simple")
    
    # 假设有一个包含文件的目录
    input_dir = "test_files"
    
    try:
        # 查找所有支持的文件
        files = processor.find_files(input_dir)
        
        if not files:
            print(f"在目录 {input_dir} 中未找到支持的文件")
            return
        
        print(f"找到 {len(files)} 个文件:")
        for file in files[:5]:  # 只显示前5个
            print(f"  - {Path(file).name}")
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个文件")
        
        # 顺序处理
        results = processor.process_batch_sequential(files)
        
        # 显示统计
        processor.print_statistics(results)
        
    except Exception as e:
        print(f"批量处理失败: {e}")


def example_parallel_batch():
    """并行批量处理示例"""
    print("\n并行批量处理示例")
    print("-" * 40)
    
    processor = BatchProcessor(output_base_dir="./batch_output_parallel")
    
    # 创建测试文件列表（模拟大量文件）
    test_files = []
    for i in range(10):
        test_files.append(f"test_files/sample_{i}.pdf")  # 假设有这些文件
    
    # 过滤实际存在的文件
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if not existing_files:
        print("没有找到测试文件，使用虚拟示例")
        # 使用实际存在的文件
        input_dir = "test_files"
        existing_files = processor.find_files(input_dir)
    
    if not existing_files:
        print("没有可处理的文件")
        return
    
    print(f"处理 {len(existing_files)} 个文件（并行模式）")
    
    # 并行处理
    start_time = time.time()
    results = processor.process_batch_parallel(
        existing_files,
        max_workers=2,  # 限制并发数，避免资源耗尽
        method=None  # 使用默认方法
    )
    end_time = time.time()
    
    # 显示统计
    processor.print_statistics(results)
    print(f"总处理时间: {end_time - start_time:.2f} 秒")


def example_custom_methods():
    """自定义脱敏方法示例"""
    print("\n自定义脱敏方法示例")
    print("-" * 40)
    
    processor = BatchProcessor(output_base_dir="./batch_output_custom")
    
    # 创建测试文件列表
    test_files = [
        "test_files/sample.pdf",
        "test_files/sample.docx",
        "test_files/sample.xlsx",
        "test_files/sample.jpg"
    ]
    
    # 过滤实际存在的文件
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if not existing_files:
        print("测试文件不存在，跳过此示例")
        return
    
    print("使用自定义脱敏方法处理:")
    for file in existing_files:
        ext = Path(file).suffix.lower()
        method_map = {
            '.pdf': 'char',
            '.docx': 'encrypt',
            '.xlsx': 'fake',
            '.jpg': 'color'
        }
        method = method_map.get(ext, 'mask')
        print(f"  - {Path(file).name}: {method}方法")
    
    # 逐个文件处理（因为方法不同）
    results = []
    for file in existing_files:
        ext = Path(file).suffix.lower()
        
        if ext == '.pdf':
            result = processor.process_single_file(file, method='char', char='#')
        elif ext == '.docx':
            result = processor.process_single_file(file, method='encrypt', encryption_key='123456')
        elif ext == '.xlsx':
            result = processor.process_single_file(file, method='fake')
        elif ext == '.jpg':
            result = processor.process_single_file(file, method='color', color='red')
        else:
            result = processor.process_single_file(file, method='mask')
        
        results.append(result)
    
    processor.print_statistics(results)


def example_error_handling():
    """错误处理示例"""
    print("\n错误处理示例")
    print("-" * 40)
    
    processor = BatchProcessor(output_base_dir="./batch_output_errors")
    
    # 创建包含各种情况的文件列表
    test_files = [
        "test_files/valid.pdf",      # 有效文件
        "test_files/nonexistent.txt", # 不存在文件
        "test_files/unsupported.rar", # 不支持格式
        "test_files/corrupted.docx",  # 损坏文件
    ]
    
    print("处理包含各种情况的文件列表:")
    for file in test_files:
        print(f"  - {file}")
    
    results = []
    for file in test_files:
        try:
            if not os.path.exists(file):
                raise FileNotFoundError(f"文件不存在: {file}")
            
            result = processor.process_single_file(file)
            results.append(result)
            
        except Exception as e:
            results.append({
                'input': file,
                'output': None,
                'success': False,
                'message': str(e)
            })
    
    print("\n处理结果详情:")
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {Path(result['input']).name}: {result['message']}")


def example_directory_structure():
    """目录结构保持示例"""
    print("\n目录结构保持示例")
    print("-" * 40)
    
    # 创建复杂的测试目录结构
    test_dir = Path("./test_directory_structure")
    test_dir.mkdir(exist_ok=True)
    
    # 创建子目录和文件
    (test_dir / "project1" / "docs").mkdir(parents=True, exist_ok=True)
    (test_dir / "project1" / "data").mkdir(parents=True, exist_ok=True)
    (test_dir / "project2" / "reports").mkdir(parents=True, exist_ok=True)
    
    # 创建一些虚拟文件（实际应用中应该是真实文件）
    print("假设目录结构:")
    print(f"  {test_dir}/")
    print("  ├── project1/")
    print("  │   ├── docs/")
    print("  │   │   ├── manual.pdf")
    print("  │   │   └── spec.docx")
    print("  │   └── data/")
    print("  │       └── users.xlsx")
    print("  └── project2/")
    print("      └── reports/")
    print("          └── summary.pptx")
    
    print("\n在实际应用中，批量处理器可以:")
    print("1. 保持原始目录结构")
    print("2. 在输出目录中重建相同结构")
    print("3. 保持文件相对路径")
    
    # 演示如何实现目录结构保持
    class StructuredBatchProcessor(BatchProcessor):
        """保持目录结构的批量处理器"""
        
        def process_single_file(self, file_path, method=None, **kwargs):
            """重写单文件处理以保持目录结构"""
            input_path = Path(file_path)
            
            # 计算相对路径
            # 这里假设输入目录是已知的，实际应用中需要指定根目录
            # relative_path = input_path.relative_to(input_root)
            
            # 为了示例，我们创建一个简单的相对路径
            relative_path = input_path.name
            
            # 创建输出目录结构
            output_file = self.output_base_dir / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 调用父类方法（简化版）
            result = super().process_single_file(file_path, method, **kwargs)
            
            # 如果成功，更新输出路径
            if result['success']:
                result['structured_output'] = str(output_file)
            
            return result
    
    print("\n通过继承BatchProcessor类，可以轻松扩展功能来保持目录结构。")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("PriKit SDK - 批量处理示例")
    print("=" * 60)
    
    # 创建输出目录
    output_root = Path("./batch_examples_output")
    output_root.mkdir(exist_ok=True)
    
    # 执行各个示例
    example_simple_batch()
    example_parallel_batch()
    example_custom_methods()
    example_error_handling()
    example_directory_structure()
    
    print("\n" + "=" * 60)
    print("批量处理示例完成！")
    print("=" * 60)
    
    print("\n总结要点：")
    print("1. BatchProcessor类提供了统一的批量处理接口")
    print("2. 支持顺序和并行处理模式")
    print("3. 自动识别文件类型并选择合适的方法")
    print("4. 详细的统计信息和错误报告")
    print("5. 易于扩展自定义处理逻辑")
    
    print("\n输出目录:")
    print(f"  {output_root.absolute()}")
    
    print("\n下一步:")
    print("1. 查看生成的脱敏文件")
    print("2. 修改示例代码以适应实际需求")
    print("3. 集成到现有数据处理流程中")
    print("=" * 60)


if __name__ == "__main__":
    main()