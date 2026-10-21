# 默认内置生图，可选千问与火山

默认provider=codex_builtin。不读取外部凭证，不要求OPENAI_API_KEY。内置能力来自当前Codex会话的image_gen工具，Python不能模拟调用它，也不提供虚构HTTP地址。先按imagegen技能选择生成/编辑路径。

## Codex默认工作流

1. 使用商品卡、参考角色和提示词规划逐张图位。单张直接请求可以直接调用工具；需要可靠批量记录时建立schema_version=2的plan.json，provider可省略。size=null表示记录实际尺寸，不承诺工具精确像素。
2. `python3 <shared>/scripts/ecommerce.py prepare --job <job目录>`返回可执行图位。action=call_image_gen_once才是新调用；recover_or_inspect_previous_tool_call表示之前已准备，先检查工具历史/现有结果，不能盲目再次生成。
3. 本地参考图先用view_image实际查看。随后调用当前会话真实image_gen：所有参考有本地路径时使用referenced_image_paths；有会话附图没有路径时按工具说明使用最小num_last_images_to_include，两者不同时传。全新生成不带参考参数。工具规则以当次schema为准，不发明size、model、output_path或mask字段。
4. 透明背景请求设transparent_background=true，编辑时保留原透明性，其他情况为false。每个图位单独调用；多图不是自动转API的理由。
5. 真实返回文件先查看、再保存到项目。若工具返回本地文件，用record登记；只返回会话图且无文件时先展示，并如实标记本地文件未取得，不假造路径或截图冒充原图。
6. `python3 <shared>/scripts/ecommerce.py record --job <job目录> --asset <asset_id> --source <工具实际返回文件> --evidence <可追溯工具结果标识或路径>`复制并验证图片。evidence是人工输入的追踪信息，不是工具真实性自动认证。不得用占位图填充成品。
7. 下一轮prepare会继续未就绪的依赖步骤；已完成图不重复调用。图不合格使用新版本，保留原结果和实际检查状态。

单图无需强制完整任务目录，但最终必须保存用户要求的文件并报告实际路径。内置不可用时明确说明；千问/火山须用户选择，不能静默回退。内置工具自身的异步等待使用宿主返回的等待机制，不用本地脚本伪造远端任务查询。

## 外部可选接口

复制assets/templates/providers.example.json到用户自定配置文件。支持qwen、volcengine，分别自定义完整HTTPS endpoint、model、api_key_env、parameters、max_reference_images和timeout_seconds。凭证只从指定环境变量读，不写入计划或配置。不同地域的千问地址与密钥需要匹配；自定义网关须兼容对应协议，配置该地址意味着将提示词、参考和凭证发送给该地址。

plan.provider必须显式选择qwen或volcengine。默认模型只从配置读取，避免计划偷换模型；params为单图参数覆盖，按模型官方文档填写。参考数量默认0，核对模型能力后填写实际数量；本地参考编码为data URI随请求发送，没有独立上传服务。专用mask参数未接入。

先运行：
```sh
python3 <shared>/scripts/ecommerce.py provider-info --provider qwen --config <配置文件>
```
返回配置指纹和接口/模型，不发网络请求或验证额度。用户已选择外部服务且授权费用范围后，plan.authorization填provider、max_submissions、config_fingerprint。接口无统一实时报价API，不伪造报价快照，计费按对应控制台核对。每个asset限定单图，外部超时提交也计入数量限制。

```sh
python3 <shared>/scripts/ecommerce.py validate-plan --job <job目录>
python3 <shared>/scripts/ecommerce.py run --job <job目录> --config <配置文件> --allow-submit
python3 <shared>/scripts/ecommerce.py resume --job <job目录> --config <配置文件>
```

同步请求结果立即保存于responses，之后下载与解码；resume仅恢复已有响应的下载，不重新提交。没有响应的submitting/unknown需先去服务商核对，不能凭request_id猜测存在查询API。已保存URL过期也不能自动再生成。响应含临时下载地址/图片内容，保留在本地任务目录，不公开分享。

## 共享本地工具

```sh
python3 <shared>/scripts/ecommerce.py status --job <job目录>
python3 <shared>/scripts/ecommerce.py check --job <job目录>
python3 <shared>/scripts/ecommerce.py export --images <按顺序模块> --output <新目录> --slice-height 1600
```

文件校验不代表商品/文字/平台审核通过。长图导出只拼接已生成模块，不替代模型编辑。Python≥3.10、Pillow、POSIX锁用于本地记录/验证/导出；requests仅外部接口使用。纯内置生成本身不依赖上述Python网络库。
