"""Independent Tax Model API; one canonical dated rule implementation, no duplicated rates."""
from dataclasses import dataclass
from cny_implementability import tax_rule,tax_amount,dividend_rate,Blocked
@dataclass(frozen=True)
class TaxModel:
 rules:list
 def resolve(self,category,event_date,knowledge_date=None):return tax_rule(self.rules,category,event_date,knowledge_date)
 def calculate(self,category,income_cny,event_date,knowledge_date=None,acquired=None,assessed_at=None,foreign_paid_cny=0.,credit_eligible=False):
  rule=self.resolve(category,event_date,knowledge_date)
  if rule.get('tiers'):
   if acquired is None or assessed_at is None:raise Blocked('lot acquisition and deferred-tax assessment required')
   rule={**rule,'rate':dividend_rate(rule,acquired,assessed_at)}
  return tax_amount(rule,income_cny,foreign_paid_cny,credit_eligible)
