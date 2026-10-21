---
name: nanyin-ecommerce-marketing
description: 用户需要广告KV、促销海报、直播静态素材、带货种草或社媒配图时使用；已有底图仅改字交编辑技能。
metadata:
  author: "南殷居士"
  version: "1.2.0"
  homepage: "https://nanyinai.vip/"
  repository: "https://github.com/nicolasyxw999/nanyin-ecommerce-image"
---

# 南殷营销视觉

维护署名：南殷居士。公开内容品牌：南殷用AI。官网：https://nanyinai.vip/ 。

作者身份只用于技能介绍，不自动加入客户商品图、Logo、水印或导流文案。完整套件与安装入口：https://github.com/nicolasyxw999/nanyin-ecommerce-image 。

从活动事实、受众和图位确定一个传播重点，产出构图和短文案。将品牌锚点与参考角色传入执行计划，并核查活动信息。

## 开始与共享资料

先读取 [共享工作协议](../../shared/references/protocol.md)，只读取本任务所需的商品卡、参考映射、品牌规范与文案。专业方法见 [制作方法](references/method.md)；平台图位见 [平台核验指南](../../shared/references/platforms/index.md)。这些路径以本SKILL.md为基准，不依赖当前工作目录。

主技能总控任务时由主技能交付；直接调用本子技能时，本技能是唯一协调者。超出职责时返回handoff_required，沿用job_id移交主技能，不启动递归调用。Skill是能力模块，不自动创建子Agent。

## 制作与执行

1. 整理已知资料、保留项、允许修改项和交付规格，只询问真正缺失的信息。
2. 依据专业方法形成图位与提示词；共享事实附来源，缺失参数不补造。遵守“先方案”或已授权生成范围。
3. 读取 [执行指南](../../shared/references/execution.md)，建立plan.json并校验。默认provider=codex_builtin，由当前智能体调用真实image_gen生成/编辑，不需要API Key。使用imagegen技能并遵守当前工具schema；共享脚本只准备计划和登记返回的真实文件。只有用户明确选择千问或火山时才走外部接口，禁止失败后静默切换。
4. 结果检查按 [质量清单](../../shared/references/quality.md)；只报告实际检查。不将下载成功称为视觉验收通过。
5. 交付实际文件、提示词和未完成项。恢复时读取原任务；结果未知的调用不可自动再次提交。

内置调用中断先检查已返回图片；外部同步接口仅从已保存响应恢复下载，不伪造taskId轮询。修复使用新asset/job版本，保留原始结果；在已授权预算内最多修复两次，不自动扩大费用。
