# 共享工作协议

协调者是本job唯一业务资料写入者。子Skill读取work_order，返回work_result与plan_patch；由协调者合并。E执行器唯一写tasks和manifest。默认内置生图由智能体实际调用工具，E负责调用前准备和返回后的登记；可选外部接口由E提交。所有资产使用稳定asset_id、sku_id、step_id；同一asset只由一个专业Skill负责，图位跨专业拆成多个依赖asset。

job资料：brief.json含product、facts[{value,source,status}]、sku、audience、budget、revision；references.json含ref_id、path、sha256、role、preserve、allowed_changes；brand.json含颜色、字体、Logo；copy.json按asset、语言记录逐字文案及事实来源。用户陈述、文档事实、图中观察与未知分开。图像不能证明容量、认证、性能、销量或材料成分。

work_order：job_id、step_id、asset_id、owner_skill、brief_revision、reference_ids、platform_rule_ids、brand_revision、copy_revision、intent、preserve、allowed_changes、output_spec、depends_on、budget_scope、checks。
work_result：step_id、status(planned/completed/partial/blocked/handoff_required)、plan_patch、prompt_paths、task_record_paths、artifact_ids、checks、issues、handoff_request。

资料更新由协调者生成新revision，未执行计划重新核验；执行器冻结plan，已执行job不能直接改计划，修改生成新job版本并记录parent_job。直接使用子Skill可以建立最小资料，不必重复走总控。需要跨专业时移交总控且原技能放弃协调权。

加载范围：只读本步骤相关SKU、参考图和平台图位，不混用同批其他SKU素材。平台规则只读，外部接口配置指纹按账户隔离。已给信息和授权范围继承，不逐张重复提问。
