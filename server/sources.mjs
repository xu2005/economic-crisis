export const SOURCES = [
 {id:'acwi-nav',instrument:'ACWI',asset:'world-proxy',currency:'USD',url:'https://www.ishares.com/us/products/239600/ishares-msci-acwi-etf',parser:'acwi',kind:'raw-nav-not-total-return'},
 {id:'gold-pcf',instrument:'518880',asset:'gold-candidate',currency:'CNY',url:'https://www.huaan.com.cn/etf/518880/sgshqd.jsp',parser:'pcf',kind:'candidate-pcf-not-frozen-GLD'},
 {id:'gold-nav',instrument:'518880',asset:'gold-candidate',currency:'CNY',url:'https://www.huaan.com.cn/funds/518880/index.shtml',parser:'huaan',kind:'candidate-nav-not-frozen-GLD'},
 {id:'gld-source',instrument:'GLD',asset:'gold',currency:'USD',url:'https://www.spdrgoldshares.com/usa/gld/',parser:'evidence-only',kind:'unvalidated-dynamic-source'},
 {id:'hs300-tr',instrument:'H00300',asset:'hs300-tr',currency:'CNY',url:'https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=H00300',parser:'csi',kind:'index-return-convention-pending'},
 {id:'bond-original',instrument:'H11006',asset:'china-treasury',currency:'CNY',url:'https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=H11006',parser:'csi',kind:'original-index-return-convention-pending'},
 {id:'bond-reinvest-audit',instrument:'N11006',asset:'bond-audit-only',currency:'CNY',url:'https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=N11006',parser:'csi',kind:'separate-reinvestment-audit-not-replacement'},
 {id:'bond-etf',instrument:'511010',asset:'bond-candidate',currency:'CNY',url:'https://e.gtfund.com/etrade/Jijin/view/id/511010',parser:'evidence-only',kind:'five-year-not-all-maturity'},
 {id:'global-active-rejected',instrument:'000041',asset:'world-candidate-rejected',currency:'CNY',url:'https://www.chinaamc.com/fund/000041/index.shtml',parser:'evidence-only',kind:'active-fund-not-ACWI-replication'},
 {id:'hs300-link',instrument:'160706',asset:'hs300-candidate',currency:'CNY',url:'https://www.jsfund.cn/main/a/20250403/483800.shtml',parser:'evidence-only',kind:'candidate-route-unvalidated'},
 {id:'fx-source',instrument:'USD/CNY',asset:'fx-evidence',currency:'CNY',url:'https://www.chinamoney.com.cn/chinese/bkccpr/',parser:'evidence-only',kind:'central-parity-not-retail-fx-execution'},
 {id:'qdii-status',instrument:'QDII',asset:'quota-evidence',currency:null,url:'https://www.safe.gov.cn/safe/2018/0425/16849.html',parser:'evidence-only',kind:'institution-quota-not-fund-availability'},
];
export function sourceUrl(s,now){if(s.parser!=='csi')return s.url;const end=new Date(now);const begin=new Date(end-14*86400000);const date=d=>d.toISOString().slice(0,10).replaceAll('-','');return s.url+'&startDate='+date(begin)+'&endDate='+date(end);}
export function decodeSource(raw,contentType=''){
  const ascii=new TextDecoder().decode(raw.slice(0,2048));
  const label=(contentType.match(/charset\s*=\s*["']?([a-z0-9-]+)/i)||ascii.match(/charset\s*=\s*["']?([a-z0-9-]+)/i))?.[1]?.toLowerCase()||'utf-8';
  const allowed=['utf-8','utf8','gb2312','gbk','gb18030'];if(!allowed.includes(label))throw Error('unregistered source charset');
  return {text:new TextDecoder(label).decode(raw),encoding:label};
}
export function plain(html){return html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,' ').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,' ').replace(/<[^>]*>/g,' ').replace(/&nbsp;|&#160;/g,' ').replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();}
export function closeAt(date,us=false){
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date))throw Error('explicit date required');
  if(!us)return date+'T07:00:00.000Z';
  // Derive the New York UTC offset for this date; covers DST, never a fixed CN/US date join.
  const ref=new Date(date+'T16:00:00Z');const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',hour:'2-digit',hourCycle:'h23'}).formatToParts(ref);const h=Number(parts.find(p=>p.type==='hour').value);return new Date(+ref+(16-h)*3600000).toISOString();
}
export function parseSource(s,body,now){
  const text=plain(body);let data={timestamp:null,nav:null,close:null,fx:null,bid:null,ask:null,premium_discount:null,subscription_status:'UNKNOWN',quota_status:'UNKNOWN',quota:null,minimum_subscription_units:null,totalReturnVerified:false,parserStatus:'EVIDENCE_ONLY'};
  if(s.parser==='acwi'){
    const m=text.match(/NAV as of\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s*(?:\$\s*)+([\d,.]+)/);if(!m)throw Error('ACWI dated NAV unavailable');const date=new Date(m[1]+' 12:00:00 GMT');if(!Number.isFinite(+date))throw Error('invalid date');data.timestamp=closeAt(date.toISOString().slice(0,10),true);data.nav=Number(m[2].replaceAll(',',''));data.parserStatus='RAW_NAV';
  }else if(s.parser==='huaan'){
    const m=text.match(/日期\s*(\d{4}-\d{2}-\d{2})\s*单位净值\s*([\d.]+)/);if(!m)throw Error('dated Huaan NAV unavailable');data.timestamp=closeAt(m[1]);data.nav=Number(m[2]);data.parserStatus='CANDIDATE_NAV';
  }else if(s.parser==='pcf'){
    const dates=[...text.matchAll(/(\d{8})\s*信息内容/g)];const nav=text.match(/基金份额净值\(单位:?元\)\s*[￥¥]?\s*([\d,.]+)/);if(!dates.length||!nav)throw Error('dated PCF NAV unavailable');const d=dates[0][1];data.timestamp=closeAt(d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6));data.nav=Number(nav[1].replaceAll(',',''));
    const min=text.match(/最小申购、赎回单位\(单位:?份\)\s*([\d,.]+)/);data.minimum_subscription_units=min?Number(min[1].replaceAll(',','')):null;
    const quota=text.match(/申购上限\s*([\d,.]+)/);data.quota=quota?Number(quota[1].replaceAll(',','')):null;data.quota_status=data.quota==null?'UNKNOWN':'DISCLOSED_IN_PCF_NOT_ACCOUNT_QUOTA';
    data.subscription_status=/申购和赎回皆允许/.test(text)?'PCF_OPEN_NOT_ACCOUNT_VERIFIED':'UNKNOWN';const pub=text.match(/最新公告日期\s*(\d{8})/);data.status_date=pub?pub[1]:null;data.parserStatus='CANDIDATE_PCF';
  }else if(s.parser==='csi'){
    const json=JSON.parse(body);if(String(json.code)!=='200'||!Array.isArray(json.data))throw Error('CSI schema/status changed');const rows=json.data.filter(v=>v.indexCode===s.instrument&&/^\d{8}$/.test(v.tradeDate)&&Number(v.close)>0).sort((a,b)=>a.tradeDate.localeCompare(b.tradeDate));const v=rows.at(-1);if(!v)throw Error('no explicit index rows');const d=v.tradeDate;data.timestamp=closeAt(d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6));data.close=Number(v.close);data.parserStatus='INDEX_CONVENTION_PENDING';
  }
  if(data.timestamp&&Date.parse(data.timestamp)>Date.parse(now))throw Error('future/unclosed source data');
  return data;
}
