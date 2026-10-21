# 成图案例与检查说明

本页记录 README 展示的六张原始成图。案例属于维护者的「南殷AI保温杯」原创概念设计，来自 2026-10-20 的实际内置 image_gen 制作任务；本次仅选择、复制与发布已有图片，没有新增模型调用或修改图像像素。

## 案例一：构图差异

从八种布局系列的最终修复交付中选取极简留白、杂志编辑与巨物微距三张。系列沿用深海蓝、暖白和品牌橙，分别改变商品占比、阅读路径、景别与环境关系。

## 案例二：主题风格

从五种主题色主视觉中选取雾蓝、鼠尾草绿与石墨紫三张。杯身仍为暖白；变化的是环境、光线与主题配色，这三张不作为不同商品颜色 SKU 的示例。

## 原图清单

| 图片 | 原图 | 实际像素 |
|---|---|---|
| 极简留白 | [layout-minimal.png](images/showcase/layout-minimal.png) | 1086 × 1448 |
| 杂志编辑 | [layout-editorial.png](images/showcase/layout-editorial.png) | 1086 × 1448 |
| 巨物微距 | [layout-macro.png](images/showcase/layout-macro.png) | 1086 × 1448 |
| 雾蓝科技 | [style-mist-blue.png](images/showcase/style-mist-blue.png) | 1086 × 1448 |
| 鼠尾草绿 | [style-sage-green.png](images/showcase/style-sage-green.png) | 1086 × 1448 |
| 石墨紫光 | [style-graphite-purple.png](images/showcase/style-graphite-purple.png) | 1086 × 1448 |

图片以原始 PNG 收录，可直接查看大图。SHA-256 记录在仓库根目录 MANIFEST.json，便于核对文件；没有附带私有任务记录、凭证、参考库或开发机路径。

## 检查范围

本次逐张查看六张图，核对可见主要标题、杯型、N 标识、构图和主题差异；原图解码、尺寸、复制前后哈希与 README 引用另行校验。微距图有意裁切杯身，不要求画面出现杯身 Logo。

案例中的功能和文案属于概念表达，不构成真实硬件性能、App 实现或销售证明。没有进行全量逐字 OCR、精确 Logo 几何和色差测量、真实 App／硬件测试或平台审核；这些项目为 `not_checked`。历史多 SKU 测试存在尺寸不一致，本页未将该批次列作完整验收通过案例。

v1.2.0 发布时的执行器测试边界仍以 [验证报告](verification.md) 为准；本次新增历史成图展示，不表示对全部技能、模型或服务作了端到端认证。
