# V3.2 第二轮测试报告

本次实际执行 **189 PASS / 0 FAIL / 0 SKIP**，执行UTC：2026-10-08T17:12:47.028795+00:00。

原Python70 + TypeScript13 = 原83；资格审计29；第一轮CNY45；第二轮补证32。未引用旧PASS代替本次执行。

- old_python_crisis：48通过；日志`checks/20261008T171247Z/old_python_crisis.log`。
- old_python_freeze：22通过；日志`checks/20261008T171247Z/old_python_freeze.log`。
- old_typescript：13通过；日志`checks/20261008T171247Z/old_typescript.log`。
- qualification：29通过；日志`checks/20261008T171247Z/qualification.log`。
- new_cny：45通过；日志`checks/20261008T171247Z/new_cny.log`。
- evidence_round2：32通过；日志`checks/20261008T171247Z/evidence_round2.log`。

类型检查通过。第二轮覆盖日期费用、同日发布门控、历史费率缺口、NAV不双扣、原件篡改、税主体与发布日期未知、上市前披露、缺年/重年/无效年度、全部11行六列、来源引用与重跑幂等、元数据再生成、临时目录补证、306冻结CSV、网页CSV一致及正式税后空值。

独立复核通过：492文件哈希、96组完整账本现金/净值/日期/终值/CAGR/MDD/佣金与假设税及FX汇总均核对；`--full`在临时目录重新生成96组压力和4组现金流，主引擎全部生成文件逐字节一致。日志`checks/20261008T171247Z/reproduction-full.log`。测试通过不等于IMPLEMENTABLE，真实税后合格组合仍0。旧版报告与首次运行器错误记录保留。
