import { TemporalAudioEngine } from '/web/audio-scheduler.js';

const $ = (s) => document.querySelector(s);
const engine = new TemporalAudioEngine();
let state = null;
let selectedEventId = null;
let pixelsPerSecond = 70;
let running = false;
let saveTimer = null;
let flushPromise = null;
let pendingScoreMessage = null;
let localMutationSeq = 0;

function fmtTime(ms){
  ms = Math.max(0, Math.round(ms));
  const m = Math.floor(ms/60000);
  const s = Math.floor((ms%60000)/1000);
  const x = ms%1000;
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${String(x).padStart(3,'0')}`;
}
function setStatus(msg, bad=false){ const el=$('#statusText'); el.textContent=msg||''; el.style.color=bad?'#efaaa2':''; }
async function api(path, body=null){
  const opts = body===null ? {cache:'no-store'} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
  const res = await fetch(path, opts);
  const data = await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(data.error || `${res.status} ${res.statusText}`);
  return data;
}
async function refresh(){
  state = await api('/api/state');
  renderAll();
}
function lineById(id){ return state.lines.find(x=>x.line_id===id); }
function eventById(id){ return state.score.events.find(x=>x.event_id===id); }
function eventDuration(e){
  const src = $('#dryBypass').checked ? e.asset : e.variant;
  return Number(src?.duration_ms || e.asset?.duration_ms || 1200);
}
function audioUrlForEvent(e){
  const meta = $('#dryBypass').checked ? e.asset : e.variant;
  return meta?.wav_path ? `/files/${meta.wav_path}` : null;
}
function renderAll(){
  if(!state) return;
  $('#scoreName').textContent = state.score.name;
  $('#appVersion').textContent = `v${state.app_version}`;
  const sourceNotice=state.source.ui_notice || state.source.warning || '';
  $('#sourceWarning').hidden = !sourceNotice;
  $('#sourceWarning').textContent = sourceNotice;
  const modeDry=$('#dryBypass').checked;
  const ready=modeDry?state.readiness.dry_ready:state.readiness.processed_ready;
  const badge=$('#readyBadge');
  badge.className='state-badge '+(running?'playing':ready?(modeDry?'dry':'ready'):'blocked');
  badge.textContent=running?'PLAYING':ready?(modeDry?'READY · DRY':'READY · PROCESSED'):'BLOCKED';
  $('#playBtn').disabled=!ready || running;
  $('#playSelectionBtn').disabled=!ready || running || !selectedEventId;
  $('#stopBtn').disabled=!running;
  $('#exportBtn').disabled=state.dirty;
  const rev=state.latest_saved_revision?.revision ?? state.score.revision ?? 0;
  $('#revisionText').textContent=`Revision ${rev}`;
  $('#dirtyText').textContent=state.dirty?'UNSAVED CURRENT SCORE':'SAVED';
  $('#dirtyText').className='dirty'+(state.dirty?'':' saved');
  renderLines(); renderTimeline(); renderInspector();
}
function renderLines(){
  const root=$('#lineList'); root.replaceChildren();
  for(const line of state.lines){
    const row=document.createElement('article'); row.className='line-row';
    const assetStatus=(line.asset?.status||'MISSING').toLowerCase();
    row.innerHTML=`<div class="line-meta"><span class="line-id">${line.line_id}</span><span class="asset-state ${assetStatus}">${line.asset?.status||'MISSING'}${line.asset?.duration_ms?` · ${(line.asset.duration_ms/1000).toFixed(2)}s`:''}</span></div><p class="line-text" dir="rtl" lang="fa"></p><div class="line-actions"><button class="btn mini dry-audition">DRY</button><button class="btn mini add-event">ADD EVENT</button></div>`;
    row.querySelector('.line-text').textContent=line.text_fa;
    row.querySelector('.dry-audition').disabled=line.asset?.status!=='READY';
    row.querySelector('.dry-audition').addEventListener('click',async()=>{
      try{ setStatus(`Auditioning ${line.line_id} dry…`); await engine.audition(`/files/${line.asset.wav_path}`); }
      catch(e){setStatus(e.message,true)}
    });
    row.querySelector('.add-event').addEventListener('click',()=>addEvent(line.line_id));
    root.append(row);
  }
}
function layoutEvents(events){
  const sorted=[...events].sort((a,b)=>a.start_ms-b.start_ms || a.event_id.localeCompare(b.event_id));
  const laneEnds=[]; const layout=[];
  for(const e of sorted){
    const end=e.start_ms+Math.max(1000,eventDuration(e));
    let lane=laneEnds.findIndex(x=>x<=e.start_ms);
    if(lane<0){lane=laneEnds.length;laneEnds.push(end)} else laneEnds[lane]=end;
    layout.push({e,lane,end});
  }
  return {layout, lanes:Math.max(1,laneEnds.length)};
}
function renderTimeline(){
  const timeline=$('#timeline');
  [...timeline.querySelectorAll('.event-block,.lane-line')].forEach(x=>x.remove());
  const enabled=state.score.events;
  const {layout,lanes}=layoutEvents(enabled);
  const maxMs=Math.max(90000,...layout.map(x=>x.end+3000));
  const width=Math.ceil(maxMs/1000*pixelsPerSecond);
  const content=$('#timelineContent'); content.style.width=`${width}px`;
  timeline.style.width='100%'; timeline.style.height=`${Math.max(360,lanes*76+34)}px`; timeline.style.backgroundSize=`${pixelsPerSecond}px 100%`;
  const ruler=$('#ruler'); ruler.replaceChildren(); ruler.style.width='100%';
  for(let sec=0;sec<=maxMs/1000;sec+=5){
    const m=document.createElement('span'); m.className='ruler-mark'; m.style.left=`${sec*pixelsPerSecond}px`; m.textContent=fmtTime(sec*1000); ruler.append(m);
  }
  for(const {e,lane} of layout){
    const b=document.createElement('button'); b.type='button';
    const stale=e.variant?.status!=='READY';
    b.className=`event-block${e.event_id===selectedEventId?' selected':''}${e.enabled?'':' disabled'}${stale?' stale':''}`;
    b.style.left=`${e.start_ms/1000*pixelsPerSecond}px`; b.style.top=`${18+lane*76}px`; b.style.width=`${Math.max(82,eventDuration(e)/1000*pixelsPerSecond)}px`;
    b.dataset.eventId=e.event_id;
    b.innerHTML=`<div class="eid">${e.event_id} · ${e.line_id} · ${fmtTime(e.start_ms)}</div><div class="preview" dir="rtl"></div>`;
    b.querySelector('.preview').textContent=e.line_text_fa;
    b.addEventListener('click',()=>{selectedEventId=e.event_id;renderAll()});
    timeline.append(b);
  }
  updatePlayhead(0,false);
}
function renderInspector(){
  const e=selectedEventId?eventById(selectedEventId):null;
  $('#inspectorEmpty').hidden=!!e; $('#inspectorForm').hidden=!e;
  if(!e){$('#inspectorTitle').textContent='No selection';return}
  $('#inspectorTitle').textContent=e.event_id;
  $('#selectedLineId').textContent=e.line_id;
  $('#selectedText').textContent=e.line_text_fa;
  $('#enabledInput').checked=e.enabled;
  $('#startInput').value=e.start_ms;
  document.querySelectorAll('[data-proc]').forEach(input=>{input.value=e.processing[input.dataset.proc]});
  $('#pitchOut').textContent=`${Number(e.processing.pitch_semitones).toFixed(1)} st`;
  $('#durationReadout').textContent=`dry ${e.asset?.duration_ms??'—'} ms · processed ${e.variant?.duration_ms??'—'} ms`;
  $('#eventState').textContent=`dry=${e.asset?.status||'MISSING'} · variant=${e.variant?.status||'MISSING'} · route=${e.route_id}`;
}
function markLocalProcessedStale(reason='Local processing changed; prepare again.'){
  const ev=selectedEventId?eventById(selectedEventId):null;
  if(ev) ev.variant={...(ev.variant||{}),status:'STALE',reason};
  state.readiness={...state.readiness,processed_ready:false,state:state.readiness.dry_ready?'READY_DRY_BYPASS':'BLOCKED'};
}
function queueScorePersist(message='Score updated'){
  localMutationSeq++;
  state.dirty=true;
  clearTimeout(saveTimer);
  pendingScoreMessage=message;
  saveTimer=setTimeout(()=>{ void flushScore(); },120);
}
async function flushScore(message=null){
  clearTimeout(saveTimer); saveTimer=null;
  if(message) pendingScoreMessage=message;
  if(flushPromise) return flushPromise;
  flushPromise=(async()=>{
    let lastResponse=null;
    while(true){
      const seq=localMutationSeq;
      const snapshot=JSON.parse(JSON.stringify(state.score));
      lastResponse=await api('/api/score',{score:snapshot});
      if(seq===localMutationSeq){
        state=lastResponse.state;
        const msg=pendingScoreMessage;
        pendingScoreMessage=null;
        if(msg) setStatus(msg);
        renderAll();
        return lastResponse;
      }
      // Another edit landed while this request was in flight. Do not let the
      // older response overwrite it; loop and persist the newest client score.
    }
  })();
  try{return await flushPromise;}
  catch(e){setStatus(e.message,true);throw e}
  finally{flushPromise=null}
}
function nextEventId(){
  const nums=state.score.events.map(e=>Number(e.event_id.replace(/\D/g,''))||0); return `EV-${String(Math.max(0,...nums)+1).padStart(3,'0')}`;
}
function addEvent(lineId){
  const line=lineById(lineId);
  const event={event_id:nextEventId(),line_id:lineId,start_ms:0,enabled:true,route_id:'STEREO_MAIN',processing:{gain_db:0,pan:0,pitch_semitones:0,reverb_mix:0,delay_ms:0,delay_feedback:0,attack_ms:0,release_ms:0},line_text_fa:line?.text_fa||'',asset:line?.asset||{status:'MISSING'}};
  state.score.events.push(event); selectedEventId=event.event_id; markLocalProcessedStale('New event needs a prepared variant.'); queueScorePersist('Event added'); renderAll();
}
async function play(fromSelection=false){
  const dry=$('#dryBypass').checked; const ready=dry?state.readiness.dry_ready:state.readiness.processed_ready;
  if(!ready){setStatus(dry?'Dry assets are not ready.':'Processed variants are not ready.',true);return}
  const selected=selectedEventId?eventById(selectedEventId):null; const fromMs=fromSelection&&selected?selected.start_ms:0;
  const events=state.score.events.map(e=>({...e,audio_url:audioUrlForEvent(e)}));
  try{
    running=true;renderAll(); setStatus(`${dry?'Dry':'Processed'} run scheduled from ${fmtTime(fromMs)}.`);
    await engine.schedule(events,{fromMs,onTick:(ms)=>updatePlayhead(ms,true),onDone:()=>{running=false;updatePlayhead(0,false);renderAll();setStatus('Run complete.')}});
  }catch(e){running=false;renderAll();setStatus(e.message,true)}
}
function updatePlayhead(ms,show){
  const ph=$('#playhead'); ph.hidden=!show; ph.style.left=`${ms/1000*pixelsPerSecond}px`; $('#elapsed').textContent=fmtTime(show?ms:0);
}
function stop(){engine.stop();running=false;updatePlayhead(0,false);renderAll();setStatus('Stopped and reset.')}

$('#renderDryBtn').addEventListener('click',async()=>{
  const mode=state.tts?.recommended_render_mode || 'piper';
  try{setStatus(`Rendering dry audio (${mode})…`);const r=await api('/api/render-dry',{mode});state=r.state;renderAll();setStatus('Dry assets ready.');}
  catch(e){setStatus(e.message,true)}
});
$('#prepareBtn').addEventListener('click',async()=>{try{setStatus('Preparing processed variants…');await flushScore();const r=await api('/api/prepare',{});state=r.state;renderAll();setStatus('Processed score ready.')}catch(e){setStatus(e.message,true)}});
$('#playBtn').addEventListener('click',()=>play(false)); $('#playSelectionBtn').addEventListener('click',()=>play(true)); $('#stopBtn').addEventListener('click',stop);
$('#dryBypass').addEventListener('change',renderAll); $('#reloadBtn').addEventListener('click',refresh);
$('#zoom').addEventListener('input',e=>{pixelsPerSecond=Number(e.target.value);renderTimeline()});
$('#enabledInput').addEventListener('change',e=>{const ev=eventById(selectedEventId);ev.enabled=e.target.checked;if(ev.enabled&&ev.variant?.status!=='READY')markLocalProcessedStale('Enabled event needs a prepared variant.');queueScorePersist('Event enabled state updated');renderAll()});
$('#startInput').addEventListener('change',e=>{
  const ev=eventById(selectedEventId); const raw=Number(e.target.value);
  if(!Number.isFinite(raw) || !Number.isInteger(raw) || raw<0){
    e.target.value=ev.start_ms;
    setStatus('Start time must be a whole number of milliseconds ≥ 0. Previous value kept.',true);
    return;
  }
  ev.start_ms=raw; queueScorePersist('Start time updated; audio variant remains reusable.'); renderAll();
});
document.querySelectorAll('[data-proc]').forEach(input=>input.addEventListener('change',e=>{
  const ev=eventById(selectedEventId); const k=e.target.dataset.proc; const raw=Number(e.target.value);
  const min=e.target.min===''?-Infinity:Number(e.target.min); const max=e.target.max===''?Infinity:Number(e.target.max);
  const integer=['delay_ms','attack_ms','release_ms'].includes(k);
  if(!Number.isFinite(raw) || raw<min || raw>max || (integer&&!Number.isInteger(raw))){
    e.target.value=ev.processing[k];
    setStatus(`${k} must be ${integer?'a whole number ':''}between ${min} and ${max}. Previous value kept.`,true);
    return;
  }
  ev.processing[k]=raw; markLocalProcessedStale(`${k} changed locally; prepare this variant again.`); queueScorePersist(`${k} updated; event variant is now stale.`); renderAll();
}));
$('#auditionEventBtn').addEventListener('click',async()=>{
  let ev=eventById(selectedEventId);try{await flushScore();ev=eventById(selectedEventId);if(ev.variant?.status!=='READY'){setStatus(`Preparing ${ev.event_id}…`);const r=await api('/api/prepare',{event_ids:[ev.event_id]});state=r.state;renderAll();ev=eventById(selectedEventId)}await engine.audition(`/files/${ev.variant.wav_path}`);setStatus(`Auditioning ${ev.event_id}.`)}catch(e){setStatus(e.message,true)}
});
$('#duplicateBtn').addEventListener('click',()=>{const src=eventById(selectedEventId);const dup=JSON.parse(JSON.stringify(src));delete dup.variant;dup.event_id=nextEventId();state.score.events.push(dup);selectedEventId=dup.event_id;markLocalProcessedStale('Duplicated event needs a prepared variant.');queueScorePersist('Event duplicated; processed variant is stale.');renderAll()});
$('#deleteBtn').addEventListener('click',()=>{
  const ev=eventById(selectedEventId); if(!ev) return;
  if(state.dirty && !window.confirm(`Delete ${ev.event_id}? The current score has unsaved edits. The last saved revision remains recoverable.`)) return;
  state.score.events=state.score.events.filter(e=>e.event_id!==selectedEventId); selectedEventId=null;
  queueScorePersist('Event deleted from current score; saved revisions remain intact.'); renderAll();
});
$('#saveBtn').addEventListener('click',async()=>{try{await flushScore();const r=await api('/api/save-revision',{});state=r.state;renderAll();setStatus(`Saved revision ${r.revision}.`)}catch(e){setStatus(e.message,true)}});
$('#noteBtn').addEventListener('click',async()=>{try{await api('/api/note',{disposition:$('#disposition').value,note:$('#noteInput').value,mode:$('#dryBypass').checked?'dry':'processed'});$('#noteInput').value='';setStatus('Research note recorded.')}catch(e){setStatus(e.message,true)}});
$('#exportBtn').addEventListener('click',async()=>{try{await flushScore();setStatus('Exporting audible run + provenance sidecar…');const r=await api('/api/export',{mode:$('#dryBypass').checked?'dry':'processed'});$('#exportResult').textContent=r.wav;setStatus(`Exported ${r.wav}`)}catch(e){setStatus(e.message,true)}});
window.addEventListener('keydown',e=>{if(e.code==='Space'&&!['INPUT','TEXTAREA','SELECT','BUTTON'].includes(document.activeElement.tagName)){e.preventDefault();running?stop():play(false)}});

refresh().catch(e=>setStatus(e.message,true));
