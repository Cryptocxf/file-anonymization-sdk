"""
命令行接口
提供统一的命令行操作界面
"""

import argparse
import sys
import os
from pathlib import Path
import logging

# 导入SDK模块
from . import (
    PDFAnonymizer, WordAnonymizer, ExcelAnonymizer,
    ImageAnonymizer, PPTAnonymizer, run_api_server
)
from .utils.logger import setup_logger

# 设置默认日志记录器
logger = setup_logger("cli", level="INFO")


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                          PriKit SDK                          ║
║                基于Presidio的多格式文件脱敏工具              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
使用方式:
  prikit [命令] [参数]

命令:
  pdf      - PDF文件脱敏
  word     - Word文件脱敏
  excel    - Excel文件脱敏
  image    - 图片文件脱敏
  ppt      - PPT文件脱敏
  api      - 启动API服务器
  help     - 显示帮助信息
  version  - 显示版本信息

示例:
  prikit pdf document.pdf --method color --color white
  prikit word document.docx --method mask
  prikit excel data.xlsx --method fake
  prikit image photo.jpg --method char --char "*"
  prikit ppt presentation.pptx
  prikit api --host 0.0.0.0 --port 5000

获取详细帮助:
  prikit [命令] --help
    """
    print(help_text)


def print_version():
    """打印版本信息"""
    from . import __version__
    print(f"PriKit SDK v{__version__}")


def handle_pdf_command(args):
    """处理PDF命令"""
    try:
        # 验证文件
        if not os.path.exists(args.input):
            logger.error(f"文件不存在: {args.input}")
            return 1
        
        # 创建脱敏器
        anonymizer = PDFAnonymizer(
            language=args.language,
            verbose=args.verbose,
            output_dir=args.output_dir
        )
        
        # 执行脱敏
        result = anonymizer.anonymize(
            input_path=args.input,
            output_path=args.output,
            method=args.method,
            color=args.color,
            char=args.char
        )
        
        print(f"✓ PDF脱敏完成: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"PDF脱敏失败: {e}")
        return 1


def handle_word_command(args):
    """处理Word命令"""
    try:
        # 验证文件
        if not os.path.exists(args.input):
            logger.error(f"文件不存在: {args.input}")
            return 1
        
        # 验证加密密钥
        if args.method == 'encrypt' and not args.key:
            logger.error("加密方法需要提供加密密钥，请使用 --key 参数")
            return 1
        
        # 创建脱敏器
        anonymizer = WordAnonymizer(
            language=args.language,
            verbose=args.verbose,
            output_dir=args.output_dir
        )
        
        # 执行脱敏
        result = anonymizer.anonymize(
            input_path=args.input,
            output_path=args.output,
            method=args.method,
            encryption_key=args.key
        )
        
        print(f"✓ Word脱敏完成: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"Word脱敏失败: {e}")
        return 1


def handle_excel_command(args):
    """处理Excel命令"""
    try:
        # 验证文件
        if not os.path.exists(args.input):
            logger.error(f"文件不存在: {args.input}")
            return 1
        
        # 验证加密密钥
        if args.method == 'encrypt' and not args.key:
            logger.error("加密方法需要提供加密密钥，请使用 --key 参数")
            return 1
        
        # 创建脱敏器
        anonymizer = ExcelAnonymizer(
            language=args.language,
            verbose=args.verbose,
            output_dir=args.output_dir
        )
        
        # 执行脱敏
        result = anonymizer.anonymize(
            input_path=args.input,
            output_path=args.output,
            method=args.method,
            encryption_key=args.key
        )
        
        print(f"✓ Excel脱敏完成: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"Excel脱敏失败: {e}")
        return 1


def handle_image_command(args):
    """处理图片命令"""
    try:
        # 验证文件
        if not os.path.exists(args.input):
            logger.error(f"文件不存在: {args.input}")
            return 1
        
        # 创建脱敏器
        anonymizer = ImageAnonymizer(
            language=args.language,
            verbose=args.verbose,
            output_dir=args.output_dir
        )
        
        # 执行脱敏
        result = anonymizer.anonymize(
            input_path=args.input,
            output_path=args.output,
            method=args.method,
            color=args.color,
            char=args.char
        )
        
        print(f"✓ 图片脱敏完成: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"图片脱敏失败: {e}")
        return 1


def handle_ppt_command(args):
    """处理PPT命令"""
    try:
        # 验证文件
        if not os.path.exists(args.input):
            logger.error(f"文件不存在: {args.input}")
            return 1
        
        # 创建脱敏器
        anonymizer = PPTAnonymizer(
            language=args.language,
            verbose=args.verbose,
            output_dir=args.output_dir
        )
        
        # 执行脱敏
        result = anonymizer.anonymize(
            input_path=args.input,
            output_path=args.output,
            method='mask'  # PPT只支持mask方法
        )
        
        print(f"✓ PPT脱敏完成: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"PPT脱敏失败: {e}")
        return 1


def handle_api_command(args):
    """处理API命令"""
    try:
        print("启动API服务器...")
        print(f"地址: http://{args.host}:{args.port}")
        print("按 Ctrl+C 停止服务器")
        print("-" * 50)
        
        # 启动API服务器
        run_api_server(
            host=args.host,
            port=args.port,
            debug=args.debug,
            upload_folder=args.upload_folder,
            output_folder=args.output_folder
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nAPI服务器已停止")
        return 0
    except Exception as e:
        logger.error(f"启动API服务器失败: {e}")
        return 1


def handle_batch_command(args):
    """处理批量命令"""
    try:
        # 验证输入目录
        if not os.path.exists(args.input_dir):
            logger.error(f"输入目录不存在: {args.input_dir}")
            return 1
        
        # 选择脱敏器
        anonymizer_class = None
        if args.file_type == 'pdf':
            anonymizer_class = PDFAnonymizer
        elif args.file_type == 'word':
            anonymizer_class = WordAnonymizer
        elif args.file_type == 'excel':
            anonymizer_class = ExcelAnonymizer
        elif args.file_type == 'image':
            anonymizer_class = ImageAnonymizer
        elif args.file_type == 'ppt':
            anonymizer_class = PPTAnonymizer
        else:
            logger.error(f"不支持的文件类型: {args.file_type}")
            return 1
        
        # 创建脱敏器
        anonymizer = anonymizer_class(
            language=args.language,
            verbose=args.verbose,
            output_dir=args.output_dir
        )
        
        # 查找文件
        from .utils.file_handler import FileHandler
        file_handler = FileHandler()
        
        extensions = FileHandler.FILE_TYPE_EXTENSIONS.get(args.file_type, [])
        files = []
        
        for ext in extensions:
            pattern = f"*{ext}"
            if args.recursive:
                import glob
                files.extend(glob.glob(f"{args.input_dir}/**/{pattern}", recursive=True))
            else:
                files.extend(Path(args.input_dir).glob(pattern))
        
        files = [str(f) for f in files]
        
        if not files:
            logger.warning(f"在目录 {args.input_dir} 中未找到 {args.file_type} 文件")
            return 0
        
        print(f"找到 {len(files)} 个文件:")
        for f in files[:5]:
            print(f"  - {Path(f).name}")
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个文件")
        
        # 准备参数
        kwargs = {'method': args.method}
        if args.file_type in ['pdf', 'image']:
            kwargs['color'] = args.color
            kwargs['char'] = args.char
        elif args.method == 'encrypt':
            if not args.key:
                logger.error("加密方法需要提供加密密钥，请使用 --key 参数")
                return 1
            kwargs['encryption_key'] = args.key
        
        # 执行批量脱敏
        print(f"\n开始批量脱敏...")
        results = anonymizer.anonymize_batch(files, **kwargs)
        
        # 显示结果
        print(f"\n批量脱敏完成:")
        successful = sum(1 for r in results.values() if r is not None)
        failed = len(results) - successful
        
        print(f"  成功: {successful}")
        print(f"  失败: {failed}")
        
        if failed > 0:
            print("\n失败文件:")
            for input_file, output_file in results.items():
                if output_file is None:
                    print(f"  - {Path(input_file).name}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        logger.error(f"批量脱敏失败: {e}")
        return 1


def create_parser():
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        description='PriKit SDK - 多格式文件脱敏工具',
        add_help=False
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 帮助命令
    help_parser = subparsers.add_parser('help', help='显示帮助信息')
    
    # 版本命令
    version_parser = subparsers.add_parser('version', help='显示版本信息')
    
    # PDF命令
    pdf_parser = subparsers.add_parser('pdf', help='PDF文件脱敏')
    pdf_parser.add_argument('input', help='输入PDF文件路径')
    pdf_parser.add_argument('--method', choices=['mask', 'color', 'char'], 
                          default='mask', help='脱敏方法（默认: mask）')
    pdf_parser.add_argument('--color', choices=['white', 'black', 'red', 'blue', 'green'], 
                          default='white', help='填充颜色（默认: white）')
    pdf_parser.add_argument('--char', help='替换字符（char方法使用）')
    pdf_parser.add_argument('--language', choices=['zh', 'en'], default='zh', 
                          help='语言（默认: zh）')
    pdf_parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    pdf_parser.add_argument('--output-dir', default='./anonymized-datas',
                          help='输出目录（默认: ./anonymized-datas）')
    pdf_parser.add_argument('--verbose', '-v', action='store_true', 
                          help='详细输出模式')
    
    # Word命令
    word_parser = subparsers.add_parser('word', help='Word文件脱敏')
    word_parser.add_argument('input', help='输入Word文件路径')
    word_parser.add_argument('--method', choices=['fake', 'mask', 'encrypt'], 
                          required=True, help='脱敏方法')
    word_parser.add_argument('--key', help='加密密钥（6位数字，仅encrypt方法需要）')
    word_parser.add_argument('--language', choices=['zh', 'en'], default='zh', 
                          help='语言（默认: zh）')
    word_parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    word_parser.add_argument('--output-dir', default='./anonymized-datas',
                          help='输出目录（默认: ./anonymized-datas）')
    word_parser.add_argument('--verbose', '-v', action='store_true', 
                          help='详细输出模式')
    
    # Excel命令
    excel_parser = subparsers.add_parser('excel', help='Excel文件脱敏')
    excel_parser.add_argument('input', help='输入Excel文件路径')
    excel_parser.add_argument('--method', choices=['fake', 'mask', 'encrypt'], 
                          required=True, help='脱敏方法')
    excel_parser.add_argument('--key', help='加密密钥（6位数字，仅encrypt方法需要）')
    excel_parser.add_argument('--language', choices=['zh', 'en'], default='zh', 
                          help='语言（默认: zh）')
    excel_parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    excel_parser.add_argument('--output-dir', default='./anonymized-datas',
                          help='输出目录（默认: ./anonymized-datas）')
    excel_parser.add_argument('--verbose', '-v', action='store_true', 
                          help='详细输出模式')
    
    # 图片命令
    image_parser = subparsers.add_parser('image', help='图片文件脱敏')
    image_parser.add_argument('input', help='输入图片文件路径')
    image_parser.add_argument('--method', choices=['mask', 'color', 'char'], 
                          default='mask', help='脱敏方法（默认: mask）')
    image_parser.add_argument('--color', choices=['white', 'black', 'red', 'blue', 'green'], 
                          default='white', help='填充颜色（默认: white）')
    image_parser.add_argument('--char', help='替换字符（char方法使用）')
    image_parser.add_argument('--language', choices=['zh', 'en'], default='zh', 
                          help='语言（默认: zh）')
    image_parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    image_parser.add_argument('--output-dir', default='./anonymized-datas',
                          help='输出目录（默认: ./anonymized-datas）')
    image_parser.add_argument('--verbose', '-v', action='store_true', 
                          help='详细输出模式')
    
    # PPT命令
    ppt_parser = subparsers.add_parser('ppt', help='PPT文件脱敏')
    ppt_parser.add_argument('input', help='输入PPT文件路径')
    ppt_parser.add_argument('--language', choices=['zh', 'en'], default='zh', 
                          help='语言（默认: zh）')
    ppt_parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    ppt_parser.add_argument('--output-dir', default='./anonymized-datas',
                          help='输出目录（默认: ./anonymized-datas）')
    ppt_parser.add_argument('--verbose', '-v', action='store_true', 
                          help='详细输出模式')
    
    # API命令
    api_parser = subparsers.add_parser('api', help='启动API服务器')
    api_parser.add_argument('--host', default='0.0.0.0', help='主机地址（默认: 0.0.0.0）')
    api_parser.add_argument('--port', type=int, default=5000, help='端口号（默认: 5000）')
    api_parser.add_argument('--debug', action='store_true', help='调试模式')
    api_parser.add_argument('--upload-folder', default='./uploads',
                          help='上传文件目录（默认: ./uploads）')
    api_parser.add_argument('--output-folder', default='./anonymized-datas',
                          help='输出文件目录（默认: ./anonymized-datas）')
    
    # 批量命令
    batch_parser = subparsers.add_parser('batch', help='批量文件脱敏')
    batch_parser.add_argument('input_dir', help='输入目录路径')
    batch_parser.add_argument('--file-type', choices=['pdf', 'word', 'excel', 'image', 'ppt'],
                          required=True, help='文件类型')
    batch_parser.add_argument('--method', help='脱敏方法')
    batch_parser.add_argument('--key', help='加密密钥（仅encrypt方法需要）')
    batch_parser.add_argument('--color', default='white', help='填充颜色（默认: white）')
    batch_parser.add_argument('--char', help='替换字符（char方法使用）')
    batch_parser.add_argument('--language', choices=['zh', 'en'], default='zh',
                          help='语言（默认: zh）')
    batch_parser.add_argument('--output-dir', default='./anonymized-datas',
                          help='输出目录（默认: ./anonymized-datas）')
    batch_parser.add_argument('--recursive', '-r', action='store_true',
                          help='递归查找文件')
    batch_parser.add_argument('--verbose', '-v', action='store_true',
                          help='详细输出模式')
    
    return parser


def main():
    """主函数"""
    # 打印横幅
    print_banner()
    
    # 创建解析器
    parser = create_parser()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        print_help()
        return 0
    
    # 解析参数
    try:
        args = parser.parse_args()
    except SystemExit:
        return 1
    
    # 处理命令
    if args.command == 'help':
        print_help()
        return 0
    elif args.command == 'version':
        print_version()
        return 0
    elif args.command == 'pdf':
        return handle_pdf_command(args)
    elif args.command == 'word':
        return handle_word_command(args)
    elif args.command == 'excel':
        return handle_excel_command(args)
    elif args.command == 'image':
        return handle_image_command(args)
    elif args.command == 'ppt':
        return handle_ppt_command(args)
    elif args.command == 'api':
        return handle_api_command(args)
    elif args.command == 'batch':
        return handle_batch_command(args)
    else:
        # 如果没有匹配的命令，显示帮助
        print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())