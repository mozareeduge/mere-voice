export function scheduleBuffers(ctx, items, { baseAudioTime = 0, fromMs = 0, destination = ctx.destination } = {}) {
  const sources = [];
  for (const item of items) {
    if (!item.event.enabled || item.event.start_ms < fromMs) continue;
    const src = ctx.createBufferSource();
    src.buffer = item.buffer;
    src.connect(destination);
    src.start(baseAudioTime + (item.event.start_ms - fromMs) / 1000);
    sources.push(src);
  }
  return sources;
}

export class TemporalAudioEngine {
  constructor() {
    this.ctx = null;
    this.active = [];
    this.runToken = 0;
    this.startedAt = null;
  }

  async ensureContext() {
    if (!this.ctx || this.ctx.state === 'closed') {
      this.ctx = new AudioContext({ latencyHint: 'interactive' });
    }
    if (this.ctx.state === 'suspended') await this.ctx.resume();
    return this.ctx;
  }

  async loadBuffer(url) {
    const ctx = await this.ensureContext();
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`Audio load failed ${res.status}: ${url}`);
    return ctx.decodeAudioData(await res.arrayBuffer());
  }

  async schedule(events, { fromMs = 0, leadSeconds = 0.10, onTick = null, onDone = null } = {}) {
    this.stop();
    const ctx = await this.ensureContext();
    const token = ++this.runToken;
    const playable = events.filter(e => e.enabled && e.start_ms >= fromMs && e.audio_url);
    const buffers = await Promise.all(playable.map(e => this.loadBuffer(e.audio_url)));
    const base = ctx.currentTime + leadSeconds;
    this.startedAt = { audioTime: base, scoreOffsetMs: fromMs };
    let endScoreMs = fromMs;

    this.active = scheduleBuffers(ctx, playable.map((event, i) => ({ event, buffer: buffers[i] })), { baseAudioTime: base, fromMs });
    playable.forEach((event, i) => {
      endScoreMs = Math.max(endScoreMs, event.start_ms + buffers[i].duration * 1000);
    });

    const tick = () => {
      if (token !== this.runToken) return;
      const elapsedMs = Math.max(0, (ctx.currentTime - base) * 1000 + fromMs);
      onTick?.(elapsedMs);
      if (elapsedMs < endScoreMs + 80) requestAnimationFrame(tick);
      else {
        this.active = [];
        onDone?.(endScoreMs);
      }
    };
    requestAnimationFrame(tick);
    return { baseAudioTime: base, fromMs, endScoreMs, count: playable.length };
  }

  async audition(url) {
    this.stop();
    const ctx = await this.ensureContext();
    const buffer = await this.loadBuffer(url);
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(ctx.destination);
    src.start(ctx.currentTime + 0.03);
    this.active = [src];
    return buffer.duration;
  }

  stop() {
    this.runToken++;
    for (const src of this.active) {
      try { src.stop(); } catch (_) {}
      try { src.disconnect(); } catch (_) {}
    }
    this.active = [];
    this.startedAt = null;
  }
}

export function computeRelativeSchedule(events, fromMs = 0) {
  return events
    .filter(e => e.enabled && e.start_ms >= fromMs)
    .map(e => ({ event_id: e.event_id, relative_ms: e.start_ms - fromMs }))
    .sort((a,b) => a.relative_ms - b.relative_ms || a.event_id.localeCompare(b.event_id));
}
