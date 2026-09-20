"""Browser QA using candidate HTML/CSS/JS and Chromium via Playwright.

This intentionally injects API state instead of navigating localhost so it can run in
sandboxes that block browser loopback. API execution is covered separately by pytest.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app import current_state
OUT=ROOT/'evidence'/'qa'; OUT.mkdir(parents=True,exist_ok=True)

def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise SystemExit('Playwright is required for browser QA: pip install playwright') from exc

    html=(ROOT/'web/index.html').read_text(encoding='utf-8')
    css=(ROOT/'web/styles.css').read_text(encoding='utf-8')
    html=html.replace('<link rel="stylesheet" href="/web/styles.css" />',f'<style>{css}</style>').replace('<script type="module" src="/web/app.js"></script>','')
    scheduler=(ROOT/'web/audio-scheduler.js').read_text(encoding='utf-8').replace('export class','class').replace('export function','function')
    app=(ROOT/'web/app.js').read_text(encoding='utf-8').replace("import { TemporalAudioEngine } from '/web/audio-scheduler.js';\n",'')
    candidate_state=current_state()
    expected_lines=len(candidate_state['lines']); expected_events=len(candidate_state['score']['events'])
    state=json.dumps(candidate_state,ensure_ascii=False)
    stub=f"window.fetch=async(url)=>{{if(String(url)==='/api/state')return new Response({json.dumps(state)},{{status:200,headers:{{'Content-Type':'application/json'}}}});throw new Error('QA stub blocks '+url);}};\n"
    combined=stub+scheduler+'\n'+app
    report={'viewports':{},'temporal':{},'interaction':{},'canaries':{}}
    with sync_playwright() as p:
        chromium_path=next((p_ for p_ in ('/opt/pw-browsers/chromium', '/usr/bin/chromium') if Path(p_).exists()), None)
        b=p.chromium.launch(headless=True, executable_path=chromium_path, args=['--no-sandbox','--disable-dev-shm-usage'])
        for width,height,label in [(1440,900,'1440x900'),(1024,768,'1024x768')]:
            pg=b.new_page(viewport={'width':width,'height':height}); pg.set_content(html,wait_until='domcontentloaded'); pg.add_script_tag(content=combined,type='module'); pg.wait_for_function("(n)=>document.querySelectorAll('.event-block').length===n", arg=expected_events, timeout=5000)
            metrics={
                'line_rows':pg.locator('.line-row').count(),
                'event_blocks':pg.locator('.event-block').count(),
                'ready_badge':pg.locator('#readyBadge').inner_text(),
                'page_horizontal_overflow_px':pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth'),
                'timeline_internal_overflow_px':pg.evaluate("document.querySelector('#timelineScroll').scrollWidth-document.querySelector('#timelineScroll').clientWidth"),
            }
            report['viewports'][label]=metrics
            if label=='1440x900':
                pg.locator('.event-block').nth(max(0, expected_events-2)).click(); metrics['selected_event']=pg.locator('#inspectorTitle').inner_text(); pg.screenshot(path=str(OUT/'workbench_1440x900.png'),full_page=True)
                pg.locator('.inspector').evaluate('(el)=>{el.scrollTop=el.scrollHeight}')
                metrics['inspector_controls_clear_of_research']=pg.evaluate("""() => {
                  const controls=document.querySelector('.button-grid').getBoundingClientRect();
                  const research=document.querySelector('.research').getBoundingClientRect();
                  return controls.bottom <= research.top + 1;
                }""")
                # Geometry canary: deliberately create page-level overflow and verify detector catches it.
                pg.evaluate("const x=document.createElement('div');x.id='overflow-canary';x.style.width='5000px';x.style.height='1px';document.body.appendChild(x)")
                report['canaries']['geometry_overflow_detected']=pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')>0
            pg.close()

        async_test = """
        async ({shiftB=350}) => {
          const sr=48000; const ctx=new OfflineAudioContext(1,sr*2,sr);
          const pulse=()=>{const b=ctx.createBuffer(1,Math.floor(sr*.02),sr);b.getChannelData(0).fill(.4);return b;};
          const events=[{event_id:'A',enabled:true,start_ms:100},{event_id:'B',enabled:true,start_ms:shiftB},{event_id:'C',enabled:true,start_ms:shiftB}];
          scheduleBuffers(ctx,events.map(event=>({event,buffer:pulse()})),{baseAudioTime:0,fromMs:0});
          const rendered=await ctx.startRendering(), x=rendered.getChannelData(0), a=Math.round(sr*.1), bc=Math.round(sr*.35);
          return {a:x[a],bc:x[bc],pass:Math.abs(x[a]-.4)<.02 && x[bc]>.75};
        }
        """
        h=b.new_page(); h.set_content('<div></div>'); h.add_script_tag(content=scheduler)
        baseline=h.evaluate(async_test,{'shiftB':350}); canary=h.evaluate(async_test,{'shiftB':370})
        report['temporal']['baseline']=baseline
        report['canaries']['shifted_onset_turns_red']=baseline['pass'] and not canary['pass']
        report['temporal']['shift_canary_observation']=canary
        h.close()

        # Interaction canary: a processing edit must turn processed readiness red immediately,
        # and SAVE REVISION must flush the current score before creating the revision.
        pg=b.new_page(viewport={'width':1440,'height':900})
        pg.set_content(html,wait_until='domcontentloaded')
        interaction_stub=f"""
        window.__qaCalls=[];
        window.__confirmCalls=[];
        window.confirm=(msg)=>{{window.__confirmCalls.push(String(msg));return true;}};
        window.__qaState={state};
        window.fetch=async(url,opts={{}})=>{{
          const path=String(url); const body=opts.body?JSON.parse(opts.body):{{}};
          window.__qaCalls.push(path);
          const response=(payload,status=200)=>new Response(JSON.stringify(payload),{{status,headers:{{'Content-Type':'application/json'}}}});
          if(path==='/api/state') return response(window.__qaState);
          if(path==='/api/score'){{
            window.__qaState=structuredClone(window.__qaState);
            window.__qaState.score=body.score;
            window.__qaState.dirty=true;
            window.__qaState.readiness={{...window.__qaState.readiness,processed_ready:false,state:'READY_DRY_BYPASS'}};
            return response({{ok:true,score:body.score,state:window.__qaState}});
          }}
          if(path==='/api/save-revision'){{
            window.__qaState=structuredClone(window.__qaState);
            window.__qaState.dirty=false;
            window.__qaState.latest_saved_revision={{revision:99,score_hash:'qa',path:'qa'}};
            return response({{ok:true,revision:99,state:window.__qaState}});
          }}
          throw new Error('QA interaction stub blocks '+path);
        }};
        """
        pg.add_script_tag(content=interaction_stub+scheduler+'\n'+app,type='module')
        pg.wait_for_function("(n)=>document.querySelectorAll('.event-block').length===n",arg=expected_events,timeout=5000)
        pg.locator('.event-block').first.click()
        # Invalid numeric edits must be rejected inline and preserve the last valid value.
        start_input=pg.locator('#startInput')
        old_start=start_input.input_value()
        calls_before_invalid=len(pg.evaluate('window.__qaCalls'))
        start_input.fill('-1'); start_input.dispatch_event('change')
        invalid_start={
          'restored':start_input.input_value()==old_start,
          'status':pg.locator('#statusText').inner_text(),
          'score_calls_queued':len(pg.evaluate('window.__qaCalls'))-calls_before_invalid,
        }
        gain=pg.locator('[data-proc="gain_db"]')
        old_gain=gain.input_value()
        calls_before_invalid_gain=len(pg.evaluate('window.__qaCalls'))
        gain.fill('99'); gain.dispatch_event('change')
        invalid_gain={
          'restored':gain.input_value()==old_gain,
          'status':pg.locator('#statusText').inner_text(),
          'score_calls_queued':len(pg.evaluate('window.__qaCalls'))-calls_before_invalid_gain,
        }
        old=float(gain.input_value()); gain.fill(str(old+0.5)); gain.dispatch_event('change')
        immediate={
          'ready_badge':pg.locator('#readyBadge').inner_text(),
          'dirty_text':pg.locator('#dirtyText').inner_text(),
          'export_disabled':pg.locator('#exportBtn').is_disabled(),
          'event_state':pg.locator('#eventState').inner_text(),
        }
        pg.locator('#saveBtn').click()
        pg.wait_for_function("()=>window.__qaCalls.includes('/api/save-revision')",timeout=5000)
        calls=pg.evaluate('window.__qaCalls')
        score_i=max(i for i,x in enumerate(calls) if x=='/api/score')
        save_i=max(i for i,x in enumerate(calls) if x=='/api/save-revision')
        # Duplicate canary: a copied event has no prepared variant, so the UI must
        # invalidate processed readiness synchronously before the debounced write.
        pg.locator('.event-block').first.click()
        duplicate_before={
          'start':pg.locator('#startInput').input_value(),
          'gain':pg.locator('[data-proc="gain_db"]').input_value(),
          'line':pg.locator('#selectedLineId').inner_text(),
          'count':pg.locator('.event-block').count(),
        }
        pg.locator('#duplicateBtn').click()
        duplicate_immediate={
          'ready_badge':pg.locator('#readyBadge').inner_text(),
          'dirty_text':pg.locator('#dirtyText').inner_text(),
          'event_state':pg.locator('#eventState').inner_text(),
          'start_preserved':pg.locator('#startInput').input_value()==duplicate_before['start'],
          'gain_preserved':pg.locator('[data-proc="gain_db"]').input_value()==duplicate_before['gain'],
          'line_preserved':pg.locator('#selectedLineId').inner_text()==duplicate_before['line'],
          'count_incremented':pg.locator('.event-block').count()==duplicate_before['count']+1,
        }
        # Add-event authority: new event begins at 0 ms with DRY/default processing and is enabled.
        add_before=pg.locator('.event-block').count()
        pg.locator('.line-row .add-event').first.click()
        add_immediate={
          'count_incremented':pg.locator('.event-block').count()==add_before+1,
          'start_is_zero':pg.locator('#startInput').input_value()=='0',
          'gain_is_default':float(pg.locator('[data-proc="gain_db"]').input_value())==0.0,
          'enabled':pg.locator('#enabledInput').is_checked(),
          'ready_badge':pg.locator('#readyBadge').inner_text(),
          'event_state':pg.locator('#eventState').inner_text(),
        }
        # Delete authority: if the current score is already dirty, confirm first;
        # the prior saved revision remains visible/recoverable.
        delete_before=pg.locator('.event-block').count()
        pg.locator('#deleteBtn').click()
        delete_immediate={
          'count_decremented':pg.locator('.event-block').count()==delete_before-1,
          'confirm_calls':pg.evaluate('window.__confirmCalls'),
          'revision_text':pg.locator('#revisionText').inner_text(),
          'dirty_text':pg.locator('#dirtyText').inner_text(),
        }
        report['interaction']={'invalid_start_rejected':invalid_start,'invalid_gain_rejected':invalid_gain,'immediate_after_processing_edit':immediate,'api_calls':calls,'flush_before_revision':score_i<save_i,'immediate_after_duplicate':duplicate_immediate,'immediate_after_add':add_immediate,'immediate_after_delete':delete_immediate}
        report['canaries']['invalid_start_preserves_last_valid']=invalid_start['restored'] and invalid_start['score_calls_queued']==0 and 'Previous value kept' in invalid_start['status']
        report['canaries']['invalid_processing_preserves_last_valid']=invalid_gain['restored'] and invalid_gain['score_calls_queued']==0 and 'Previous value kept' in invalid_gain['status']
        report['canaries']['processing_edit_blocks_stale_playback']=immediate['ready_badge']=='BLOCKED' and immediate['export_disabled'] and 'STALE' in immediate['event_state']
        report['canaries']['save_revision_flushes_score_first']=score_i<save_i
        report['canaries']['duplicate_event_preserves_semantics']=duplicate_immediate['start_preserved'] and duplicate_immediate['gain_preserved'] and duplicate_immediate['line_preserved'] and duplicate_immediate['count_incremented']
        report['canaries']['duplicate_event_blocks_stale_playback']=duplicate_immediate['ready_badge']=='BLOCKED' and 'STALE' in duplicate_immediate['event_state']
        report['canaries']['add_event_uses_authority_defaults']=add_immediate['count_incremented'] and add_immediate['start_is_zero'] and add_immediate['gain_is_default'] and add_immediate['enabled'] and add_immediate['ready_badge']=='BLOCKED' and 'STALE' in add_immediate['event_state']
        report['canaries']['delete_dirty_score_confirms_and_keeps_revision']=delete_immediate['count_decremented'] and len(delete_immediate['confirm_calls'])==1 and delete_immediate['revision_text']=='Revision 99' and delete_immediate['dirty_text']=='UNSAVED CURRENT SCORE'
        pg.close(); b.close()
    report['pass']=all(v['page_horizontal_overflow_px']==0 and v['line_rows']==expected_lines and v['event_blocks']==expected_events and v['ready_badge']=='READY · PROCESSED' for v in report['viewports'].values()) and report['viewports']['1440x900'].get('inspector_controls_clear_of_research') is True and report['temporal']['baseline']['pass'] and all(report['canaries'].values())
    (OUT/'browser_qa_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['pass'] else 1)

if __name__=='__main__': main()
