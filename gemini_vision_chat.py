import os
import base64
from google.auth import default
import google.auth.transport.requests
import openai
import argparse
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

# 设置认证文件路径（用户需要将此替换为自己的服务账号密钥文件）
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ogcloud-458110-38b399810621.json"

# 从环境变量中获取Google Cloud项目ID，如果没有设置则使用默认值
GOOGLE_CLOUD_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT_ID", "ogcloud-458110")
# 从环境变量中获取Google Cloud区域，如果没有设置则使用默认值
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# HTML模板，用于创建简单的Web界面
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gemini 2.5 有点牛逼的 接 OpenAI-like 接口</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .input-section {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        textarea {
            height: 100px;
            width: 100%;
            padding: 10px;
        }
        .file-upload {
            margin-top: 10px;
        }
        button {
            padding: 10px 15px;
            background-color: #4285f4;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        .response {
            margin-top: 20px;
            white-space: pre-wrap;
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .stream {
            height: 300px;
            overflow-y: auto;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 14px;
        }
        .footer a {
            color: #4285f4;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Gemini 2.5 多模态演示</h1>
    <div class="container">
        <div class="input-section">
            <h2>输入文本</h2>
            <textarea id="prompt" placeholder="请输入您的问题..."></textarea>
            
            <div class="file-upload">
                <h2>上传图片</h2>
                <input type="file" id="image-upload" accept="image/*">
                <div id="image-preview" style="margin-top: 10px;"></div>
            </div>
            
            <button id="submit-btn">提交</button>
        </div>
        
        <div class="response">
            <h2>响应</h2>
            <div id="response-content" class="stream"></div>
        </div>
    </div>

    <div class="footer">
        <a href="/test-api" target="_blank">测试API连接</a>
    </div>

    <script>
        const imageUpload = document.getElementById('image-upload');
        const imagePreview = document.getElementById('image-preview');
        const promptTextarea = document.getElementById('prompt');
        const submitBtn = document.getElementById('submit-btn');
        const responseContent = document.getElementById('response-content');
        
        let base64Image = null;
        
        // 处理图片上传并显示预览
        imageUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '300px';
                img.style.maxHeight = '300px';
                imagePreview.innerHTML = '';
                imagePreview.appendChild(img);
                
                // 存储base64编码的图像（去掉开头的data:image/jpeg;base64,）
                base64Image = e.target.result.split(',')[1];
            };
            reader.readAsDataURL(file);
        });
        
        // 提交请求
        submitBtn.addEventListener('click', async function() {
            const prompt = promptTextarea.value.trim();
            if (!prompt && !base64Image) {
                alert('请输入文本或上传图片');
                return;
            }
            
            responseContent.textContent = '正在处理...';
            submitBtn.disabled = true;
            
            try {
                // 创建请求数据
                const messages = [{
                    role: 'user',
                    content: []
                }];
                
                // 添加文本部分
                if (prompt) {
                    messages[0].content.push({
                        type: 'text',
                        text: prompt
                    });
                }
                
                // 添加图像部分
                if (base64Image) {
                    messages[0].content.push({
                        type: 'image_url',
                        image_url: {
                            url: `data:image/jpeg;base64,${base64Image}`
                        }
                    });
                }
                
                // 发送请求
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ messages: messages }),
                });
                
                if (response.status !== 200) {
                    // 尝试解析错误消息
                    const errorData = await response.json();
                    throw new Error(`服务器错误 (${response.status}): ${errorData.error || '未知错误'}`);
                }
                
                // 处理流式响应
                responseContent.textContent = '';
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const text = decoder.decode(value);
                    responseContent.textContent += text;
                    responseContent.scrollTop = responseContent.scrollHeight;
                }
            } catch (error) {
                responseContent.textContent = `错误: ${error.message}`;
                console.error(error);
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
"""

app = Flask(__name__)

def get_gemini_client(use_proxy=False, proxy_url=None):
    if use_proxy:
        # 使用geminiapi代理
        if not proxy_url:
            raise ValueError("使用代理模式需要提供proxy_url参数")
            
        # 设置OpenAI客户端使用代理URL
        client = openai.OpenAI(
            base_url=f"{proxy_url}/v1",
            api_key=os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")  # 从环境变量获取或使用默认值
        )
        
        # 使用OpenAI兼容的chat.completions接口（通过代理到Gemini）
        model_name = "google/gemini-2.5-pro-preview-05-06"  # geminiapi默认会将此转换为正确的Gemini模型
        print("\n==============================================================")
        print(f"🔄 使用代理模式访问Gemini API：{proxy_url}")
        print(f"🤖 模型：{model_name}")
        print("==============================================================\n")
    else:
        # 直接使用Google Cloud的OpenAI兼容端点
        project_id = GOOGLE_CLOUD_PROJECT_ID
        location = GOOGLE_CLOUD_LOCATION
        
        # 获取访问令牌
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(google.auth.transport.requests.Request())
        
        # 创建OpenAI客户端，确保传递正确的headers
        client = openai.OpenAI(
            base_url=f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/endpoints/openapi",
            api_key=credentials.token,
            default_headers={"x-vertex-ai-endpoint": "true"}
        )
        
        # 使用官方推荐的model名称格式，确保使用支持视觉的型号
        model_name = "google/gemini-2.5-pro-preview-05-06" # 使用支持视觉的模型
        print("\n==============================================================")
        print(f"☁️ 使用Google Cloud Vertex AI访问Gemini API")
        print(f"🔑 项目ID：{project_id}，区域：{location}")
        print(f"🤖 模型：{model_name}")
        print("==============================================================\n")
    
    return client, model_name

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/test-api')
def test_api():
    """测试API连接和认证"""
    try:
        client, model_name = get_gemini_client()
        
        # 简单文本请求测试
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=10,
            stream=False
        )
        
        return jsonify({
            "status": "success",
            "model": model_name,
            "response": response.choices[0].message.content
        })
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/generate', methods=['POST'])
def generate_response():
    try:
        data = request.json
        print(f"收到请求数据: {data}")
        
        # 获取查询参数是否使用代理
        use_proxy = request.args.get('proxy', 'false').lower() == 'true'
        proxy_url = request.args.get('proxy_url', None)
        
        client, model_name = get_gemini_client(use_proxy=use_proxy, proxy_url=proxy_url)
        print(f"使用模型: {model_name}")
        
        # 提取消息内容
        messages = data.get('messages', [])
        if not messages:
            return jsonify({"error": "请求中缺少messages参数"}), 400
        
        print(f"请求消息结构: {messages}")
        
        try:
            # 检查消息格式是否正确
            for message in messages:
                if 'role' not in message or 'content' not in message:
                    return jsonify({"error": "消息格式错误，需要包含role和content字段"}), 400
                
                # 检查多模态格式是否正确
                if isinstance(message['content'], list):
                    for content_item in message['content']:
                        if 'type' not in content_item:
                            return jsonify({"error": "多模态内容格式错误，缺少type字段"}), 400
            
            print("开始调用API...")
            # 根据OpenAI兼容的多模态格式创建请求
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True
            )
            print("API调用成功，开始流式输出...")
            
            # 流式输出
            def generate():
                try:
                    for chunk in response:
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                except Exception as stream_error:
                    print(f"流式输出错误: {str(stream_error)}")
                    yield f"\n错误: {str(stream_error)}"
            
            return app.response_class(generate(), mimetype='text/plain')
        
        except Exception as api_error:
            print(f"API调用错误: {type(api_error).__name__}: {str(api_error)}")
            return jsonify({"error": f"API调用错误: {str(api_error)}"}), 500
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"服务器错误: {type(e).__name__}: {str(e)}")
        print(f"详细错误信息: {error_details}")
        return jsonify({"error": f"服务器错误: {str(e)}", "details": error_details}), 500

def main():
    parser = argparse.ArgumentParser(description='使用OpenAI兼容格式的Gemini API进行多模态分析')
    parser.add_argument('--proxy', action='store_true', help='使用geminiapi代理')
    parser.add_argument('--proxy-url', type=str, help='geminiapi代理的URL，例如：https://my-proxy.vercel.app')
    parser.add_argument('--image', type=str, help='要分析的图片路径')
    parser.add_argument('--prompt', type=str, default="描述这张图片中的内容", help='分析图片的提示')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--show-path', action='store_true', help='显示API调用路径信息并退出')
    args = parser.parse_args()
    
    # 如果只想查看API路径信息
    if args.show_path:
        client, model_name = get_gemini_client(use_proxy=args.proxy, proxy_url=args.proxy_url)
        print("API路径检查完成，程序退出。")
        return
        
    # 设置是否调试模式
    app.debug = args.debug
    
    if args.web:
        print("正在启动Web界面，请访问 http://127.0.0.1:5000")
        if args.debug:
            print("调试模式已启用，将显示详细日志")
        
        # 在启动前显示API路径
        get_gemini_client(use_proxy=args.proxy, proxy_url=args.proxy_url)
        
        app.run(debug=args.debug)
        return
    
    if args.image:
        # 检查文件是否存在
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"错误：图片文件 {args.image} 不存在")
            return
        
        # 获取客户端和模型
        client, model_name = get_gemini_client(use_proxy=args.proxy, proxy_url=args.proxy_url)
        
        # 编码图片为base64
        base64_image = encode_image(args.image)
        
        # 创建符合OpenAI规范的消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": args.prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        # 调用API
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            stream=True
        )
        
        # 流式输出响应
        print("\n=== Gemini 多模态分析 ===\n")
        try:
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="")
        except Exception as e:
            print(f"\n错误: {str(e)}")
        print("\n")
    else:
        print("错误：请提供一个图片文件路径或使用--web参数启动Web界面")

if __name__ == "__main__":
    main()