# File Anonymization SDK （文件脱敏SDK）

基于Presidio的多格式文件脱敏SDK，支持PDF、Word、Excel、图片、PPT文件的敏感信息脱敏处理。

## 1. 功能特性

- **多格式支持**：PDF、Word、Excel、图片(JPG/PNG等)、PPT
- **多种脱敏方法**：颜色填充、字符替换、打码、伪造数据、加密
- **中文优化**：专门优化的中文敏感信息识别（姓名、手机号、身份证号等）
- **多种使用方式**：命令行、Python SDK、REST API
- **格式保留**：Word/Excel/PPT脱敏后完整保留原始格式
- **批量处理**：支持单文件和批量文件脱敏
- **任务管理**：完整的任务状态跟踪和进度监控

## 2. 安装

### 2.1 基础安装
```bash
pip install file-anonymization-sdk
```

### 2.2 从源码安装
```bash
git clone https://github.com/yourusername/file-anonymization-sdk.git
cd file-anonymization-sdk
pip install -e .
```

**安装额外依赖**：
```python
# 中文NLP模型
python -m spacy download zh_core_web_trf

# Tesseract OCR（图片脱敏需要）
# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim

# macOS
brew install tesseract

# Windows：从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
```

## 3. 快速开始
**方式一：命令行使用**
```bash
# PDF脱敏
file-anonymizer pdf document.pdf --method color --color white

# Word脱敏
file-anonymizer word document.docx --method mask

# Excel脱敏
file-anonymizer excel data.xlsx --method fake

# 图片脱敏
file-anonymizer image photo.jpg --method char --char "*"

# PPT脱敏
file-anonymizer ppt presentation.pptx

# 启动API服务器
file-anonymizer api --host 0.0.0.0 --port 5000
```
**方式二：python代码中使用**
```python
from file_anonymizer_sdk import PDFAnonymizer

# 创建脱敏器
anonymizer = PDFAnonymizer(language='zh', verbose=True)

# 单文件脱敏
result = anonymizer.anonymize(
    "input.pdf",
    method="color",
    color="white"
)
print(f"脱敏完成: {result}")

# 批量脱敏
files = ["file1.pdf", "file2.pdf"]
results = anonymizer.anonymize_batch(
    files,
    method="char",
    char="*"
)
```
**方式三：API调用**
```bash
# 单文件脱敏
curl -X POST http://localhost:5000/api/anonymize/single \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "test.pdf",
    "file_type": "pdf",
    "method": "mask",
    "language": "zh"
  }'

# 文件上传脱敏
curl -X POST http://localhost:5000/api/upload/single \
  -F "file=@document.pdf" \
  -F "file_type=pdf" \
  -F "method=mask"

# 查询任务状态
curl http://localhost:5000/api/task/{task_id}

# 下载结果文件
curl http://localhost:5000/api/download/{task_id}/0 -o result.pdf
```

## 4. 支持文件类型和方法


| 文件类型	|支持格式	|支持方法|
|---|---|---|
| PDF	|.pdf	|mask, color, char|
| Word	|.docx, .doc|	fake, mask, encrypt|
| Excel	|.xlsx, .xls	|fake, mask, encrypt|
| Image	|.jpg, .jpeg, .png, .bmp, .tiff	|mask, color, char|
| PPT	|.pptx, .ppt|	mask|

## 5. 配置参数
**通用参数**
- `language`：语言（zh/en）
- `verbose`：详细输出模式
- `output_dir`：输出目录（默认：`./anonymized-datas`）

**特定参数**
- `color`：填充颜色(`white/black/red/blue`）
- `char`：替换任意字符
- `encrypt`：6位数字密钥

## 6. Docker部署
```bash
# 构建镜像
docker build -t anonymization-sdk .

# 运行容器
docker run -p 5000:5000 \
  -v ./data:/app/data \
  anonymization-sdk
```

## 7. 示例代码
更多使用示例请查看 examples/ 目录：

- basic_usage.py - 基础使用示例

- batch_processing.py - 批量处理示例

- api_server.py - API服务器示例

## 8. 安全性
- 所有上传文件存储在临时目录，处理完成后自动清理

- 支持加密脱敏，使用AES-256加密算法

- 任务状态信息存储在内存中，可配置持久化存储

- 支持文件大小限制和类型验证



