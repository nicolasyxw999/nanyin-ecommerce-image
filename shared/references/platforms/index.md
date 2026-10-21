# 平台与图位规则核验

支持按抖音、淘宝、拼多多、Amazon、TikTok Shop、1688等目标规划。平台不是风格预设，按platform/marketplace/category/placement/language确定规则。

Amazon区分主图、辅图、A+；淘宝/拼多多区分主图、详情、活动广告；抖音区分商品图、直播静态素材、广告图；跨境区分站点与语言。规则包含宽高、比例、背景、可见文字、安全区、来源URL、checked_at、适用范围、verified。平台硬要求、摄影建议与用户指定尺寸分别记录。

本包不内置未经实时验证的强制数字。生产前优先阅读用户提供的后台规格或平台官方商家文档，记录实际来源；无法访问则按用户规格生产，platform_review=not_checked。禁止把参考库旧规格当当前合规结论。

rule记录示例字段：rule_id、platform、marketplace、category、placement、requirements、source_url、checked_at、verified。缺失规则不阻止概念方案，但不能声称可直接通过平台审核。
