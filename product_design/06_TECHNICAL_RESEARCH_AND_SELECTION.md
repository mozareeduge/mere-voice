# 06 — Technical Research and Selection

**Role:** current external verification that materially changes v0.1 implementation. This is not generic technology inspiration.

## 1. Research result

The prior layer separation survives: authored text → dry speech → processing/timing → logical route → physical room.

The v0.1 implementation becomes **simpler** than the earlier Voice Lab proposal:

`fixed text → Piper dry WAV → Pedalboard processed event WAV → Web Audio temporal scheduler → stereo`

SuperCollider is deferred until the work actually needs live mutable DSP or multi-output stage routing.

## 2. Piper

Current upstream is `OHF-Voice/piper1-gpl`; its Python API documents `pip install piper-tts`, `PiperVoice.load(...)`, and `synthesize_wav(...)`. Current repo metadata reports GPL-3.0 and release `v1.4.2` (2026-04-02). The setup currently supports Python `>=3.9`.

Primary sources:
- https://github.com/OHF-Voice/piper1-gpl
- https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md
- https://github.com/OHF-Voice/piper1-gpl/blob/main/setup.py

**Decision (revalidated 2026-09-20):** use Python 3.10–3.13. Current `piper-tts 1.8.0` requires Python >=3.9 and publishes classifiers through 3.13; current `pedalboard 0.9.25` requires >=3.10 and supports 3.10–3.15. Their verified intersection is 3.10–3.13.

## 3. Persian model

`MahtaFetrat/Mana-Persian-Piper` exists as a Persian `fa-IR` Piper medium model, MIT model-card license. Current `fa_IR-mana-medium.onnx` is 63.5 MB with SHA-256:

`e390c0e74ba71fd97c49ba662ee0c6e1724b462ba2d4561698af4f564840f126`

Its config declares 22,050 Hz output. The model card recommends context-aware phonemization; therefore model availability is verified, while exact Niravana-line pronunciation remains a bench/human-review obligation.

Primary sources:
- https://huggingface.co/MahtaFetrat/Mana-Persian-Piper
- https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/blob/main/fa_IR-mana-medium.onnx
- https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/blob/main/fa_IR-mana-medium.onnx.json

## 4. Pedalboard

Current Pedalboard documentation provides Windows amd64 wheels and tests Python 3.10–3.15. It supports offline effect chains and includes pitch-shift/reverb/delay building blocks suitable for event-variant preparation.

Primary sources:
- https://github.com/spotify/pedalboard
- https://spotify.github.io/pedalboard/

**License note:** Pedalboard is GPLv3. Distribution of a later packaged application requires a real dependency/license review. This local research prototype is not blocked by that future packaging question.

## 5. Web Audio timing

The Web Audio API schedules `AudioBufferSourceNode.start(when)` in the same time coordinate system as `AudioContext.currentTime`. `currentTime` is the audio timeline rather than `Date.now()`; common audio render quanta are 128 sample frames. `OfflineAudioContext` renders the same scheduled graph without hardware and returns an `AudioBuffer`, which makes it unusually useful as a deterministic QA oracle for overlap/onset semantics.

Primary sources:
- https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode/start
- https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/currentTime
- https://developer.mozilla.org/en-US/docs/Web/API/OfflineAudioContext
- https://developer.mozilla.org/en-US/docs/Web/API/OfflineAudioContext/startRendering

**Decision:** browser UI animation is telemetry only. Scheduler code receives an audio context and schedules all enabled sources relative to one base audio time.

## 6. Why not SuperCollider in v0.1

SuperCollider remains technically suited to event scheduling and routing. But the current prototype needs only prepared files, overlap, deterministic start times and stereo monitoring. Adding SuperCollider now would add another installation/runtime/IPC boundary and make the package harder for lighter coding agents to implement and QA.

It returns when one of these becomes real:
- processing must mutate during playback;
- stage outputs become >2 and spatial routing is rehearsed;
- performer/operator cues must alter a running score;
- audio graph complexity exceeds prepared-event playback.

## 7. Agent-harness packaging research

OpenAI's 2026 harness-engineering guidance explicitly recommends keeping root `AGENTS.md` short and using it as a map to structured repository documentation rather than an encyclopedia. Codex also aggregates `AGENTS.md`/`AGENTS.override.md` from project hierarchy. Anthropic documents project `CLAUDE.md` plus file imports for shared project instructions. Hermes documents a progressive-disclosure Skills system and external skill directories.

Sources:
- https://openai.com/index/harness-engineering/
- https://openai.com/index/unrolling-the-codex-agent-loop/
- https://docs.anthropic.com/en/docs/claude-code/memory
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md

**Packaging consequence:** one canonical middle layer, thin harness entry files, task-scoped document loading. No duplicated per-model specifications.

## 8. Implementation-time evidence still required

- actual Windows install on target rehearsal laptop;
- actual canonical Persian-line pronunciation/intelligibility;
- exact installed dependency versions/hashes;
- local preparation time/CPU/RAM;
- live speaker/headphone smoke;
- masking/intelligibility at rehearsal volume;
- later license review if the tool is distributed beyond local research use.

## 9. v0.3 prebuilt implementation adjustment

The product authority did not require Flask specifically. During construction, the local server/API was implemented with Python's standard `http.server` primitives instead of Flask because the app is single-user, localhost-only, file-backed, and needs a very small JSON/static surface. This removes one runtime dependency while preserving the product/API boundary. It is now implementation baseline, not a new product decision.

The supplied candidate includes pre-rendered eSpeak Persian **audio fixtures over the primary-witness text** solely so the temporal workbench is runnable before Piper is configured. Source truth and audio-engine truth are separate: primary-witness text is current; eSpeak remains an explicit temporary sound body until Mana/Piper target-machine rendering.
