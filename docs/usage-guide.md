# 使用指南

## 安装布局与升级

从仓库根目录运行 `python3 install.py --dest ~/.codex/skills`。安装器把 `skills/` 下六个技能及 `shared/` 复制到目标目录，改写共享文档的相对路径，不修改宿主设置或模型选择。

```text
~/.codex/skills/
  nanyin-ecommerce-image/
  nanyin-ecommerce-photography/
  nanyin-ecommerce-detail/
  nanyin-ecommerce-marketing/
  nanyin-ecommerce-edit/
  nanyin-ecommerce-consistency/
  nanyin-ecommerce-shared/
```

全套适合总控协调。`--skills edit` 可仅安装编辑技能和共享资源，但跨专业任务需要完整套件；该选项不是对已有安装的增量升级。任一目标目录存在时安装器拒绝覆盖，应先备份七个目录、核对改动，再由用户选择替换版本。项目 job 目录独立保存，不放进技能源码。

Codex 安装后需由宿主重新发现技能。其他支持技能文件的智能体可读取六个入口和共享资源，但工具名称与导入规则取决于宿主；本项目没有验证 Claude、Lavart 等平台的自动导入或实际生图兼容性。

## 从资料到成图

1. 附上商品图或明确授权原创概念款，提供已知名称、卖点、必要规格和交付用途。已给内容不会要求重复填写。完整资料范围见 [商品信息引导](../skills/nanyin-ecommerce-image/references/intake.md)。
2. 智能体区分用户事实、图中观察、设计建议和未知项，按传播任务规划逐张文案与构图。说“先方案”则停在方案；资料足够且已授权制作时继续生成。
3. 指定摄影、详情、营销、编辑或模特需求；跨专业由总控协调，同一个 asset 只归一个专业技能负责。技能模块不自动创建子 Agent。
4. 内置生成由当前智能体按实际工具 schema 调用 image_gen；本地参考先查看。工具不可用时明确说明，不静默切到外部付费接口。
5. 逐张保存实际结果，核对产品、文字与构图；文件下载、解码或哈希通过不代表视觉或平台审核通过。交付注明完成项和 `not_checked` 项。

只要提示词时明确说“不生成图片”。可要求独立中文、英文文件，画面文字语言另行指定。本套件没有强制所有任务都使用双语或固定字数。

## 批量记录与恢复

简单单图可直接调用内置工具；需要可靠批量记录时，基于 [模板](../shared/assets/templates/plan.example.json) 建立 `schema_version=2` 的 plan.json。模板中的示例提示词与商品资料必须换成本次真实内容。参考文件路径相对 job，引用哈希须与文件匹配，依赖图位排在前面。

安装后 `<shared>` 指 `~/.codex/skills/nanyin-ecommerce-shared`；下列占位路径在执行前换为实际路径，使用安装依赖的 Python 环境：

```bash
python <shared>/scripts/ecommerce.py validate-plan --job <job目录>
python <shared>/scripts/ecommerce.py prepare --job <job目录>
```

`call_image_gen_once` 才表示需要新调用；`recover_or_inspect_previous_tool_call` 表示应先检查已有结果。Python 不执行内置模型，智能体实际调用后才登记真实返回文件：

```bash
python <shared>/scripts/ecommerce.py record --job <job目录> --asset <asset_id> --source <真实返回文件> --evidence <工具结果标识>
python <shared>/scripts/ecommerce.py status --job <job目录>
python <shared>/scripts/ecommerce.py check --job <job目录>
```

已冻结计划不能直接改写；修改使用新 asset／job 版本，保留旧图。中断后先检查原任务及工具返回，不重复提交结果未知的调用。详见 [执行指南](../shared/references/execution.md)。

## 千问与火山（可选）

用户明确选择外部服务后，复制 [配置模板](../shared/assets/templates/providers.example.json) 到仓库外的私有文件，按所用地域和实际模型填写 endpoint、model、参考图上限与参数。凭证只通过指定环境变量读取，不写进源码或 plan。

先用 `provider-info` 生成配置指纹；该命令不联网验证。费用范围、最大提交次数与配置指纹写入 plan.authorization，显式设置 plan.provider 后才允许提交。超时也计入提交次数。`resume` 只恢复已保存响应的下载；无响应时去服务商核对，不自动重发。

完整命令和停止条件见 [执行指南](../shared/references/execution.md)，协议来源见 [接口说明](../shared/references/providers/interfaces.md)。本次开源整理没有实测付费接口。

## 长图与交付

同宽模块可以按顺序拼接与切片：

```bash
python <shared>/scripts/ecommerce.py export --images <模块1> <模块2> --output <新目录> --slice-height 1600
```

工具不隐式缩放不同宽度图片。导出只是本地组装，不替代生图或逐字检查。最终清单至少列实际文件、尺寸、提示词、已检查项与未检查项；平台要求按本次后台或官方资料核对，不能把旧模板当成当前合规结论。
