"""Write research results with explicit evidence gaps; never choose a winning cell."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/crisis-v32-cny'
def round2_summary(e):
 p=lambda v:f'{v*100:.4f}%'
 d=e['product_diagnostic']
 fees='\n'.join(f"| {x['code']} | {x['kind']} | {x.get('effective') or x.get('as_of')} | {x['published_at']} | {p(x['management_fee'])} / {p(x['custody_fee'])} | {x['source_id']} |" for x in e['fee_disclosures'])
 periods='\n'.join(f"| {x['start']} → {x['end']} | {p(x['fund_return'])} | {p(x['fund_return_std'])} | {p(x['benchmark_return'])} | {p(x['benchmark_return_std'])} | {p(x['reported_gap'])} | {p(x['reported_std_gap'])} | {x['date_access_label']} |" for x in e['product_periods'])
 return f"""**FREEZE / IMPLEMENTATION BLOCKED。** 7个成功原件、2次失败回执完整保存；{e['preserved_numeric_files']}个既有数值CSV SHA不变；真实税后合格组合0，真实交易0。前述历史代理实验和强基准全不改动。第二轮协议SHA `{e['protocol']['sha256']}`。

## 产品身份与费用披露

510300法定上市公告核实2012-05-28；2012年年报交叉验证。2024-11-20公告规定2024-11-22管理费0.50%→0.15%、托管0.10%→0.05%。这不是2011起固定费率，也不证明2026当前连续有效。年报URL路径2013-03-27与正文送出日期2013-03-28冲突：首次发布时刻未知，不自行填补PIT。

| 产品 | 证据类型 | 生效/快照日 | 文件发布日期 | 管理/托管年费率 | 来源 |
|---|---|---|---|---|---|
{fees}

513500招募书披露指数许可费0.06%及最低费用孰高条款；最低金额未在本次核实，不填0。2024概要0.91%为基于年报的综合运作费率估计，包含管理托管等，不能再加到0.60%+0.25%上，更不能从真实NAV重复外扣。历史快照不授予正式历史费率连续性。

## Level 2人民币基金净值披露

513500比较基准为S&P 500 **Net TR**，2024概要明确经估值汇率调整以人民币计价。Net TR不是毛股息再投指数；不能直接与美元价格指数比较。这是标普500基金产品诊断，不是ACWI映射或强基准替换。以原件第68–69页六列为准，NFKC/空白归一化只处理断行，不填漏值；两个差值列按原披露0.01%精度对账，全部11行保留。

| 区间 | 净值增长 | 披露标准差 | 基准增长 | 基准标准差 | 增长差 | 标准差差 | 可交易边界 |
|---|---:|---:|---:|---:|---:|---:|---|
{periods}

2014–2021八个完整披露年度的连乘诊断：基金CAGR **{p(d['fund_cagr'])}**，基准 **{p(d['benchmark_cagr'])}**，几何年化差 **{d['geometric_drag']*100:.4f}个百分点**，8年中7年落后；仅按四舍五入年度值复算。2014年初早于2014-01-15上市，属于基金Level 2，不能称全年可买收益。初始部分期、2022半年及累计期均不混入8年连乘。

披露标准差只保留原列，未推断其日/周年化频率；没有连续每日NAV，因此MDD、Sharpe、Sortino、个人税后CAGR和二级市场执行收益全部为空。年化差共同含费用、底层税、复制、现金与汇率口径，不隔离归因成“费用损耗”。这些历史文件2026才抓取，非已验证历史可知数据。

## 税主体与国债口径

财税字〔1998〕55号原文限定中国证监会新批准设立的**封闭式证券投资基金**。成文1998-08-06，追溯1998-03-01生效；首个可知发布时刻未验证，不把成文自动当发布时间，也不回穿历史信息集。营业税、历史印花税段不等同现行税表；未扩展为全部ETF/QDII免税，未批准投资者具体所得税应用。

中证事实表（截至2026-08-31）列H01006净价和N11006利息再投资。H11006/N11006现金利息公式、再投资机制与历史序列对账仍缺；不替换H11006，不用511010当然替代全期限国债。

## 可复算性与未解项

原件.raw与所有下载回执随复核包保存；稳定source_id引用核实来源，R2-标识独立下载尝试，失败不隐藏。产品元数据与主生成流程共用补证路径，临时目录全量复算读取同一冻结data快照。新增测试真实执行结果见TEST_REPORT.md；旧第12版报告/测试保存在archive/v32-version12。

{chr(10).join('- '+x for x in e['open_gaps'])}

这些缺口未齐前不授予IMPLEMENTABLE；暂停的定时任务不自动恢复。
"""

def main():
 r=json.loads((O/'results.json').read_text());r['sources']=json.loads((R/'data/v32-cny/data_sources.json').read_text());(O/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n');(O/'data_sources.json').write_text(json.dumps(r['sources']+json.loads((R/'data/v32-cny/column_provenance.json').read_text())+[r['provenance']],ensure_ascii=False,indent=2)+'\n');p=lambda n:'未验证' if n is None else f'{n*100:.3f}%'
 rows='\n'.join(f'| {x["scenario"]} | {x["label"]} | {p(x["proxy_cagr"])} | {p(x["proxy_liquidated_twr_cagr"])} | {p(x["proxy_mdd"])} | {p(x["turnover_annual"])} | {x["trade_count"]} | {x["cumulative_transaction_cost"]:.0f} | {x["cumulative_synthetic_tax"]:.0f} |' for x in r['proxy_summary'] if x['mode']=='annual')
 reb='\n'.join(f'| {x["scenario"]} | {x["mode"]} | {p(x["proxy_cagr_delta"])} | {p(x["proxy_mdd_delta"])} | {p(x["turnover_delta"])} | {x["transaction_cost_delta"]:.0f} | 无法验证 |' for x in r['complexity'])
 products='\n'.join(f'| {x["code"]} {x["name"]} | {x["inception"]} / {x["listed"]} | {x["index"]} | {p(x["management_fee"])} / {p(x["custody_fee"])} | {x["mapping_gap"]} |' for x in r['products'])
 tax='\n'.join(f'| {x["category"]} | {p(x["rate"])} | {x["published"]} / {x["effective"]} / {x["expires"]} | {x["scope"]} | {x["source_id"]} |' for x in r['tax_rules'])
 refs='\n'.join(f'- [{x["id"]} · {x["name"]}]({x["url"]})：等级{x["evidence_level"]}；{x["scope"]}。原始hash：{x.get("original_sha256") or "未取得/继承说明，不伪造原字节hash"}' for x in r['sources'])
 blocked='\n'.join('- '+x for x in r['blockers'])
 q=r['archive'];conf=r['registered'];stages='\n'.join(f'- **{k}**：{v}' for k,v in r['status_definitions'].items())
 report=f'''# V3.2 人民币税后可实施性研究

**Verdict：FREEZE / IMPLEMENTATION BLOCKED。**

**研究回答：数据不足，暂不能判断理论全球配置扣除大陆个人真实税收、汇兑、产品、溢价和准入摩擦后是否值得实施。没有批准任何真实组合；不发布伪精确的税后CAGR。**

本报告合并原第12版人民币研究与第二轮补证；旧版正文已归档。以下历史读取与代理计算属于第一轮，第二轮新增内容见第13节。

本轮不是V4权重优化。30/30/30/10与ACWI全球股票60%＋中国国债H11006 40%强基准冻结。原V3理论CAGR 7.9546%对9.0789%，111个重叠窗口只有8个领先；四档V3.1费用压力没有稳定翻盘，large场景6.795%对7.926%。这些负面结果、V2 Verdict C和原FREEZE结论保持，不删除年份/不更换强基准。强基准国债腿为中国国债，不是美国债券或泛全球60/40。

## 1. 只归档上一阶段，不宣布实盘资格已完成

读取源版本88c4dc17124851480ef988939333bc620d32deca，审读源码、历史报告、README、回测、原始HTML、账本、数据及测试；预修改清单读取1,016个文件、135,741,647字节、768份CSV/726,049行，见pre-change-inventory.json。旧83项测试完整保留；后续资格审计29项也保留。本轮独立新增测试，完整执行状态见TEST_REPORT.md。

云端只读归档{q['events']}条事件、{q['rawBlobs']}份原始资料，逐事件哈希链及原字节SHA核验通过；失败和旧报价仍在。链尾 `{q['head']}`。OOS NAV、强基准OOS NAV及真实成交仍无有效完整观测，不伪造0收益。每日自动采集保持暂停，没有创建或恢复任务；历史来源可以继续在网页归档调用。原协议仍是八项AND，新人民币研究没有回写或“放宽通过”旧资格结果。

## 2. 投资者模型与组合边界

默认：中国大陆税收居民，人民币工资与生活负债，本金100,000 CNY；普通境内证券/基金账户。没有默认美国/香港券商、海外银行、离岸美元、机构额度。

Research Portfolio可用ACWI/GLD基金代理、H00300与H11006历史指数；研究本身不形成购买路径。Implementable Portfolio必须在指定历史日期存在真实合法可得产品，上市、普通账户、资本来源、申购或二级交易、流动性、税务、费用和时点均通过。美股单指数、主动全球基金或5年国债ETF不能“走势像”就代替ACWI/全期限国债。

本轮五组正式比较：100%中国股票H00300、国内60/40、全球股票60%＋中国国债40%、冻结V3、相同权重的V3.2大陆候选（全球腿未映射）。五组真实CNY税后收益全部为空；前四组有理论代理压力，第五组没有偷偷用SP500填补30%全球腿。

## 3. 四层收益

1. Gross Asset Return：毛资产指数层；现有ACWI/GLD是已含费基金代理，不冒称毛指数。
2. Fund/Product Return：真实NAV或复权净值含管理、托管、底层税和实现跟踪差；不能重复扣管理/托管/跟踪误差。
3. Investor Pre-Tax Return：成交点差、佣金、申赎、溢折价及与渠道相符的换汇/汇款等。QDII人民币份额的个人层并不发生逐笔美元换汇。
4. Investor After-Tax CNY Return：`W_end_after_tax_CNY/W_start_CNY−1`。严格产品/所得适用通过才填值；本金与合理成本不是全部课税收入。

Actual Account模块支持份额与现金守恒、100份交易单位、经验证成本、平均CNY成本基础、已实现利得税、分红现金、净值含分红防双计、交易时点和原始报价验证。未匹配产品所得类别即阻塞。它是验证与记账引擎，不是实际下单系统，当前没有传入合格真实交易。税款结算、跨国分类抵免/结转和税务FX仍需完整申报事件；不把一个简单记账公式等同完整纳税申报。

## 4. 市场准入与外汇

五项分别是Legal / Account / Capital / Product / Liquidity。外汇管理办法区分经常与资本项目、境外投资通过有资格机构办理；购汇用途官方问答明确约束未开放资本项目。5万美元额度不能推导自由投资美股。合法已有境外资金可以另立情景，但不默认普通账户具备。

二级市场可以与一级申购暂停并存。上交所ETF问答最低100份，不把一级100,000份/大额创设门槛误当个人唯一交易门槛。然而二级可交易还须同步参考净值、价差和合理价格；普通渠道存在不等于组合已批准。这个新路径模型单独登记，不覆写旧8项AND。

**FX Return**：`CNY增长倍数=本币资产倍数×USD/CNY倍数`，有交互项，不能CAGR相加。**FX Friction**：真实兑换价差与手续费。ACWI底层多币种，黄金美元报价不是纯美元经济敞口。投资估值FX、税务折算中间价、真实兑换价三者区分；真实税务FX未齐不计算正式结果。

## 5. 税务规则：原文和产品适用分离

A级官方税法/监管原文，B级正式交易所/券商/招募材料，C二级资料，D估算。文件日期不等于逐日时刻：只有发布日期无时分秒的同日新规则，不能自动进入当天08:00知识集。历史生效和发布均检查；2020文件追溯2019不意味着2019已知。

| 类别 | 原文税率或暂免 | 发布/生效/到期 | 适用范围 | 来源 |
|---|---:|---|---|---|
{tax}

开放式基金的申赎差价与分配暂免条款，不自动拓展为每只QDII/黄金ETF的所有税种免征。基金底层预扣与投资者个人所得分开。A股股息公历1个月/1年分档按取得/登记记录，短持补扣不得当立即统一扣税。直接国债利息免税不等于债券价差免税，也不等于每只债基免税。港股通差价优惠到2027-12-31不涵盖全部股息。境外直接证券分类所得与有上限抵免要区分；不把基金自身纳税当个人抵免凭证。原2002文件部分营业税/历史印花条款不用于今日规则。

## 6. 产品映射与可得日期

| 产品 | 成立/上市 | 真实跟踪对象 | 披露管理/托管费 | 缺口 |
|---|---|---|---|---|
{products}

510300为华泰柏瑞，不是嘉实；第二轮正式上市公告及2012年年报交叉核实2012-05-28上市，已修正第一轮缺口。160706早于2011但法律形式转型须分段。518880、513100、513500及511010上市前没有INVESTABLE RETURN；指数历史标INDEX BACKFILL。上市后也不能用指数冒充真实产品净值。全球主动基金不因较早成立就成为严格ACWI映射。

新增来源更正：V3.1 S08所链华安2026-08-11页面是访谈，不足以独立核实正式费用。本轮使用518880产品资料概要核实其披露段管理0.50%/托管0.10%，不宣称贯穿2011或自动核实2026当日费率。511010与513100当前资料/网页披露有原文依据但无完整历史费率段；513500已取得2022/2024披露快照0.60%/0.25%；2026现行确认与连续费率历史仍未齐。历史原报告不回写，新增更正保留证据链。

H11006事实表单列N11006利息再投资指数。未完成编制方案与净值序列对账，不能自动把H11006称已验证全收益；5110105年久期更不能当全期限国债复制。保留原债券数据，不替换强基准再宣称收益提高。

## 7. QDII现实

管理/托管、底层税和跟踪差进入NAV，二级ETF另有价差与premium、QDII剩余额度、限购/暂停、跨境交易时差和异地休市。机构批额度不是具体基金实时剩额度。溢价需要同一参考时刻，昨日NAV与今日场价的比值不代表可套利的实时premium。

1%/3%/5%/10%警示压力全部保存。底层NAV不变，初始5%溢价归零，10万元中V3全球30%损失1,429元、强基准60%损失2,857元；10%压力分别2,727/5,455元。这是一次机制压力，不是今日报价或每年均值。折价同样支持，缺价格不填0。

## 8. 现实摩擦：条件压力结果

独立协议 `{conf['id']}`，登记 `{conf['registered_at']}`，指纹 `{conf['sha256']}`；先登记再计算，无权重/场景择优。四组合×四场景×六再平衡=96组；另有四组月入500元现金流实验。完整CSV、每日净值与逐笔压力账本均保存。

A单边5bp/最低0/额外产品0；B 15bp/最低5元/额外25bp/全球初始1%溢价；C 50bp/最低5/额外100bp/全球5%溢价；D再加10%全球溢价、50bp直接兑换和20%已实现正利得**假设税**。全部D级参数，不是券商报价或境内产品税率。D的DIRECT_FX是独立有条件渠道假设，不能作为默认QDII零售成本。额外产品损耗是统一代理复制差，不与已含管理费重复当真实收费。

新历史诊断对全部资产滞后一条本地日期；08:00先用前日标记，再下一观测日纸面交易，联合observed才交易。估值可保留旧非交易日标记，但不能当可成交价。没有恢复历史发布/抓取时点，当前复权历史修订仍可能影响研究；因此仍是理论诊断、不是无条件无前视实盘曲线。新首日2011-10-11、最后观测2026-09-30只知前日；与旧V3同期同日曲线不能数值替换。

下表年度代理压力；日NAV是持续持有记账值，清算CAGR另扣终端卖出费用/假设税。真实after-tax字段全空。期末条件清算逐资产费用、成本基础、假设税和净收入另列于liquidations目录；不是收盘后已经取得的真实成交报价。

| 场景 | 组合 | 代理持有CAGR | 代理清算CAGR | MDD | 年周转 | 成交数 | 全程含清算交易费 | 假设税 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
{rows}

年化波动及Sortino用周末最后可得估值、52周，Sortino MAR0为假设；Worst1Y/3Y使用过去边界以前的估值，不看未来。MDD/Ulcer/水下期由完整日曲线；Recovery只报已恢复周期最长值，当前未恢复起点单列。没有完整CPI不报Real CAGR，没有可比RF不报Sharpe，真实fund_expenses/tracking_error/FX contribution不能由统一损耗假设倒算。累计假设税与实际税字段分开；后者空。

## 9. 再平衡及复杂性

年度、半年、季度、绝对5个百分点、相对目标20%、只用现金流全部报告；没有“最佳规则”。买卖先卖后买，现金内联立缩放，最低费不造成透支。只用现金流不卖原持仓；每月500元贡献通过新增组合单位剔除存款效应（TWR），总贡献、利润、财富分开；不以末期总财富/初始10万元计算假收益。复权代理已有分红，不能再加虚构现金股息/利息。

| 场景 | 规则 | V3−强基准代理CAGR | MDD差 | 年周转差 | 交易费差 | 真实税后风险调整增量 |
|---|---|---:|---:|---:|---:|---|
{reb}

复杂度不是人为标价。V3比强基准多中国股票/黄金两腿，新增产品维护、基差与税务应用，默认仍为国内账户/CNY结算；底层币种与经济暴露不能用报价币种计数。两者共享全球映射和国债疑点。当前代理实验可以展示成本/周转/风险差，不能证明真实税后价值；不据单样本排名降低实施门槛。如果未来境内股债税后相当或领先，接受其结论。

## 10. 未解决问题与状态

{blocked}

{stages}

本轮不授予RESEARCH VALID的无条件标签（H11006待审）、PARTIALLY IMPLEMENTABLE或READY TO INVEST。没有实际税后数据支持STRATEGY REJECTED，也不支持宣布全球最优。可以称“研究框架与条件实验已实现 / 实施未验证”，理论分散化不等于实践价值已经成立。

## 11. 复算与文件

`python scripts/cny_implementability.py`生成96组代理实验和明确空的正式税后结果；`python scripts/test_cny_implementability.py`执行新增测试；`npm test`原13项；`node --test tests/implementation.test.mjs`原资格29项；旧Python70项见测试报告。`python scripts/reproduce_cny.py`核验全包hash、96组账本及现金/净值守恒；`--full`在临时目录重算全结果，不回写冻结档案。新复核ZIP含新协议/代码/测试/固定输入/全部新结果/37条归档事件及原字节；完整旧项目在站点源仓库与V1-V3.1原页面保存，不假称新ZIP是旧135MB文件的重复副本。

## 12. 来源

{refs}
'''
 if r.get('evidence_round2'):
  report+='\n## 13. 第二轮官方补证（2026-10-08 UTC / 北京时间恢复于10月9日）\n\n'+round2_summary(r['evidence_round2'])
 (O/'V3.2_IMPLEMENTABILITY_REPORT.md').write_text(report)
 assumptions='# V3.2 Assumptions / 全部实施假设\n\n正式默认账户CNY after tax；未知不按0处理。权重和强基准冻结。\n\n'
 assumptions+='\n'.join(f'## {a["id"]} · 等级{a["evidence"]}\n\n{a["text"]}\n\n影响：{a["impact"]}\n' for a in r['assumptions'])
 assumptions+='\n## 法律不是估算参数\n\n税收规则由tax_rules.json按所得、发布、生效和到期匹配；原文证据与产品适用另审。A/B来源身份不能自动提高假设等级；C/D税率不得作为正式结果依据。\n\n## 产品身份与归档\n\n无ACWI映射不拿标普/纳指替换。当前费用未从2011恒定回填；未知源时刻不得同日08:00使用。旧失败/负面结果不修改。每日任务仍暂停，没有新增实际交易。\n'
 if r.get('evidence_round2'):
  assumptions+='\n## 带日期披露与年度净值边界\n\n费用快照只证明披露时点；510300降费事件不证明所有历史段或2026现行连续性。0.91%综合运作费率为测算，不是另扣固定费用。真实NAV内费用与底层税不外扣；年度净值差含复制、费用、税、现金与汇率等共同影响。11段披露全部保留，仅8个完整年度连乘诊断；2014含上市前日期，非全年可交易收益。1998税文件成文日期非首个可知时刻，限定新批准封闭式基金，不能泛用ETF/QDII。\n'
 (O/'V3.2_ASSUMPTIONS.md').write_text(assumptions)
 audit=f'''# V3.2 Data Audit\n\n正式可实施数据完整度不足，after-tax字段全部为空。\n\n## 已归档\n\n源版本88c4dc17124851480ef988939333bc620d32deca；37事件/15原始文件，原字节及哈希链核验。数据不修订；既有失败留存。归档回执与事件原档附包。pre-change-inventory.json保留完整前置读取清单。\n\n## 历史输入\n\n{json.dumps(r['provenance'],ensure_ascii=False,indent=2)}\n\n每列独立column_provenance.json保存数据名/来源/代码/原文件SHA/覆盖/复权/缺数/发布时刻未知/非PIT/交易日对齐；下载时刻无可靠记录保持空。每列provenance：H00300沪深300全收益来自中证，H11006来自中证但利息再投资口径未验证；world-proxy=ACWI调整收盘×USD/CNY，gold=GLD调整收盘×USD/CNY，FX=Yahoo CNY=X，仅研究代理；没有真实境内ETF净值、分红或成交。全部逐列时间范围以冻结panel和原acquisition记录为准，旧输入SHA校验，人工衍生滞后1条。observed_*控制联合新报价纸面交易；非交易日持平只估值，不买卖。新每日CSV不含缺数值，但这不等于基础数据无问题：修订历史、假日标记、真实发布时间缺失仍在。\n\n## 官方来源\n\ndata_sources.json保存每项URL、下载/发布日期、等级、原字节SHA、失败状态、频率、代理与人工处理。既有S来源是继承的原文释义，未下载字节不伪造hash。新原字节见data/v32-cny/official；HTTP200不是应用资格，通过文本核对才能使用具体条款。来源失败保留不隐藏。\n\n## 上市与幸存者偏差\n\n上市前INDEX BACKFILL；上市后也不代表INDEX=PRODUCT。510300第二轮正式公告核实上市，listing_verified=true；513100/500、518880、511010有正式来源日期。候选由资产角色列出，未按历史收益选择；清单并非包含所有退市/清盘产品的幸存者无偏全集，实际长历史可实施比较尚不能成立。160706转型须另做时间段。\n\n## 税务时点\n\n只有发布日期的当天规则不用于当日08:00决策。effective与published分别检查，到期后阻塞；没有把后发追溯文件当早期已知。文件修改/失效须更新新带日期规则，不回写原登记。2002营业税与历史印花段不能视作今天税表；产品适用未验证保持UNCERTAIN。境外税FX转换不是Yahoo估值FX。\n\n## 空缺字段\n\n真实税后终值、actual累计税、实际fund expenses/跟踪误差、完整FX归因、CPI/RF、实时申购/剩额度、同步bid/ask与premium、完整历史产品NAV/现金分红、合格OOS均未齐。product-observations.csv、真实execution-ledger.csv只提供表头；不得用代理账本填入真实账本。\n\n## 更正\n\nV3.1 S08链接为访谈，不是充分正式费用证据；新518880资料概要有日期限定。旧归档保留，另追加说明。H11006/N11006未审完，本轮未换序列。\n\n## 可复查性\n\nmanifest逐文件SHA；全包复算使用固定输入和记录协议。原始CSV→研究引擎→压力逐笔账本→日净值→KPI全可复算。实际产品→CNY after-tax链尚被上述缺口阻断，不能冒称完整链已成立。\n'''
 if r.get('evidence_round2'):
  audit+='\n## 第二轮原件与解析核对\n\n'+round2_summary(r['evidence_round2'])
 (O/'V3.2_DATA_AUDIT.md').write_text(audit)
 changelog='''# V3.2 Changelog\n\n## 新增\n\n- 原资格审计只读归档37事件/15原始文件，含失败；不恢复暂停采集任务。\n- 独立CNY after-tax协议、普通大陆投资者模型、Research/Implementable分层。\n- 税法有效期、所得/产品应用与五项准入；FX变化与真实换汇摩擦分离。\n- 产品身份/上市门控、QDII同步premium、未验证字段和来源清单。160706明确为深圳LOF/基金渠道；未批准全球路径的准入保持未知。\n- 96组预登记压力、年度/半年/季度/双阈值/现金流；四组现金流TWR。\n- 真实CNY记账/税务验证模块；未知阻塞，不产生虚假实盘业绩。\n- 八节V3.2网页、首页FREEZE状态、强基准首屏、报告和全复核包。页内章节导航滚动而不改写Hash路由。\n- npm test使用node --import tsx，保留原13项断言；原启动器在此环境IPC失败，日志保留。\n\n## 保持\n\nV2 Verdict C、V3原历史、111窗口8胜、固定30/30/30/10、ACWI60%＋H1100640%强基准、V3.1四档费用结论、FREEZE / IMPLEMENTATION BLOCKED、原83与资格29项测试、旧协议与旧数据库全不改写。\n\n## 更正及未推翻\n\n更正旧S08费用来源不充分，改用正式黄金资料概要并限制日期。一级暂停不自动否定独立二级路线，新准入模型单列，不更改旧8项AND分数。新增滞后诊断不替换原V3曲线；没有宣称推翻原历史业绩，也没有更换国债口径。未取得完整真实税后结果，所以没有推翻/证明“全球配置值得实施”。\n\n## 未完成事实\n\n完整ACWI大陆映射、H11006/N11006对账、真实产品序列与历史分红费税、连续同步交易数据、CPI/RF与长期OOS。缺口在网页首屏和正式结果表公开，不藏在脚注。\n'''
 if r.get('evidence_round2'):
  changelog+='\n## 第二轮补证完成\n\n- 修复Net TR断行解析，核验原PDF第68–69页六列，保留11段及标准差列。\n- 稳定来源ID与9次下载回执分离，保留2次失败；元数据生成复用唯一产品补证流程。\n- 510300上市与2024-11-22降费、513500两次费率快照和Net TR人民币口径补齐。\n- 1998年封闭式基金税范围、成文/生效时间和年报URL/正文日期冲突独立登记。\n- 临时目录全量复算不再依赖固定报告路径，逐文件验证；306个冻结数值CSV不变。\n- 新增第二轮测试与独立报告；真实税后资格仍0，定时任务保持暂停。\n'
 (O/'V3.2_CHANGELOG.md').write_text(changelog)
 if r.get('evidence_round2'):
  (O/'V3.2_EVIDENCE_ROUND2.md').write_text('# V3.2 第二轮官方补证\n\n'+round2_summary(r['evidence_round2']))
 print('4 named reports written')
if __name__=='__main__':main()
