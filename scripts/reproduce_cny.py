"""python scripts/reproduce_cny.py [--full]; never overwrites historical archives."""
from pathlib import Path
import argparse,json,hashlib,sys,tempfile,shutil
import pandas as pd
import cny_implementability as study
R=Path(__file__).resolve().parents[1];O=R/'reports/crisis-v32-cny'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args()
 manifest=json.loads((O/'manifest.json').read_text())
 for name,expected in manifest['files'].items():
  p=R/name
  if hashlib.sha256(p.read_bytes()).hexdigest()!=expected['sha256']:raise ValueError('hash mismatch: '+name)
 p,o,_,_=study.historical_panel();results=json.loads((O/'results.json').read_text())
 # Independent ledger / curve arithmetic for ALL 96 outputs.
 for row in results['proxy_summary']:
  key=f"{row['id']}-{row['scenario']}-{row['mode']}";c=pd.read_csv(O/'curves'/f'{key}.csv');f=pd.read_csv(O/'ledgers'/f'{key}.csv')
  delta=(c.equity-c.cash-c[[k for k in c if k.startswith('value_')]].sum(axis=1)).abs().max()
  if delta>1e-6:raise ValueError('wealth conservation: '+key)
  if len(f) and not (f.signal_at<f.date).all():raise ValueError('future signal: '+key)
  cash=100000+c.external_flow.cumsum()+c.date.map(f.groupby('date').cash_flow.sum()).fillna(0).cumsum()
  if (cash-c.cash).abs().max()>1e-6:raise ValueError('cash conservation: '+key)
  liquidation=pd.read_csv(O/'liquidations'/f'{key}.csv')
  if abs(c.cash.iloc[-1]+liquidation.net_proceeds.sum()-row['terminal_proxy_liquidated_cny'])>1e-6:raise ValueError('terminal liquidation: '+key)
  years=(pd.Timestamp(c.date.iloc[-1])-pd.Timestamp(c.date.iloc[0])).days/365.25
  cg=(c.nav.iloc[-1]/c.nav.iloc[0])**(1/years)-1;dd=(1-c.nav/c.nav.cummax()).max()
  if abs(cg-row['proxy_cagr'])>1e-10 or abs(dd-row['proxy_mdd'])>1e-10:raise ValueError('independent CAGR/MDD: '+key)
  for keyfield,ledgerfield,termfield in [('cumulative_transaction_cost','commission','commission'),('cumulative_synthetic_tax','synthetic_tax','synthetic_tax'),('fx_friction','fx_friction','fx_friction')]:
   if abs(f[ledgerfield].sum()+liquidation[termfield].sum()-row[keyfield])>1e-6:raise ValueError('cost ledger sum: '+keyfield)
 if args.full:
  with tempfile.TemporaryDirectory() as d:
   study.O=Path(d);sub=study.O/'archive/qualification-2026-10-08';sub.mkdir(parents=True);shutil.copy2(O/'archive/qualification-2026-10-08/archive-receipt.json',sub/'archive-receipt.json');study.main()
   if (study.O/'results.json').read_bytes()!=(O/'results.json').read_bytes():raise ValueError('full replay mismatch')
   for replayed in study.O.rglob('*'):
    if replayed.is_file():
     saved=O/replayed.relative_to(study.O)
     if not saved.exists() or replayed.read_bytes()!=saved.read_bytes():raise ValueError('full generated file mismatch: '+str(replayed.relative_to(study.O)))
 print(json.dumps({'hashes_verified':len(manifest['files']),'all_proxy_ledgers':96,'full_replay':args.full,'formal_aftertax_valid':0}))
if __name__=='__main__':main()
