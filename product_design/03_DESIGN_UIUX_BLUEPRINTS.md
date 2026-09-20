# 03 — Design / UI-UX Blueprints

## 1. Design position

This is a **rehearsal instrument**, not a generic DAW and not the performance. The dominant thing is the relation between authored Persian text, onset time, overlap and audible transformation. Provenance exists but stays visually secondary.

Dark-only v0.1. No theme toggle.

## 2. Surface anatomy — SURF-001 Voice Temporal Workbench

### A. Transport / readiness — persistent top strip
Order of importance:
1. run mode/state: `NOT READY | READY | PLAYING | DRY BYPASS | FAILED`;
2. elapsed score time;
3. `PLAY FULL`;
4. `PLAY FROM SELECTION`;
5. `STOP / RESET` while sounding;
6. preparation action when needed (`RENDER DRY`, `PREPARE SCORE`).

A disabled primary action always has a nearby causal reason.

### B. Voice line library — left rail on wide desktop
Each row:
- stable `VOICE-###`;
- exact Persian source text, RTL, read-only;
- dry asset state + duration;
- `DRY` audition;
- `ADD EVENT`.

No in-app canonical text editor in v0.1.

### C. Timeline — dominant central field
- LTR time axis; labels `mm:ss.mmm`;
- event blocks start at authored `start_ms`;
- lanes are a presentation solution, not semantic ordering;
- silence stays visibly empty;
- overlap never hides all participating blocks;
- selected event distinctly outlined;
- playhead is visual telemetry only;
- zoom + timeline-owned horizontal scroll;
- **no drag-to-edit requirement**. Event movement occurs through numeric `start_ms` in the inspector.

Event block minimum content at ordinary zoom: event ID + line ID + short Persian preview. Full line is visible in inspector/library.

### D. Event inspector — right rail / compact bottom dock
Sections:
- ID + enabled state;
- TIME: `start_ms`, derived dry/processed duration read-only;
- LEVEL/SPACE: gain, pan;
- PITCH: semitones;
- TAIL: reverb mix, delay time, feedback;
- ENVELOPE: attack/release;
- lifecycle actions: Duplicate, Delete;
- `AUDITION EVENT`.

Changing a processing field marks only that event's processed variant stale. Changing start time does not.

### E. Research / revision region
Compact lower panel or inspector tab:
- score name/revision/dirty state;
- `SAVE REVISION`;
- short note + KEEP/RETRY/DROP/HOLD;
- `EXPORT RUN`.

## 3. Interaction truth

- `PLAY FULL` in processed mode: enabled only when all enabled events have current dry + processed audio.
- `PLAY FULL` in DRY BYPASS: requires only current dry assets.
- `PLAY FROM SELECTION`: selected enabled event required.
- `AUDITION EVENT`: if variant is stale, show `PREPARING…`, prepare that event, then audition; never pretend it was already ready.
- `DELETE EVENT`: current event disappears only from unsaved/current score; prior saved revision remains.
- `EXPORT RUN`: enabled only when current UI state matches a saved revision; dirty state must be saved first so export provenance is unambiguous.
- `RENDER DRY`: acts on missing/stale/failed required dry assets, not on already-current assets.
- `PREPARE SCORE`: acts on missing/stale/failed variants for enabled events.

## 4. Visual hierarchy

Dominant: timeline + selected source line.  
Secondary: event inspector + transport.  
Tertiary: hashes, paths, model details, export metadata.

Do not make every panel a same-weight card. Avoid dashboard aesthetics that flatten the rehearsal relation into metrics.

## 5. Responsive contract

### DESKTOP_WIDE — ≥1280px
`library | timeline | inspector`, transport above, research panel collapsible below.

### DESKTOP_COMPACT — 1024–1279px
Library remains visible but narrower; inspector docks below timeline; transport remains one persistent row where feasible.

### <1024px
Unsupported acceptance target. The app may render, but no mobile workflow or product compromises are required.

### 1024×768 stress
- no page horizontal overflow;
- transport reachable without horizontal scrolling;
- timeline may scroll horizontally internally;
- selected event inspector reachable without covering transport.

## 6. Typography / directionality

- Persian: Vazirmatn local/web-safe fallback, correct RTL shaping.
- Timing/IDs/parameters: readable monospace/tabular numerals, LTR isolated.
- Persian and numeric fragments must not reorder each other because of bidi mistakes.

## 7. Keyboard/accessibility

- Tab: transport → line library → timeline events → inspector → research region.
- Enter/Space activates focused buttons.
- `Space` may toggle Play/Stop only when focus is not an editable control.
- Escape closes transient popovers only; ordinary editing is non-modal.
- after Stop/reset, focus returns to initiating transport control.
- state uses word + icon/shape, never hue only.
- visible 2px-or-equivalent focus indication.
- practical target size ≈40 CSS px or larger for rehearsal use.
- reduced-motion removes eased playhead/scroll animation but not direct state updates.
- audio failures always have textual state.

## 8. Density/overflow

- up to 12 clustered events is a required density fixture;
- hashes/paths may visually truncate but remain inspectable/copyable;
- long Persian lines wrap in library/inspector;
- parameter labels remain textual; do not collapse critical controls to unexplained icons.
