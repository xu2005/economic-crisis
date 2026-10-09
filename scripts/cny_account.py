"""Validated CNY retail accounting; not automatically authorised by a research proxy.
Actual products require separate valid application scopes and account cost evidence.
"""
from dataclasses import dataclass,field
import math
from cny_implementability import Blocked,fee,tax_rule,tax_amount,validate_product_quote,validate_execution,convert_cny
@dataclass
class Account:
 cash:float=100000.
 units:dict=field(default_factory=dict)
 basis:dict=field(default_factory=dict)
 fills:list=field(default_factory=list)
 tax:float=0.
 cost:float=0.
 def execute(self,product,quote,decision_at,execution,rules,tax_category,cost_profile):
  validate_execution(decision_at,execution)
  # Execution snapshot must itself be saved / known by the declared execution record.
  prem=validate_product_quote(quote,product,execution['executed_at'])
  if quote['timestamp']!=execution['executed_at']:raise Blocked('execution evidence is not same timestamp')
  if quote['observed_at']>execution['executed_at']:raise Blocked('later observed quote cannot be synthetic historical execution')
  if not cost_profile.get('verified') or not cost_profile.get('source'):raise Blocked('account fees not validated')
  if any(cost_profile.get(k) is None or cost_profile[k]<0 for k in ['commission_rate','minimum','stamp_rate']):raise Blocked('unknown/negative account fees')
  if tax_category not in product.get('tax_categories_validated',[]):raise Blocked('tax rule not matched to product and income')
  day=execution['executed_at'][:10];rule=tax_rule(rules,tax_category,day,decision_at[:10]);code=product['code'];side=execution['side'];n=execution['units']
  if n<=0 or not math.isfinite(n):raise Blocked('invalid units')
  if n%100 and side=='buy':raise Blocked('secondary ETF purchases must use verified lot size')
  price=quote['ask'] if side=='buy' else quote['bid']
  if execution['price']!=price:raise Blocked('paper execution must match executable ask / bid; real fills require separate broker evidence')
  notional=convert_cny(n*price,quote['fx']);commission=fee(notional,cost_profile['commission_rate'],cost_profile['minimum']);stamp=notional*cost_profile['stamp_rate'] if side=='sell' else 0.;charge=0.
  if side=='buy':
   spent=notional+commission+stamp
   if spent>self.cash+1e-8:raise Blocked('cash overdraft')
   self.cash-=spent;self.units[code]=self.units.get(code,0.)+n;self.basis[code]=self.basis.get(code,0.)+spent;flow=-spent
  elif side=='sell':
   old=self.units.get(code,0.)
   if n>old+1e-10:raise Blocked('short selling prohibited')
   released=self.basis[code]*n/old;gain=notional-commission-stamp-released;charge=tax_amount(rule,gain)
   self.units[code]-=n;self.basis[code]-=released;flow=notional-commission-stamp-charge;self.cash+=flow
  else:raise Blocked('invalid side')
  self.tax+=charge;self.cost+=commission+stamp
  fill=dict(code=code,side=side,units=n if side=='buy' else -n,executed_at=execution['executed_at'],decision_at=decision_at,price=price,fx=quote['fx'],premium=prem,commission=commission,stamp_tax=stamp,income_tax=charge,cash_flow=flow,cash_after=self.cash,source_sha256=quote['sha256'],tax_source=rule['source_id'])
  self.fills.append(fill);return fill
 def distribution(self,code,per_unit,rules,date,tax_category,adjusted_nav=False,application_verified=False):
  if adjusted_nav:raise Blocked('adjusted NAV already includes distributions; no second dividend')
  if not application_verified:raise Blocked('distribution tax application not verified')
  if per_unit<0:raise Blocked('negative dividend')
  rule=tax_rule(rules,tax_category,date)
  if rule.get('tiers'):raise Blocked('direct A-share deferred dividend requires lot / disposal liability ledger')
  gross=self.units.get(code,0.)*per_unit;tax=tax_amount(rule,gross);self.cash+=gross-tax;self.tax+=tax;return gross-tax
 def wealth(self,prices):
  if any(k not in prices or prices[k] is None for k,n in self.units.items() if n):raise Blocked('missing asset mark')
  return self.cash+sum(n*prices[k] for k,n in self.units.items() if n)

def four_return_levels(start_cny,gross_end_cny,product_end_cny,investor_end_pre_tax_cny,tax_cny,validated=False):
 """Do not fill unavailable gross returns from fund NAV or index backfills."""
 from cny_implementability import aftertax_return
 def ret(x):return None if x is None else x/start_cny-1
 if start_cny<=0:raise Blocked('positive CNY capital required')
 return dict(gross_asset_return=ret(gross_end_cny),fund_product_return=ret(product_end_cny),investor_pre_tax_return=ret(investor_end_pre_tax_cny),investor_after_tax_cny_return=aftertax_return(start_cny,investor_end_pre_tax_cny,tax_cny) if validated and investor_end_pre_tax_cny is not None and tax_cny is not None else None)

def real_cagr(nominal_cagr,cpi_start,cpi_end,years):
 if cpi_start is None or cpi_end is None or cpi_start<=0 or cpi_end<=0 or years<=0:raise Blocked('verified CPI endpoints and positive period required')
 return (1+nominal_cagr)/(cpi_end/cpi_start)**(1/years)-1
