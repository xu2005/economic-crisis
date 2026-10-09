export const GATES = ['mapping','primary-access','premium-spread','fx','costs','tax','continuity','chronology'];
export function canonical(v) {
  if (v === null || typeof v !== 'object') { if (typeof v === 'number' && !Number.isFinite(v)) throw Error('nonfinite'); return JSON.stringify(v); }
  if (Array.isArray(v)) return '['+v.map(canonical).join(',')+']';
  return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
}
export async function sha(bytes) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256',typeof bytes==='string'?new TextEncoder().encode(bytes):bytes))].map(v=>v.toString(16).padStart(2,'0')).join(''); }
export function time(s) { if(typeof s!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(s)||!Number.isFinite(Date.parse(s))) throw Error('aware timestamp required'); return Date.parse(s); }
export function qualify(checks) {
  if (Object.keys(checks).some(k=>!GATES.includes(k))) throw Error('unknown gate');
  const rows=GATES.map(id=>({id,status:checks[id]?.status==='PASS'&&checks[id]?.evidenceSha256?.match(/^[a-f0-9]{64}$/)&&checks[id]?.source?.startsWith('https://')?'PASS':checks[id]?.status==='FAIL'?'FAIL':'UNKNOWN',reason:checks[id]?.reason||'缺少可核验证据'}));
  const pass=rows.filter(r=>r.status==='PASS').length;
  return {verdict:pass===8?'IMPLEMENTABLE':'BLOCKED',score:100*pass/8,passed:pass,total:8,rows};
}
export function evaluateFacts(f,p,cutoff) {
  const l=p.limits; const missing=(...keys)=>keys.some(k=>f[k]===null||f[k]===undefined);
  const nonnegative=(...values)=>values.every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0);
  const bool=(test,absent)=>absent?'UNKNOWN':test?'PASS':'FAIL';
  const s={mapping:bool(f.passive===true&&f.referenceEquivalent===true&&f.returnConventionVerified===true&&(!f.bond||Math.abs(f.duration-f.targetDuration)<=l.maxBondDurationGapYears),missing('passive','referenceEquivalent','returnConventionVerified')||(f.bond&&missing('duration','targetDuration'))),
    'primary-access':bool(f.subscriptionOpen===true&&nonnegative(f.minimumSubscriptionCny,f.budgetCny,f.quotaCny)&&f.budgetCny>0&&f.minimumSubscriptionCny<=f.budgetCny&&f.quotaCny>=f.budgetCny&&f.legalChannel===true,missing('subscriptionOpen','minimumSubscriptionCny','budgetCny','quotaCny','legalChannel')),
    'premium-spread':bool(f.sameTimeFairValue===true&&Number.isFinite(f.premium)&&nonnegative(f.spread,f.quoteAgeSeconds)&&Math.abs(f.premium)<=l.maxAbsPremium&&f.spread<=l.maxSpread&&f.quoteAgeSeconds<=l.maxQuoteAgeSeconds,missing('sameTimeFairValue','premium','spread','quoteAgeSeconds')),
    fx:bool(f.fxChannelVerified===true&&f.fxCostKnown===true,missing('fxChannelVerified','fxCostKnown')),
    costs:bool(f.costInventoryComplete===true&&nonnegative(f.oneWayCost,f.annualExpense)&&f.oneWayCost<=l.maxTradingCostOneWay&&f.annualExpense<=l.maxAnnualKnownExpense&&f.noDoubleCounting===true,missing('costInventoryComplete','oneWayCost','annualExpense','noDoubleCounting')),
    tax:bool(f.taxInventoryComplete===true&&f.taxApplicableVerified===true,missing('taxInventoryComplete','taxApplicableVerified')),
    continuity:bool(nonnegative(f.sessions,f.completeness)&&f.completeness<=1&&f.sessions>=l.minContinuitySessions&&f.completeness>=l.requiredCompleteness&&f.rawEvidenceComplete===true,missing('sessions','completeness','rawEvidenceComplete')),
    chronology:missing('closed','marketAt','knownAt','observedAt','recordedAt')?'UNKNOWN':bool(f.closed===true&&time(f.marketAt)<=time(f.knownAt)&&time(f.knownAt)<=time(f.observedAt)&&time(f.observedAt)<=time(f.recordedAt)&&time(f.recordedAt)<=time(cutoff),false)};
  return qualify(Object.fromEntries(GATES.map(id=>[id,{status:s[id],reason:s[id]==='PASS'?'预注册要求满足':s[id]==='FAIL'?'未满足预注册要求':'证据不完整',source:f.evidence?.[id]?.source,evidenceSha256:f.evidence?.[id]?.sha256}])));
}
export function validateObservation(o, now) {
  if (!o.source?.startsWith('https://')||!o.sha256?.match(/^[a-f0-9]{64}$/)) throw Error('provenance required');
  if(time(o.observed_at)>time(now)||time(o.observed_at)>time(o.recorded_at)||time(o.recorded_at)>time(now)) throw Error('future/backdated observation');
  for(const field of ['nav','close','fx','bid','ask']) if(o[field]!=null&&(!Number.isFinite(o[field])||o[field]<=0))throw Error('invalid value');
  if(o.bid!=null&&o.ask!=null&&o.bid>o.ask)throw Error('crossed market');
  if(o.premium_discount!=null&&!Number.isFinite(o.premium_discount))throw Error('invalid premium');
  if(o.timestamp!=null&&time(o.timestamp)>time(o.observed_at))throw Error('unclosed/future valuation');
  if(o.known_at!=null&&time(o.known_at)>time(o.observed_at))throw Error('future knowledge');
  return o;
}
export function infoSet(rows,cutoff,registeredAt) {
  const c=time(cutoff); if(new Date(c).getUTCHours()!==0||new Date(c).getUTCMinutes()!==0||new Date(c).getUTCSeconds()!==0||new Date(c).getUTCMilliseconds()!==0)throw Error('08:00 Shanghai required');
  return rows.filter(o=>o.timestamp&&time(o.timestamp)>=time(registeredAt)&&time(o.timestamp)<=c&&time(o.observed_at)<=c&&time(o.recorded_at)<=c&&o.known_at&&time(o.known_at)<=c&&o.totalReturnVerified===true);
}
export function matchedPremium(price,nav,priceAt,navAt,fxVerified) {
  if(!fxVerified||priceAt!==navAt||!(price>0&&nav>0))return null;
  return price/nav-1;
}
export function qualifyPortfolio(assetChecks,weights){
  const assets=Object.keys(weights).filter(a=>weights[a]>0);
  if(assets.some(a=>!assetChecks[a]))return {verdict:'BLOCKED',score:0,passed:0,total:8,missingAssets:assets.filter(a=>!assetChecks[a]),rows:GATES.map(id=>({id,status:'UNKNOWN',reason:'组合含未验证资产'}))};
  const rows=GATES.map(id=>{const rs=assets.map(a=>qualify(assetChecks[a]).rows.find(r=>r.id===id));return {id,status:rs.every(r=>r.status==='PASS')?'PASS':rs.some(r=>r.status==='FAIL')?'FAIL':'UNKNOWN',reason:assets.filter((a,i)=>rs[i].status!=='PASS').join(' / ')||'所有资产证据齐全'};});
  const passed=rows.filter(r=>r.status==='PASS').length;return {verdict:passed===8?'IMPLEMENTABLE':'BLOCKED',score:passed*100/8,passed,total:8,rows};
}
