import {canonical,sha,validateObservation} from './qualification.mjs';
export async function append(db,payload,key,recordedAt){
  const prior=await db.prepare('SELECT * FROM implementation_events WHERE event_key = ?').bind(key).first();if(prior)return {duplicate:true,event:JSON.parse(prior.payload),hash:prior.hash};
  for(let i=0;i<4;i++){
    const head=await db.prepare('SELECT hash, recorded_at FROM implementation_events ORDER BY sequence DESC LIMIT 1').first();
    if(head&&Date.parse(head.recorded_at)>Date.parse(recordedAt))throw Error('clock moved backwards');
    const p={...payload,recorded_at:recordedAt,previousHash:head?.hash||null};if(p.type==='observation')validateObservation(p,recordedAt);const hash=await sha(canonical(p));
    const result=await db.prepare("INSERT INTO implementation_events(event_key, recorded_at, source_id, payload, hash, previous_hash) SELECT ?,?,?,?,?,? WHERE COALESCE((SELECT hash FROM implementation_events ORDER BY sequence DESC LIMIT 1),'') = ?").bind(key,recordedAt,p.source_id||'protocol',canonical(p),hash,head?.hash||null,head?.hash||'').run();
    if(result.meta?.changes===1)return {duplicate:false,event:p,hash};
    const existing=await db.prepare('SELECT * FROM implementation_events WHERE event_key = ?').bind(key).first();if(existing)return {duplicate:true,event:JSON.parse(existing.payload),hash:existing.hash};
  }throw Error('concurrent append failed; retry with same key');
}
export async function readAll(db){const r=await db.prepare('SELECT sequence,event_key,recorded_at,source_id,payload,hash,previous_hash FROM implementation_events ORDER BY sequence').all();return r.results;}
export async function verify(rows){let prior=null;for(const r of rows){const p=JSON.parse(r.payload);if(r.previous_hash!==prior||p.previousHash!==prior||await sha(canonical(p))!==r.hash)throw Error('ledger hash chain mismatch');prior=r.hash;}return prior;}
