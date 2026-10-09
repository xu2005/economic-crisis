import {SOURCES,sourceUrl,parseSource,decodeSource} from './sources.mjs';
import {sha,canonical,qualify,GATES,infoSet} from './qualification.mjs';
import {append,readAll,verify} from './store.mjs';
import {PROTOCOL,FREEZE} from './protocol.mjs';
const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'}});
async function collect(env,runKey){
  const started=new Date().toISOString();const receipt=[];
  await append(env.DB,{type:'protocol-registration',protocolHash:PROTOCOL.sha256,freezeHash:FREEZE.sha256,observed_at:started},'protocol:'+PROTOCOL.sha256,started);
  const downloads=await Promise.all(SOURCES.map(async s=>{
    const key=runKey+':'+s.id;
    const old=await env.DB.prepare('SELECT hash FROM implementation_events WHERE event_key=?').bind(key).first();if(old)return {old};
    const url=sourceUrl(s,new Date());let raw=null,http=null,error=null,parsed=null,contentType=null;
    try{
      const response=await fetch(url,{headers:{'User-Agent':'CrisisObservatory-ImplementationAudit/3.2','Accept':'text/html,application/json;q=0.9,*/*;q=0.5'},redirect:'manual',signal:AbortSignal.timeout(10000)});http=response.status;contentType=response.headers.get('content-type');raw=new Uint8Array(await response.arrayBuffer());if(raw.byteLength>4*1024*1024){raw=null;throw Error('response too large');}if(!response.ok)throw Error('source HTTP '+response.status);
      const decoded=decodeSource(raw,contentType||'');parsed={...parseSource(s,decoded.text,new Date().toISOString()),source_encoding:decoded.encoding};
    }catch(e){error=String(e.message).slice(0,200);}
    return {url,raw,http,error,parsed,contentType,observedAt:new Date().toISOString()};
  }));
  for(let i=0;i<SOURCES.length;i++){
    const s=SOURCES[i];const download=downloads[i];
    const key=runKey+':'+s.id;
    if(download.old){receipt.push({id:s.id,duplicate:true,hash:download.old.hash});continue;}
    const {url,raw,http,error,parsed,contentType,observedAt}=download;
    // Preserve exact source response bytes, including a returned error page. Timeout has no response SHA.
    let rawHash=null;if(raw){rawHash=await sha(raw);if(!await env.BUCKET.head('v32/raw/'+rawHash))await env.BUCKET.put('v32/raw/'+rawHash,raw,{httpMetadata:{contentType:contentType||'application/octet-stream'}});}
    const payload={type:parsed&&!error?'observation':'acquisition-failure',source_id:s.id,source:url,instrument:s.instrument,asset:s.asset,currency:s.currency,price_kind:s.kind,observed_at:observedAt,known_at:observedAt,sha256:rawHash,http_status:http,error,...(parsed||{timestamp:null,nav:null,close:null,fx:null,bid:null,ask:null,premium_discount:null,subscription_status:'UNKNOWN',quota_status:'UNKNOWN',quota:null,totalReturnVerified:false})};
    const a=await append(env.DB,payload,key,new Date().toISOString());receipt.push({id:s.id,type:payload.type,parserStatus:parsed?.parserStatus||null,hash:a.hash,duplicate:a.duplicate});
  }
  return {runKey,started,completed:new Date().toISOString(),receipt};
}
async function status(env){
  const rows=await readAll(env.DB);const head=await verify(rows);const events=rows.map(r=>({...JSON.parse(r.payload),sequence:r.sequence,hash:r.hash}));const latest={};for(const e of events)if(e.source_id)latest[e.source_id]=e;
  const checks=Object.fromEntries(GATES.map(id=>[id,{status:'UNKNOWN',reason:'尚无完整且合格的实际产品证据；采集响应不等于资格通过'}]));
  const now=new Date();const c=new Date(Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate()));const observations=events.filter(e=>e.type==='observation');const eligible=infoSet(observations,c.toISOString(),FREEZE.registeredAt);
  return {version:PROTOCOL.version,verdict:'BLOCKED',qualification:qualify(checks),freezeHash:FREEZE.sha256,protocolHash:PROTOCOL.sha256,registeredAt:PROTOCOL.registeredAt,head,eventCount:rows.length,observations:observations.length,failures:events.filter(e=>e.type==='acquisition-failure').length,lastRecordedAt:rows.at(-1)?.recorded_at||null,latest:Object.values(latest),infoCutoff:c.toISOString(),eligibleTotalReturn:eligible.length,oos:{baseline:null,nav:null,strongBenchmarkNav:null,reason:'报价口径和完整共同信息集尚未验证；候选原始NAV不能接入冻结全收益曲线'},automaticFeed:'schedule-not-verified-by-this-response',writer:'D1+R2 append-only; owner/service-authorized research data'};
}
export default {async fetch(request,env){
  const u=new URL(request.url);
  if(!u.pathname.startsWith('/api/implementation/'))return env.ASSETS.fetch(request);
  try{
    if(request.method==='GET'&&u.pathname==='/api/implementation/status')return json(await status(env));
    if(request.method==='GET'&&u.pathname==='/api/implementation/events'){
      const rows=await readAll(env.DB);await verify(rows);return new Response(rows.map(r=>canonical({...JSON.parse(r.payload),sequence:r.sequence,hash:r.hash,event_key:r.event_key})).join('\n')+'\n',{headers:{'content-type':'application/x-ndjson','cache-control':'no-store'}});
    }
    if(request.method==='GET'&&u.pathname.startsWith('/api/implementation/raw/')){
      const h=u.pathname.split('/').at(-1);if(!/^[a-f0-9]{64}$/.test(h))return json({error:'invalid hash'},400);const object=await env.BUCKET.get('v32/raw/'+h);return object?new Response(object.body,{headers:{'content-type':'application/octet-stream','content-disposition':'attachment; filename="'+h+'.bin"','content-security-policy':"sandbox; default-src 'none'",'x-content-type-options':'nosniff','cache-control':'no-store'}}):json({error:'evidence not found'},404);
    }
    if(request.method==='POST'&&u.pathname==='/api/implementation/collect'){
      if(request.headers.get('Origin')&&request.headers.get('Origin')!==u.origin)return json({error:'cross-origin write forbidden'},403);
      if(!request.headers.get('content-type')?.startsWith('application/json'))return json({error:'JSON required'},415);
      const owner=env.IMPLEMENTATION_OWNER_EMAIL&&request.headers.get('oai-authenticated-user-email')===env.IMPLEMENTATION_OWNER_EMAIL;
      const serviceToken=request.headers.get('X-Implementation-Collector');
      const service=env.IMPLEMENTATION_SERVICE_TOKEN_SHA256&&serviceToken&&await sha(serviceToken)===env.IMPLEMENTATION_SERVICE_TOKEN_SHA256;
      if(!owner&&!service)return json({error:'owner or configured collector authorization required'},403);
      const b=await request.json();if(typeof b.runKey!=='string'||!/^v32-[a-z0-9:-]{1,100}$/.test(b.runKey))return json({error:'bounded idempotency key required'},400);
      return json(await collect(env,b.runKey));
    }
    return json({error:'endpoint/method not allowed'},405);
  }catch(e){console.error('Implementation register:',e.message);return json({error:'数据采集或账本暂不可用；不据此判为通过',detail:String(e.message).slice(0,180)},503);}
}};
