# Gemini Vision Chat

这是一个基于 Gemini 2.5 Pro 的多模态对话应用程序，支持同时处理文本和图像输入，并通过 OpenAI 兼容的接口格式与 Google Vertex AI 进行交互。

## Google Cloud 认证指南

当前项目使用 Google Cloud 服务账号进行认证。如果您要移植或部署此项目，需要进行以下设置：

### 认证流程概述

1. 项目通过以下代码设置认证文件路径：
   ```python
   os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ogcloud-458110-38b399810621.json"
   ```

2. 在访问 Google Cloud API 时，使用以下代码获取和刷新认证凭据：
   ```python
   credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
   credentials.refresh(google.auth.transport.requests.Request())
   ```

3. 项目ID硬编码为 `"ogcloud-458110"`，您需要更改为自己的项目ID

### 如何移植项目的认证

1. **创建 Google Cloud 项目**（如果您还没有）
   - 访问 [Google Cloud 控制台](https://console.cloud.google.com/)
   - 点击"创建项目"并完成设置

2. **启用必要的 API**
   - 在您的项目中启用以下 API：
     - Vertex AI API
     - Cloud Storage API（如果需要存储上传的图片）

3. **创建服务账号**
   - 在 Google Cloud 控制台中导航到"IAM 和管理" > "服务账号"
   - 点击"创建服务账号"
   - 填写服务账号名称和描述
   - 为服务账号分配必要的角色：
     - `Vertex AI User`
     - `Storage Object Viewer`（如果需要访问 Cloud Storage）

4. **创建并下载密钥文件**
   - 在服务账号列表中，找到您刚创建的服务账号
   - 点击"操作"中的"管理密钥"
   - 点击"添加密钥" > "创建新密钥"
   - 选择 JSON 格式并下载

5. **配置项目**
   - 将下载的 JSON 密钥文件放在项目根目录下
   - 修改代码中的环境变量设置，指向您的密钥文件：
     ```python
     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./your-key-file.json"
     ```
   - 或者，您可以通过以下方式设置环境变量（推荐）：
     - Windows:
       ```bash
       set GOOGLE_APPLICATION_CREDENTIALS=path\to\your-key-file.json
       ```
     - macOS/Linux:
       ```bash
       export GOOGLE_APPLICATION_CREDENTIALS=path/to/your-key-file.json
       ```
   - 设置其他环境变量以自定义配置：
     - Windows:
       ```bash
       set GOOGLE_CLOUD_PROJECT_ID=your-project-id
       set GOOGLE_CLOUD_LOCATION=your-preferred-region
       set GEMINI_API_KEY=your-api-key-if-using-proxy
       ```
     - macOS/Linux:
       ```bash
       export GOOGLE_CLOUD_PROJECT_ID=your-project-id
       export GOOGLE_CLOUD_LOCATION=your-preferred-region
       export GEMINI_API_KEY=your-api-key-if-using-proxy
       ```

### 环境变量说明

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `GOOGLE_APPLICATION_CREDENTIALS` | 服务账号密钥文件路径 | `./ogcloud-458110-38b399810621.json` |
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud 项目ID | `ogcloud-458110` |
| `GOOGLE_CLOUD_LOCATION` | Google Cloud 区域 | `us-central1` |
| `GEMINI_API_KEY` | 代理模式下的 Gemini API 密钥 | `YOUR_GEMINI_API_KEY` |

### 常见认证问题

1. **权限不足**
   - 症状：API 调用返回 403 错误
   - 解决方案：确保服务账号有足够的权限，检查 IAM 角色分配

2. **密钥文件不存在或路径错误**
   - 症状：出现文件未找到错误
   - 解决方案：确认密钥文件路径是否正确，文件是否存在

3. **项目 ID 不正确**
   - 症状：API 调用返回 404 错误
   - 解决方案：确保使用的是正确的项目 ID

4. **未启用必要的 API**
   - 症状：API 调用返回服务未启用错误
   - 解决方案：在 Google Cloud 控制台中启用必要的 API

## API路径说明

应用程序支持两种方式调用Gemini模型：

1. **Google Cloud Vertex AI 路径**（默认模式）：
   - 直接使用 Google Cloud 的 Vertex AI API，通过 OpenAI 兼容端点访问 Gemini 模型
   - 使用 `google/gemini-2.5-pro-preview-05-06` 模型
   - 需要 Google Cloud 项目和服务账号认证
   - 在企业环境中推荐使用，可以利用 Google Cloud 的配额、安全性和监控功能

2. **代理模式路径**（通过 `--proxy` 参数启用）：
   - 通过第三方代理服务访问 Gemini API
   - 使用自定义 API 密钥
   - 适用于无法直接访问 Google Cloud 的环境或测试场景
   - 需要提供有效的代理服务器URL

## 功能特性

- **多模态支持**：同时处理文本和图像输入
- **双模式运行**：
  - 命令行模式：适合脚本和批处理
  - Web界面模式：提供友好的用户交互界面
- **流式响应**：实时显示生成内容
- **OpenAI兼容格式**：使用与 OpenAI API 兼容的格式调用 Gemini
- **支持代理**：可选择使用代理服务访问 Gemini API

## 安装依赖

1. 确保已安装 Python 3.8 或更高版本
2. 安装所需的依赖包：

```bash
pip install google-auth google-auth-oauthlib openai flask
```

3. 配置 Google Cloud 认证：
   - 将您的 Google Cloud 服务账号密钥文件放在项目根目录下
   - 更新代码中的 `GOOGLE_APPLICATION_CREDENTIALS` 环境变量指向您的密钥文件

## 使用方法

### Web 界面模式

启动 Web 服务器：

```bash
python gemini_vision_chat.py --web
```

默认使用 Google Cloud Vertex AI 路径访问 Gemini 模型。如需使用代理模式，请添加 `--proxy` 和 `--proxy-url` 参数：

```bash
python gemini_vision_chat.py --web --proxy --proxy-url https://your-proxy-url.com
```

然后在浏览器中访问 http://127.0.0.1:5000

在 Web 界面中：
1. 输入文本提示（可选）
2. 上传图片（可选）
3. 点击"提交"按钮
4. 查看生成的响应

### 命令行模式

分析本地图片：

```bash
python gemini_vision_chat.py --image 图片路径.jpg --prompt "描述这张图片"
```

### 调试模式

启用调试模式以查看详细日志：

```bash
python gemini_vision_chat.py --web --debug
```

### 查看API路径

如果您想查看程序实际使用的是哪条API路径，可以使用以下命令：

```bash
# 查看默认API路径（Google Cloud Vertex AI）
python gemini_vision_chat.py --show-path

# 查看代理模式的API路径
python gemini_vision_chat.py --show-path --proxy --proxy-url https://your-proxy-url.com
```

程序会显示当前配置下使用的API路径信息，包括：
- 使用的API类型（Google Cloud Vertex AI 或 代理模式）
- 项目ID和区域（如果使用Google Cloud）
- 代理URL（如果使用代理模式）
- 使用的模型名称

### 参数说明

| 参数 | 描述 |
|------|------|
| `--web` | 启动 Web 界面模式 |
| `--image PATH` | 指定要分析的图片路径 |
| `--prompt TEXT` | 分析图片的提示文本，默认为"描述这张图片中的内容" |
| `--proxy` | 使用代理模式访问 Gemini API |
| `--proxy-url URL` | 指定代理服务器 URL |
| `--debug` | 启用调试模式，显示详细日志 |
| `--show-path` | 显示API调用路径信息并退出 |

## 示例

### 分析本地图片（使用 Google Cloud Vertex AI）

```bash
python gemini_vision_chat.py --image 示例图片.jpg --prompt "详细描述这张图片中的内容和情绪"
```

### 使用代理服务

```bash
python gemini_vision_chat.py --web --proxy --proxy-url https://your-proxy-url.com
```

## 技术实现

项目实现了以下技术集成：

1. **OpenAI 兼容接口**：
   - 利用 OpenAI Python 客户端库
   - 通过 OpenAI 兼容格式调用 Gemini 模型
   - 支持流式响应（streaming）

2. **Vertex AI 集成**：
   - 使用 Google Cloud 认证
   - 使用 Vertex AI 提供的 OpenAI 兼容端点
   - 设置必要的请求头 `x-vertex-ai-endpoint`

3. **多模态处理**：
   - 使用 OpenAI 兼容的多模态消息格式
   - 图像通过 base64 编码传输
   - 支持同时处理文本和图像输入

## 故障排除

如果遇到问题：

1. **API 连接问题**：
   - 在 Web 界面中，点击页面底部的"测试 API 连接"链接
   - 检查认证设置和 API 密钥
   - 确认网络连接正常

2. **图片上传失败**：
   - 确保图片格式为常见的类型（JPEG、PNG 等）
   - 检查图片大小是否过大（建议小于 4MB）

3. **响应错误**：
   - 启用调试模式获取详细错误信息
   - 检查控制台输出的错误日志

## 注意事项

- 请确保您有权访问 Google Vertex AI 和 Gemini 2.5 Pro 模型
- 如果您在中国大陆使用，可能需要配置代理
- 确保安全存储您的 API 密钥和服务账号凭证
- 本应用仅供演示和学习使用

## 许可证

本项目采用 MIT 许可证。 