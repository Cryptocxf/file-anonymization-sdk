"""
API服务器
基于Flask的REST API服务
"""

import os
import sys
import time
import uuid
import threading
from typing import Dict, List, Optional
from pathlib import Path

# Flask相关
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# 项目模块
from ..core.pdf_anonymizer import PDFAnonymizer
from ..core.word_anonymizer import WordAnonymizer
from ..core.excel_anonymizer import ExcelAnonymizer
from ..core.image_anonymizer import ImageAnonymizer
from ..core.ppt_anonymizer import PPTAnonymizer

# 配置
DEFAULT_UPLOAD_FOLDER = './uploads'
DEFAULT_OUTPUT_FOLDER = './anonymized-datas'
DEFAULT_MAX_CONTENT_SIZE = 16 * 1024 * 1024  # 16MB

# 支持的文件类型
SUPPORTED_FILE_TYPES = {
    'excel': ['.xlsx', '.xls'],
    'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'],
    'pdf': ['.pdf'],
    'word': ['.docx', '.doc'],
    'ppt': ['.pptx', '.ppt']
}

# 支持的脱敏方法
ANONYMIZATION_METHODS = {
    'excel': ['fake', 'mask', 'encrypt'],
    'image': ['mask', 'color', 'char'],
    'pdf': ['mask', 'color', 'char'],
    'word': ['fake', 'mask', 'encrypt'],
    'ppt': ['mask']
}


class AnonymizationTask:
    """脱敏任务"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = 'pending'  # pending, processing, completed, failed
        self.progress = 0
        self.message = ''
        self.input_files = []
        self.output_files = []
        self.original_filenames = []
        self.start_time = time.time()
        self.end_time = None
        self.method = ''
        self.file_type = ''
        self.error = None


class APIServer:
    """API服务器类"""
    
    def __init__(self, upload_folder: str = DEFAULT_UPLOAD_FOLDER,
                 output_folder: str = DEFAULT_OUTPUT_FOLDER,
                 max_content_size: int = DEFAULT_MAX_CONTENT_SIZE):
        
        # 初始化Flask应用
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 配置
        self.app.config['UPLOAD_FOLDER'] = upload_folder
        self.app.config['OUTPUT_FOLDER'] = output_folder
        self.app.config['MAX_CONTENT_LENGTH'] = max_content_size
        self.app.config['JSON_AS_ASCII'] = False
        
        # 创建目录
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        # 任务存储
        self.tasks: Dict[str, AnonymizationTask] = {}
        
        # 注册路由
        self._register_routes()
        
        # 初始化日志
        self._setup_logging()
    
    def _setup_logging(self):
        """配置日志"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _register_routes(self):
        """注册API路由"""
        
        # 健康检查
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'service': 'File Anonymization API',
                'version': '1.0.0',
                'timestamp': time.time()
            })
        
        # 获取支持类型
        @self.app.route('/api/supported_types', methods=['GET'])
        def get_supported_types():
            return jsonify({
                'supported_file_types': SUPPORTED_FILE_TYPES,
                'anonymization_methods': ANONYMIZATION_METHODS
            })
        
        # 单文件脱敏（文件路径）
        @self.app.route('/api/anonymize/single', methods=['POST'])
        def single_file_anonymize():
            return self._handle_single_file_anonymize()
        
        # 批量文件脱敏（文件路径）
        @self.app.route('/api/anonymize/batch', methods=['POST'])
        def batch_file_anonymize():
            return self._handle_batch_file_anonymize()
        
        # 单文件上传脱敏
        @self.app.route('/api/upload/single', methods=['POST'])
        def upload_single_file():
            return self._handle_upload_single_file()
        
        # 批量文件上传脱敏
        @self.app.route('/api/upload/batch', methods=['POST'])
        def upload_batch_files():
            return self._handle_upload_batch_files()
        
        # 查询任务状态
        @self.app.route('/api/task/<task_id>', methods=['GET'])
        def get_task_status(task_id):
            return self._handle_get_task_status(task_id)
        
        # 下载结果文件
        @self.app.route('/api/download/<task_id>/<int:file_index>', methods=['GET'])
        def download_file(task_id, file_index):
            return self._handle_download_file(task_id, file_index)
    
    def _validate_file_path(self, file_path: str, file_type: str) -> tuple:
        """验证文件路径"""
        if not file_path:
            return False, "文件路径不能为空"
        
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in SUPPORTED_FILE_TYPES[file_type]:
            return False, f"不支持的文件格式，支持格式: {', '.join(SUPPORTED_FILE_TYPES[file_type])}"
        
        return True, "验证通过"
    
    def _validate_uploaded_file(self, file, file_type: str) -> tuple:
        """验证上传的文件"""
        if not file or file.filename == '':
            return False, "未提供文件或文件名为空"
        
        filename = file.filename
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in SUPPORTED_FILE_TYPES[file_type]:
            return False, f"不支持的文件格式，支持格式: {', '.join(SUPPORTED_FILE_TYPES[file_type])}"
        
        return True, "验证通过"
    
    def _save_uploaded_file(self, file, task_id: str) -> str:
        """保存上传的文件"""
        filename = file.filename
        unique_filename = f"{task_id}_{filename}"
        file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return file_path
    
    def _run_single_anonymization(self, task_id: str, file_path: str, 
                                 file_type: str, method: str, language: str = 'zh',
                                 encryption_key: Optional[str] = None,
                                 color: str = 'white', char: str = '*'):
        """运行单文件脱敏"""
        try:
            task = self.tasks[task_id]
            task.status = 'processing'
            task.progress = 20
            task.message = f'开始处理文件: {os.path.basename(file_path)}'
            
            # 获取原始文件名
            original_filename = os.path.basename(file_path)
            original_stem = Path(original_filename).stem
            
            # 根据文件类型选择脱敏器
            anonymizer = None
            if file_type == 'pdf':
                anonymizer = PDFAnonymizer(language=language, verbose=False)
                output_path = anonymizer.anonymize(
                    file_path, method=method, color=color, char=char
                )
            elif file_type == 'word':
                anonymizer = WordAnonymizer(language=language, verbose=False)
                output_path = anonymizer.anonymize(
                    file_path, method=method, encryption_key=encryption_key
                )
            elif file_type == 'excel':
                anonymizer = ExcelAnonymizer(language=language, verbose=False)
                output_path = anonymizer.anonymize(
                    file_path, method=method, encryption_key=encryption_key
                )
            elif file_type == 'image':
                anonymizer = ImageAnonymizer(language=language, verbose=False)
                output_path = anonymizer.anonymize(
                    file_path, method=method, color=color, char=char
                )
            elif file_type == 'ppt':
                anonymizer = PPTAnonymizer(language=language, verbose=False)
                output_path = anonymizer.anonymize(file_path, method=method)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            # 更新任务状态
            if os.path.exists(output_path):
                task.output_files.append(output_path)
                task.status = 'completed'
                task.progress = 100
                task.message = '脱敏完成'
            else:
                task.status = 'failed'
                task.message = '输出文件未生成'
            
            task.end_time = time.time()
            
        except Exception as e:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = 'failed'
                task.message = f'处理失败: {str(e)}'
                task.error = str(e)
                task.end_time = time.time()
            self.logger.error(f"任务 {task_id} 处理失败: {e}")
    
    def _run_batch_anonymization(self, task_id: str, file_paths: List[str], 
                                file_type: str, method: str, language: str = 'zh',
                                encryption_key: Optional[str] = None,
                                color: str = 'white', char: str = '*'):
        """运行批量脱敏"""
        try:
            task = self.tasks[task_id]
            task.status = 'processing'
            task.input_files = file_paths
            
            total_files = len(file_paths)
            
            for i, file_path in enumerate(file_paths):
                task.progress = int((i / total_files) * 80)
                task.message = f'正在处理文件 {i+1}/{total_files}: {os.path.basename(file_path)}'
                
                # 处理单个文件
                try:
                    if file_type == 'pdf':
                        anonymizer = PDFAnonymizer(language=language, verbose=False)
                        output_path = anonymizer.anonymize(
                            file_path, method=method, color=color, char=char
                        )
                    elif file_type == 'word':
                        anonymizer = WordAnonymizer(language=language, verbose=False)
                        output_path = anonymizer.anonymize(
                            file_path, method=method, encryption_key=encryption_key
                        )
                    elif file_type == 'excel':
                        anonymizer = ExcelAnonymizer(language=language, verbose=False)
                        output_path = anonymizer.anonymize(
                            file_path, method=method, encryption_key=encryption_key
                        )
                    elif file_type == 'image':
                        anonymizer = ImageAnonymizer(language=language, verbose=False)
                        output_path = anonymizer.anonymize(
                            file_path, method=method, color=color, char=char
                        )
                    elif file_type == 'ppt':
                        anonymizer = PPTAnonymizer(language=language, verbose=False)
                        output_path = anonymizer.anonymize(file_path, method=method)
                    
                    if output_path and os.path.exists(output_path):
                        task.output_files.append(output_path)
                    
                except Exception as e:
                    self.logger.error(f"处理文件 {file_path} 失败: {e}")
                    continue
            
            # 更新任务状态
            if task.output_files:
                task.status = 'completed'
                task.progress = 100
                task.message = f'批量处理完成，成功处理 {len(task.output_files)}/{total_files} 个文件'
            else:
                task.status = 'failed'
                task.message = '所有文件处理失败'
            
            task.end_time = time.time()
            
        except Exception as e:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = 'failed'
                task.message = f'批量处理失败: {str(e)}'
                task.error = str(e)
                task.end_time = time.time()
            self.logger.error(f"批量任务 {task_id} 处理失败: {e}")
    
    def _handle_single_file_anonymize(self):
        """处理单文件脱敏请求"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': '请求体必须是JSON格式'}), 400
            
            # 必需参数
            required_params = ['file_path', 'file_type', 'method']
            for param in required_params:
                if param not in data:
                    return jsonify({'error': f'缺少必需参数: {param}'}), 400
            
            file_path = data['file_path']
            file_type = data['file_type']
            method = data['method']
            
            # 参数验证
            if file_type not in SUPPORTED_FILE_TYPES:
                return jsonify({
                    'error': f'不支持的文件类型: {file_type}',
                    'supported_types': list(SUPPORTED_FILE_TYPES.keys())
                }), 400
            
            if method not in ANONYMIZATION_METHODS.get(file_type, []):
                return jsonify({
                    'error': f'不支持的脱敏方法: {method}',
                    'supported_methods': ANONYMIZATION_METHODS.get(file_type, [])
                }), 400
            
            # 文件路径验证
            is_valid, message = self._validate_file_path(file_path, file_type)
            if not is_valid:
                return jsonify({'error': message}), 400
            
            # 获取可选参数
            language = data.get('language', 'zh')
            encryption_key = data.get('encryption_key')
            color = data.get('color', 'white')
            char = data.get('char', '*')
            
            # 加密密钥检查
            if method == 'encrypt' and not encryption_key:
                return jsonify({'error': '加密方法需要提供encryption_key参数'}), 400
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务
            task = AnonymizationTask(task_id)
            task.input_files = [file_path]
            task.original_filenames = [os.path.basename(file_path)]
            task.method = method
            task.file_type = file_type
            self.tasks[task_id] = task
            
            # 启动后台任务
            thread = threading.Thread(
                target=self._run_single_anonymization,
                args=(task_id, file_path, file_type, method, language, encryption_key, color, char)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'status': 'pending',
                'message': '单文件脱敏任务已开始处理',
                'file_type': file_type,
                'method': method,
                'input_file': file_path
            }), 202
            
        except Exception as e:
            self.logger.error(f"单文件脱敏请求处理失败: {e}")
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    def _handle_batch_file_anonymize(self):
        """处理批量文件脱敏请求"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': '请求体必须是JSON格式'}), 400
            
            # 必需参数
            required_params = ['file_paths', 'file_type', 'method']
            for param in required_params:
                if param not in data:
                    return jsonify({'error': f'缺少必需参数: {param}'}), 400
            
            file_paths = data['file_paths']
            file_type = data['file_type']
            method = data['method']
            
            # 参数验证
            if not isinstance(file_paths, list) or len(file_paths) == 0:
                return jsonify({'error': 'file_paths必须是非空列表'}), 400
            
            if file_type not in SUPPORTED_FILE_TYPES:
                return jsonify({
                    'error': f'不支持的文件类型: {file_type}',
                    'supported_types': list(SUPPORTED_FILE_TYPES.keys())
                }), 400
            
            if method not in ANONYMIZATION_METHODS.get(file_type, []):
                return jsonify({
                    'error': f'不支持的脱敏方法: {method}',
                    'supported_methods': ANONYMIZATION_METHODS.get(file_type, [])
                }), 400
            
            # 获取可选参数
            language = data.get('language', 'zh')
            encryption_key = data.get('encryption_key')
            color = data.get('color', 'white')
            char = data.get('char', '*')
            
            # 加密密钥检查
            if method == 'encrypt' and not encryption_key:
                return jsonify({'error': '加密方法需要提供encryption_key参数'}), 400
            
            # 验证所有文件路径
            valid_files = []
            original_filenames = []
            for file_path in file_paths:
                is_valid, message = self._validate_file_path(file_path, file_type)
                if is_valid:
                    valid_files.append(file_path)
                    original_filenames.append(os.path.basename(file_path))
                else:
                    self.logger.warning(f"跳过无效文件 {file_path}: {message}")
            
            if not valid_files:
                return jsonify({'error': '没有有效的文件路径'}), 400
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务
            task = AnonymizationTask(task_id)
            task.input_files = valid_files
            task.original_filenames = original_filenames
            task.method = method
            task.file_type = file_type
            self.tasks[task_id] = task
            
            # 启动后台任务
            thread = threading.Thread(
                target=self._run_batch_anonymization,
                args=(task_id, valid_files, file_type, method, language, encryption_key, color, char)
            )
            thread.daemon = True
            thread.start()
            
            response = {
                'task_id': task_id,
                'status': 'pending',
                'message': f'批量脱敏任务已开始处理，共 {len(valid_files)} 个文件',
                'file_type': file_type,
                'method': method,
                'total_files': len(valid_files),
                'original_filenames': original_filenames
            }
            
            # 添加特定参数
            if file_type in ['pdf', 'image']:
                response['color'] = color
                response['char'] = char
            
            if method == 'encrypt' and encryption_key:
                response['encryption_key_provided'] = True
            
            return jsonify(response), 202
            
        except Exception as e:
            self.logger.error(f"批量文件脱敏请求处理失败: {e}")
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    def _handle_upload_single_file(self):
        """处理单文件上传脱敏请求"""
        try:
            # 检查文件
            if 'file' not in request.files:
                return jsonify({'error': '未提供文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '未选择文件'}), 400
            
            # 获取参数
            file_type = request.form.get('file_type', '').lower()
            method = request.form.get('method', '').lower()
            language = request.form.get('language', 'zh')
            encryption_key = request.form.get('encryption_key')
            color = request.form.get('color', 'white')
            char = request.form.get('char', '*')
            
            # 参数验证
            if not file_type:
                return jsonify({'error': '缺少file_type参数'}), 400
            
            if not method:
                return jsonify({'error': '缺少method参数'}), 400
            
            if file_type not in SUPPORTED_FILE_TYPES:
                return jsonify({
                    'error': f'不支持的文件类型: {file_type}',
                    'supported_types': list(SUPPORTED_FILE_TYPES.keys())
                }), 400
            
            if method not in ANONYMIZATION_METHODS.get(file_type, []):
                return jsonify({
                    'error': f'不支持的脱敏方法: {method}',
                    'supported_methods': ANONYMIZATION_METHODS.get(file_type, [])
                }), 400
            
            # 验证上传的文件
            is_valid, message = self._validate_uploaded_file(file, file_type)
            if not is_valid:
                return jsonify({'error': message}), 400
            
            # 加密密钥检查
            if method == 'encrypt' and not encryption_key:
                return jsonify({'error': '加密方法需要提供encryption_key参数'}), 400
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 保存上传的文件
            file_path = self._save_uploaded_file(file, task_id)
            
            # 创建任务
            task = AnonymizationTask(task_id)
            task.input_files = [file_path]
            task.original_filenames = [file.filename]
            task.method = method
            task.file_type = file_type
            self.tasks[task_id] = task
            
            # 启动后台任务
            thread = threading.Thread(
                target=self._run_single_anonymization,
                args=(task_id, file_path, file_type, method, language, encryption_key, color, char)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'status': 'pending',
                'message': '单文件上传脱敏任务已开始处理',
                'file_type': file_type,
                'method': method,
                'original_filename': file.filename
            }), 202
            
        except Exception as e:
            self.logger.error(f"单文件上传脱敏请求处理失败: {e}")
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    def _handle_upload_batch_files(self):
        """处理批量文件上传脱敏请求"""
        try:
            # 检查文件
            if 'files' not in request.files:
                return jsonify({'error': '未提供文件'}), 400
            
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                return jsonify({'error': '未选择文件'}), 400
            
            # 获取参数
            file_type = request.form.get('file_type', '').lower()
            method = request.form.get('method', '').lower()
            language = request.form.get('language', 'zh')
            encryption_key = request.form.get('encryption_key')
            color = request.form.get('color', 'white')
            char = request.form.get('char', '*')
            
            # 参数验证
            if not file_type:
                return jsonify({'error': '缺少file_type参数'}), 400
            
            if not method:
                return jsonify({'error': '缺少method参数'}), 400
            
            if file_type not in SUPPORTED_FILE_TYPES:
                return jsonify({
                    'error': f'不支持的文件类型: {file_type}',
                    'supported_types': list(SUPPORTED_FILE_TYPES.keys())
                }), 400
            
            if method not in ANONYMIZATION_METHODS.get(file_type, []):
                return jsonify({
                    'error': f'不支持的脱敏方法: {method}',
                    'supported_methods': ANONYMIZATION_METHODS.get(file_type, [])
                }), 400
            
            # 加密密钥检查
            if method == 'encrypt' and not encryption_key:
                return jsonify({'error': '加密方法需要提供encryption_key参数'}), 400
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 验证和保存所有文件
            valid_files = []
            original_filenames = []
            
            for file in files:
                if file.filename == '':
                    continue
                
                is_valid, message = self._validate_uploaded_file(file, file_type)
                if is_valid:
                    file_path = self._save_uploaded_file(file, task_id)
                    valid_files.append(file_path)
                    original_filenames.append(file.filename)
                else:
                    self.logger.warning(f"跳过无效文件 {file.filename}: {message}")
            
            if not valid_files:
                return jsonify({'error': '没有有效的文件'}), 400
            
            # 创建任务
            task = AnonymizationTask(task_id)
            task.input_files = valid_files
            task.original_filenames = original_filenames
            task.method = method
            task.file_type = file_type
            self.tasks[task_id] = task
            
            # 启动后台任务
            thread = threading.Thread(
                target=self._run_batch_anonymization,
                args=(task_id, valid_files, file_type, method, language, encryption_key, color, char)
            )
            thread.daemon = True
            thread.start()
            
            response = {
                'task_id': task_id,
                'status': 'pending',
                'message': f'批量上传脱敏任务已开始处理，共 {len(valid_files)} 个文件',
                'file_type': file_type,
                'method': method,
                'total_files': len(valid_files),
                'original_filenames': original_filenames
            }
            
            # 添加特定参数
            if file_type in ['pdf', 'image']:
                response['color'] = color
                response['char'] = char
            
            if method == 'encrypt' and encryption_key:
                response['encryption_key_provided'] = True
            
            return jsonify(response), 202
            
        except Exception as e:
            self.logger.error(f"批量文件上传脱敏请求处理失败: {e}")
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    def _handle_get_task_status(self, task_id: str):
        """处理查询任务状态请求"""
        if task_id not in self.tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = self.tasks[task_id]
        
        response = {
            'task_id': task_id,
            'status': task.status,
            'progress': task.progress,
            'message': task.message,
            'input_files': task.input_files,
            'original_filenames': task.original_filenames,
            'output_files_count': len(task.output_files),
            'start_time': task.start_time,
            'method': task.method,
            'file_type': task.file_type
        }
        
        if task.end_time:
            response['end_time'] = task.end_time
            response['duration'] = round(task.end_time - task.start_time, 2)
        
        if task.error:
            response['error'] = task.error
        
        if task.status == 'completed' and task.output_files:
            response['download_urls'] = [
                f"/api/download/{task_id}/{i}" for i in range(len(task.output_files))
            ]
            response['output_filenames'] = [Path(path).name for path in task.output_files]
        
        return jsonify(response)
    
    def _handle_download_file(self, task_id: str, file_index: int):
        """处理下载文件请求"""
        if task_id not in self.tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = self.tasks[task_id]
        
        if task.status != 'completed':
            return jsonify({'error': '任务未完成'}), 400
        
        if file_index < 0 or file_index >= len(task.output_files):
            return jsonify({'error': '文件索引无效'}), 400
        
        output_file = task.output_files[file_index]
        
        if not os.path.exists(output_file):
            return jsonify({'error': '文件不存在'}), 404
        
        try:
            filename = Path(output_file).name
            return send_file(
                output_file,
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )
        except Exception as e:
            self.logger.error(f"下载文件失败: {e}")
            return jsonify({'error': f'下载文件失败: {str(e)}'}), 500
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        current_time = time.time()
        old_task_ids = []
        
        for task_id, task in self.tasks.items():
            if task.end_time and (current_time - task.end_time) > (max_age_hours * 3600):
                old_task_ids.append(task_id)
        
        for task_id in old_task_ids:
            # 删除临时上传的文件
            for file_path in self.tasks[task_id].input_files:
                if file_path.startswith(self.app.config['UPLOAD_FOLDER']):
                    try:
                        os.remove(file_path)
                    except:
                        pass
            del self.tasks[task_id]
        
        if old_task_ids:
            self.logger.info(f"清理了 {len(old_task_ids)} 个旧任务")
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        运行API服务器
        
        Args:
            host: 主机地址
            port: 端口号
            debug: 调试模式
        """
        print("=" * 60)
        print("          文件脱敏工具集 - API 服务")
        print("=" * 60)
        print("核心API端点:")
        print("  POST /api/anonymize/single - 单文件脱敏（文件路径）")
        print("  POST /api/anonymize/batch  - 多文件脱敏（文件路径）")
        print("  POST /api/upload/single    - 单文件上传脱敏")
        print("  POST /api/upload/batch     - 多文件上传脱敏")
        print("  GET  /api/task/<task_id>   - 查询任务状态")
        print("  GET  /api/download/<task_id>/<file_index> - 下载结果文件")
        print("  GET  /api/supported_types  - 获取支持类型")
        print("  GET  /api/health           - 健康检查")
        print("=" * 60)
        print(f"服务器地址: http://{host}:{port}")
        print("=" * 60)
        
        self.app.run(host=host, port=port, debug=debug)


def run_api_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False,
                   upload_folder: str = DEFAULT_UPLOAD_FOLDER,
                   output_folder: str = DEFAULT_OUTPUT_FOLDER):
    """
    运行API服务器（便捷函数）
    
    Args:
        host: 主机地址
        port: 端口号
        debug: 调试模式
        upload_folder: 上传文件目录
        output_folder: 输出文件目录
    """
    server = APIServer(
        upload_folder=upload_folder,
        output_folder=output_folder
    )
    server.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_api_server()