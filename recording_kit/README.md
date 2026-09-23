# recording_kit

Sources for the performer recorder pages, the casting desk, and the Word/PDF scripts.
The finished kit is delivered outside the repo (it contains no audio).

Rebuild pages: put `lines17.json` (from data/source), `gm_pilot.json` (bench/grammar_pilot_spec.json) and `reading_sentences.json` in one folder with the templates, then run `python build_html.py <folder> <out>`.
Word files: `node build_docs.js <out>` (needs the `docx` npm package).
