#!/usr/bin/env python3
"""
API服务器示例
展示如何启动和使用PriKit的REST API服务
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, Any

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from file_anonymizer_sdk.api.api_server import run_api_server


class APIClient:
    """API客户端示例"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_supported_types(self):
        """获取支持的文件类型和方法"""
        try:
            response = self.session.get(f"{self.base_url}/api/supported_types")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def single_file_anonymize(self, file_path: str, file_type: str, 
                            method: str = "mask", **kwargs):
        """单文件脱敏（文件路径方式）"""
        payload = {
            "file_path": file_path,
            "file_type": file_type,
            "method": method,
            **kwargs
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/anonymize/single",
                json=payload,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def batch_file_anonymize(self, file_paths: list, file_type: str, 
                           method: str = "mask", **kwargs):
        """多文件脱敏（文件路径方式）"""
        payload = {
            "file_paths": file_paths,
            "file_type": file_type,
            "method": method,
            **kwargs
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/anonymize/batch",
                json=payload,
                timeout=60
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def upload_single_file(self, file_path: str, file_type: str, 
                         method: str = "mask", **kwargs):
        """单文件上传脱敏"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f)}
                data = {
                    'file_type': file_type,
                    'method': method,
                    **kwargs
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/upload/single",
                    files=files,
                    data=data,
                    timeout=60
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def upload_batch_files(self, file_paths: list, file_type: str, 
                         method: str = "mask", **kwargs):
        """多文件上传脱敏"""
        try:
            files = []
            for file_path in file_paths:
                with open(file_path, 'rb') as f:
                    files.append(('files', (Path(file_path).name, f)))
            
            data = {
                'file_type': file_type,
                'method': method,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/upload/batch",
                files=files,
                data=data,
                timeout=120
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_task_status(self, task_id: str):
        """查询任务状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/task/{task_id}",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def download_file(self, task_id: str, file_index: int = 0, 
                    save_path: str = None):
        """下载结果文件"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/download/{task_id}/{file_index}",
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                if save_path is None:
                    # 从Content-Disposition头获取文件名
                    content_disposition = response.headers.get('content-disposition')
                    if content_disposition:
                        filename = content_disposition.split('filename=')[1].strip('"')
                    else:
                        filename = f"result_{task_id}.pdf"
                    save_path = filename
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return {"success": True, "saved_to": save_path}
            else:
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def wait_for_task_completion(self, task_id: str, 
                               timeout: int = 300, 
                               interval: int = 2):
        """等待任务完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            if "error" in status:
                return status
            
            current_status = status.get("status", "unknown")
            progress = status.get("progress", 0)
            
            print(f"任务状态: {current_status}, 进度: {progress}%")
            
            if current_status in ["completed", "failed"]:
                return status
            
            time.sleep(interval)
        
        return {"error": f"任务超时（{timeout}秒）"}


def example_health_check():
    """健康检查示例"""
    print("API健康检查示例")
    print("-" * 40)
    
    client = APIClient()
    result = client.health_check()
    
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "healthy":
        print("✓ API服务运行正常")
    else:
        print("✗ API服务可能存在问题")


def example_supported_types():
    """获取支持类型示例"""
    print("\n获取支持的文件类型和方法")
    print("-" * 40)
    
    client = APIClient()
    result = client.get_supported_types()
    
    if "error" in result:
        print(f"请求失败: {result['error']}")
        return
    
    print("支持的文件类型:")
    for file_type, extensions in result.get("supported_file_types", {}).items():
        print(f"  {file_type}: {', '.join(extensions)}")
    
    print("\n支持的脱敏方法:")
    methods = result.get("anonymization_methods", [])
    print(f"  {', '.join(methods)}")


def example_pdf_single_file():
    """PDF单文件脱敏示例"""
    print("\nPDF单文件脱敏示例（文件路径方式）")
    print("-" * 40)
    
    client = APIClient()
    
    # 测试文件路径（请修改为实际存在的文件）
    test_file = "test_files/sample.pdf"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        print("请创建一个测试文件或修改文件路径")
        return
    
    print(f"处理文件: {test_file}")
    
    # 提交脱敏任务
    result = client.single_file_anonymize(
        file_path=test_file,
        file_type="pdf",
        method="mask",
        language="zh"
    )
    
    print(f"提交结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if "task_id" in result:
        task_id = result["task_id"]
        print(f"任务ID: {task_id}")
        
        # 等待任务完成
        print("\n等待任务完成...")
        final_status = client.wait_for_task_completion(task_id, timeout=60)
        
        print(f"最终状态: {json.dumps(final_status, indent=2, ensure_ascii=False)}")
        
        if final_status.get("status") == "completed":
            # 下载结果文件
            print("\n下载结果文件...")
            download_result = client.download_file(
                task_id=task_id,
                file_index=0,
                save_path="output_anonymized.pdf"
            )
            print(f"下载结果: {json.dumps(download_result, indent=2, ensure_ascii=False)}")


def example_image_upload():
    """图片上传脱敏示例"""
    print("\n图片上传脱敏示例")
    print("-" * 40)
    
    client = APIClient()
    
    # 测试文件路径
    test_file = "test_files/sample.jpg"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return
    
    print(f"上传文件: {test_file}")
    
    # 提交上传脱敏任务
    result = client.upload_single_file(
        file_path=test_file,
        file_type="image",
        method="color",
        color="white",
        language="zh"
    )
    
    print(f"提交结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if "task_id" in result:
        task_id = result["task_id"]
        
        # 等待并下载
        print("\n等待处理完成...")
        final_status = client.wait_for_task_completion(task_id, timeout=90)
        
        if final_status.get("status") == "completed":
            download_result = client.download_file(
                task_id=task_id,
                save_path="output_image.jpg"
            )
            print(f"下载结果: {json.dumps(download_result, indent=2, ensure_ascii=False)}")


def example_batch_processing():
    """批量处理示例"""
    print("\n批量文件脱敏示例")
    print("-" * 40)
    
    client = APIClient()
    
    # 准备测试文件列表
    test_files = []
    
    for ext in ['.pdf', '.docx', '.jpg']:
        test_file = f"test_files/sample{ext}"
        if os.path.exists(test_file):
            test_files.append(test_file)
    
    if not test_files:
        print("没有找到测试文件")
        return
    
    print(f"批量处理 {len(test_files)} 个文件:")
    for file in test_files:
        print(f"  - {file}")
    
    # 由于批量API要求文件类型相同，我们按类型分组处理
    files_by_type = {}
    for file in test_files:
        ext = Path(file).suffix.lower()
        if ext == '.pdf':
            file_type = 'pdf'
        elif ext in ['.docx', '.doc']:
            file_type = 'word'
        elif ext in ['.jpg', '.jpeg', '.png']:
            file_type = 'image'
        else:
            continue
        
        if file_type not in files_by_type:
            files_by_type[file_type] = []
        files_by_type[file_type].append(file)
    
    # 对每种类型分别处理
    all_results = {}
    for file_type, files in files_by_type.items():
        print(f"\n处理 {file_type} 类型文件 ({len(files)}个):")
        
        result = client.batch_file_anonymize(
            file_paths=files,
            file_type=file_type,
            method="mask"
        )
        
        print(f"提交结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "task_id" in result:
            task_id = result["task_id"]
            all_results[file_type] = {"task_id": task_id}
            
            # 等待任务完成
            final_status = client.wait_for_task_completion(task_id, timeout=120)
            
            if final_status.get("status") == "completed":
                # 下载所有文件
                output_files = final_status.get("output_filenames", [])
                for i, filename in enumerate(output_files):
                    save_name = f"batch_output_{file_type}_{i}_{filename}"
                    download_result = client.download_file(
                        task_id=task_id,
                        file_index=i,
                        save_path=save_name
                    )
                    print(f"  下载 {filename}: {download_result.get('success', False)}")
    
    return all_results


def example_error_cases():
    """错误情况处理示例"""
    print("\n错误情况处理示例")
    print("-" * 40)
    
    client = APIClient()
    
    # 测试用例1：不存在的文件
    print("1. 不存在的文件:")
    result = client.single_file_anonymize(
        file_path="nonexistent_file.pdf",
        file_type="pdf",
        method="mask"
    )
    print(f"   结果: {result.get('error', '未知错误')}")
    
    # 测试用例2：不支持的文件类型
    print("\n2. 不支持的文件类型:")
    result = client.single_file_anonymize(
        file_path="test_files/sample.txt",
        file_type="text",  # 不存在的类型
        method="mask"
    )
    print(f"   结果: {result.get('error', '未知错误')}")
    
    # 测试用例3：不支持的方法
    print("\n3. 不支持的方法:")
    result = client.single_file_anonymize(
        file_path="test_files/sample.pdf",
        file_type="pdf",
        method="invalid_method"
    )
    print(f"   结果: {result.get('error', '未知错误')}")
    
    # 测试用例4：缺少必需参数
    print("\n4. 缺少必需参数:")
    result = client.single_file_anonymize(
        file_path="test_files/sample.pdf",
        # 缺少 file_type
        method="mask"
    )
    print(f"   结果: {result.get('error', '未知错误')}")


def example_advanced_usage():
    """高级用法示例"""
    print("\n高级用法示例")
    print("-" * 40)
    
    client = APIClient()
    
    # 示例1：加密脱敏
    print("1. Word文件加密脱敏:")
    test_file = "test_files/sample.docx"
    
    if os.path.exists(test_file):
        result = client.single_file_anonymize(
            file_path=test_file,
            file_type="word",
            method="encrypt",
            encryption_key="123456"
        )
        print(f"   任务提交: {'成功' if 'task_id' in result else '失败'}")
    else:
        print("   测试文件不存在")
    
    # 示例2：自定义字符脱敏
    print("\n2. PDF文件自定义字符脱敏:")
    test_file = "test_files/sample.pdf"
    
    if os.path.exists(test_file):
        result = client.single_file_anonymize(
            file_path=test_file,
            file_type="pdf",
            method="char",
            char="#",
            color="black"
        )
        print(f"   任务提交: {'成功' if 'task_id' in result else '失败'}")
    else:
        print("   测试文件不存在")
    
    # 示例3：进度监控
    print("\n3. 任务进度监控:")
    print("   使用 get_task_status() 定期查询任务状态")
    print("   或使用 wait_for_task_completion() 等待完成")


def start_api_server():
    """启动API服务器（在后台线程中）"""
    import threading
    
    print("启动API服务器...")
    
    def run_server():
        run_api_server(host="127.0.0.1", port=5000, debug=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(3)
    
    return server_thread


def check_server_running():
    """检查服务器是否运行"""
    try:
        client = APIClient()
        result = client.health_check()
        return result.get("status") == "healthy"
    except:
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("File Anonymization SDK - API服务器示例")
    print("=" * 60)
    
    # 检查API服务器是否已运行
    if check_server_running():
        print("检测到API服务器已在运行")
        server_running = True
    else:
        print("API服务器未运行，将在示例结束后自动启动")
        print("如需手动启动，请运行: file-anonymizer api")
        server_running = False
    
    print("\n将演示以下API功能:")
    print("1. 健康检查和获取支持类型")
    print("2. 单文件脱敏（文件路径方式）")
    print("3. 文件上传脱敏")
    print("4. 批量文件脱敏")
    print("5. 错误情况处理")
    print("6. 高级用法示例")
    print("=" * 60)
    
    # 如果服务器未运行，启动它
    if not server_running:
        print("\n启动API服务器（可能需要一些时间）...")
        server_thread = start_api_server()
        
        # 等待服务器启动
        for i in range(10):
            if check_server_running():
                print("✓ API服务器启动成功")
                break
            time.sleep(1)
            print(".", end="", flush=True)
        else:
            print("\n✗ API服务器启动失败，请手动启动")
            return
    
    try:
        # 执行示例
        example_health_check()
        example_supported_types()
        example_pdf_single_file()
        example_image_upload()
        example_batch_processing()
        example_error_cases()
        example_advanced_usage()
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n执行出错: {e}")
    
    print("\n" + "=" * 60)
    print("API示例完成！")
    print("=" * 60)
    
    print("\n完整的API文档:")
    print("端点:")
    print("  POST /api/anonymize/single  - 单文件脱敏（文件路径）")
    print("  POST /api/anonymize/batch   - 批量文件脱敏（文件路径）")
    print("  POST /api/upload/single     - 单文件上传脱敏")
    print("  POST /api/upload/batch      - 批量文件上传脱敏")
    print("  GET  /api/task/{task_id}    - 查询任务状态")
    print("  GET  /api/download/{task_id}/{file_index} - 下载结果文件")
    print("  GET  /api/supported_types   - 获取支持类型")
    print("  GET  /api/health            - 健康检查")
    
    print("\n使用方式:")
    print("  命令行: prikti api --host 0.0.0.0 --port 5000")
    print("  Python: from prikit import run_api_server")
    print("  Docker: docker run -p 5000:5000 anonymization-sdk")
    print("=" * 60)


if __name__ == "__main__":
    main()