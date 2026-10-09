"""Run original and new suites; never reuse an old PASS as a new observation."""
from pathlib import Path
import datetime,json,re,subprocess,sys
R=Path(__file__).resolve().parents[1];O=R/'reports/crisis-v32-cny'
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 logs=O/'checks'/stamp;logs.mkdir(parents=True,exist_ok=False)
 suites=[('old_python_crisis',[sys.executable,'-m','unittest','discover','-s','scripts','-p','test_crisis*.py','-v'],48),('old_python_freeze',[sys.executable,'-m','unittest','discover','-s','scripts','-p','test_freeze_v31.py','-v'],22),('old_typescript',['npm','test'],13),('qualification',['node','--test','tests/implementation.test.mjs'],29),('new_cny',[sys.executable,'-m','unittest','discover','-s','scripts','-p','test_cny_implementability.py','-v'],45),('evidence_round2',[sys.executable,'-m','unittest','discover','-s','scripts','-p','test_cny_evidence_round2.py','-v'],32)]
 runs=[]
 for name,cmd,expected in suites:
  p=subprocess.run(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(logs/(name+'.log')).write_text(p.stdout)
  count=re.search(r'Ran (\d+) tests?',p.stdout) if 'unittest' in cmd else re.search(r'\btests (\d+)',p.stdout)
  skipped=re.search(r'\bskipped (\d+)',p.stdout) if 'unittest' not in cmd else re.search(r'skipped=(\d+)',p.stdout)
  n=int(count[1]) if count else 0;skip=int(skipped[1]) if skipped else 0
  runs.append(dict(name=name,command=cmd,count=n,expected=expected,exit_code=p.returncode,skip=skip,log=str((logs/(name+'.log')).relative_to(O))))
  print(json.dumps(runs[-1]),flush=True)
  if p.returncode or n!=expected or skip:raise RuntimeError('suite failed or count/skip changed: '+name)
 cmd=['node','node_modules/typescript/bin/tsc','-b'];p=subprocess.run(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(logs/'typecheck.log').write_text(p.stdout)
 if p.returncode:raise RuntimeError('typecheck failed')
 report=dict(executed_at=now,confirmed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_tests=83,qualification_tests=29,new_tests=45,evidence_round2_tests=32,**{'pass':sum(x['count'] for x in runs),'fail':0,'skip':0},suites=runs,typecheck='PASS',typecheck_log=str((logs/'typecheck.log').relative_to(O)),limitations='Tests and arithmetic do not qualify missing product/tax/access evidence; formal after-tax results remain null',independent_reproduction={'full_repeat_engine':False,'status':'PENDING NEW EXECUTION'})
 (O/'test-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (O/'TEST_REPORT.md').write_text(f"# V3.2 第二轮测试报告\n\n本次实际执行 **{report['pass']} PASS / 0 FAIL / 0 SKIP**，执行UTC：{now}。\n\n原Python70 + TypeScript13 = 原83；资格审计29；第一轮CNY45；第二轮补证32。未引用旧PASS代替本次执行。\n\n"+'\n'.join(f"- {x['name']}：{x['count']}通过；日志`{x['log']}`。" for x in runs)+'\n\n类型检查通过。第二轮覆盖日期费用、同日发布门控、历史费率缺口、NAV不双扣、原件篡改、税主体与发布日期未知、上市前披露、缺年/重年/无效年度、全部11行六列、来源引用与重跑幂等、元数据再生成、临时目录补证、306冻结CSV、网页CSV一致及正式税后空值。\n\n独立账本校验和完整临时目录重算将在下一步执行，结果写入本报告。测试通过不等于IMPLEMENTABLE，真实税后合格组合仍0。旧版报告与首次运行器错误记录保留。\n')
if __name__=='__main__':main()
