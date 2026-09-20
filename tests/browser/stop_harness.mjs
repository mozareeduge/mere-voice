import { TemporalAudioEngine, computeRelativeSchedule } from '../../web/audio-scheduler.js';
const calls=[];
const fake=()=>({stop(){calls.push('stop')},disconnect(){calls.push('disconnect')}});
const e=new TemporalAudioEngine();
e.active=[fake(),fake(),fake()]; e.runToken=4; e.stop();
if(e.active.length!==0 || e.runToken!==5 || calls.filter(x=>x==='stop').length!==3 || calls.filter(x=>x==='disconnect').length!==3){
  console.error('FAIL stop cleanup', {active:e.active.length,runToken:e.runToken,calls}); process.exit(1);
}
const rel=computeRelativeSchedule([{event_id:'A',enabled:true,start_ms:500},{event_id:'B',enabled:true,start_ms:900},{event_id:'C',enabled:true,start_ms:200},{event_id:'D',enabled:false,start_ms:700}],500);
if(JSON.stringify(rel)!==JSON.stringify([{event_id:'A',relative_ms:0},{event_id:'B',relative_ms:400}])){
  console.error('FAIL selection schedule',rel); process.exit(1);
}
console.log('PASS stop cleanup + play-from-selection deltas');
