# 04 — Consequential Copy Deck

Shell copy is English-first; canonical Voice text remains Persian and is never translated by the tool.

| ID | State | Exact/template copy |
|---|---|---|
| COPY-001 | processed ready | `READY — processed run is prepared.` |
| COPY-002 | dry ready only | `DRY READY — processed events still need preparation.` |
| COPY-003 | missing dry | `NOT READY — {count} Voice asset(s) need rendering.` |
| COPY-004 | stale source | `This line changed after its current audio was rendered.` |
| COPY-005 | stale processing | `Processing changed — prepare this event before processed playback.` |
| COPY-006 | render action | `RENDER DRY` |
| COPY-007 | prepare action | `PREPARE SCORE` |
| COPY-008 | play | `PLAY FULL` |
| COPY-009 | rehearsal play | `PLAY FROM SELECTION` |
| COPY-010 | rehearsal badge | `REHEARSAL START — earlier events are not reconstructed.` |
| COPY-011 | stop | `STOP / RESET` |
| COPY-012 | bypass | `DRY BYPASS — timing preserved; processing disabled.` |
| COPY-013 | invalid onset | `Start time must be 0 ms or later.` |
| COPY-014 | invalid field | `{field} must be between {min} and {max}.` |
| COPY-015 | missing dry ref | `Event {event_id} cannot run: dry audio for {line_id} is not ready.` |
| COPY-016 | missing variant | `Event {event_id} needs preparation before processed playback.` |
| COPY-017 | render failure | `Could not render {line_id}. Existing successful assets were kept.` |
| COPY-018 | processing failure | `Could not prepare {event_id}. Its dry source was kept.` |
| COPY-019 | runtime failure | `RUN STOPPED — audio output failed. Score and notes are preserved.` |
| COPY-020 | dirty score | `Unsaved score changes` |
| COPY-021 | save success | `Saved revision {revision}.` |
| COPY-022 | save failure | `Revision was not saved. The previous saved revision is unchanged.` |
| COPY-023 | no selection | `Select an event to audition or edit it.` |
| COPY-024 | offline | `Offline run available — required audio is already local.` |
| COPY-025 | delete event | `Delete {event_id} from the current score? Saved revisions are unchanged.` |
| COPY-026 | export success | `Exported {filename} with revision {revision} evidence.` |
| COPY-027 | evidence state | `KEEP` / `RETRY` / `DROP` / `HOLD` |
| COPY-028 | fixture warning | `FIXTURE CONTENT — replace with confirmed Voice text before artistic review.` |
| COPY-029 | dirty export | `Save a revision before export so the WAV and evidence sidecar share one identity.` |

## Prohibited ambiguity

Do not use generic `Something went wrong`, `Audio unavailable`, `Saved`, `Final`, `Approved`, `Correct Voice`, or `Production ready` where the system knows a more exact state.
