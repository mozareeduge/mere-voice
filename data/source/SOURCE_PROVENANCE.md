# Source provenance — current package

The working source file `voice_lines.fixture.json` was extracted from the `const BEATS` operational-score data embedded in:

`NIRAVANA_MOZARE_DIVERGENT_PERFORMANCE_DOSSIER_ARCHIVE_v0.6.html`

Only records with role code `v` (Voice) were selected. Fourteen strings are present there.

This is **not equivalent to the primary five-page play text**. The dossier itself says the primary text governs wording, and several operational-score Voice entries visibly contain ellipses. Accordingly:

- every line has `canonical: false`;
- every line records its dossier beat source;
- lines containing `…` are marked `dossier_excerpt_with_ellipsis`;
- the product displays a persistent fixture warning;
- no missing wording has been inferred or filled from model knowledge/web research.

When the exact play-text Voice lines are supplied, replace the source payload rather than editing text in the UI. Preserve exact Unicode/punctuation and record the primary witness reference.
