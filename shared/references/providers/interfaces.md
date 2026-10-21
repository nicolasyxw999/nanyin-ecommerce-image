# 可选接口契约与来源

核验日期：2026-10-20。以下只说明协议，模型能力与价格按实际账号、地域和当次官方文档确认。适配器采用同步单图模式，支持文字和图片参考；不包含流式、异步轮询、专用mask和组图。

## 千问 / 阿里云百炼

HTTP POST完整endpoint，Bearer环境变量凭证。请求包含model、input.messages（user，content内image data URI和text）、parameters。结果从output.choices[].message.content[].image提取，保存响应后下载。size参数使用宽*高。密钥与服务地域匹配，可配置业务空间专属域名。n固定1。

官方来源：[千问文生图](https://help.aliyun.com/zh/model-studio/qwen-image-api)、[千问图像编辑](https://help.aliyun.com/zh/model-studio/qwen-image-edit-api)。支持data URI的模型才接受本地参考；max_reference_images按当前模型上限配置。不要把文本模型名填入此适配器。

## 火山方舟 / Seedream

HTTP POST完整endpoint，通常路径/api/v3/images/generations；Bearer环境变量凭证。请求model、prompt、可选image数组、size、stream=false、sequential_image_generation=disabled。结果从data[].url或data[].b64_json取得。size参数使用宽x高，其他形式按选用模型文档配置。模型可为模型ID或用户推理接入点ID。

官方来源：[火山方舟图片生成API](https://docs.volcengine.com/docs/ark/image-generation-api?lang=zh&redirect=1)、[官方API文档中心](https://api.volcengine.com/api-docs/view?action=ImageGenerations&serviceCode=ark&version=2024-01-01)。网页正文依赖JavaScript，本次结合官方索引字段核验；没有真实账号调用，不宣称已验证服务端兼容性。

## Codex内置

执行规范以当前image_gen工具与imagegen技能为准。直接调用，不设置外部HTTP endpoint和API Key。图像路径来自工具返回，实际尺寸以文件检查为准。
