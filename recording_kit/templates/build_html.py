import json, sys
from pathlib import Path
S = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
lines = json.load(open(S / "lines17.json", encoding="utf-8"))
gm = json.load(open(S / "gm_pilot.json", encoding="utf-8"))
reading = json.load(open(S / "reading_sentences.json", encoding="utf-8"))
by = {l["id"]: l["fa"] for l in lines}
fa = lambda n: str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
TAKE = {"A": "اجرای A · طبیعی", "B": "اجرای B · دور و بالینی"}
DIRECTIONS = """<p><b>اجرای A — «طبیعی»:</b> همان‌طور بخوانید که اگر این جمله را آرام برای کسی در همان اتاق می‌گفتید. بدون بازیگری و بدون اغراق.</p>
<p><b>اجرای B — «دور و بالینی»:</b> یکنواخت‌تر و خنثی‌تر، کمی دور؛ مثل صدایی که گزارش می‌دهد و احساسش را نشان نمی‌دهد.</p>
<p class="hint">در هر دو اجرا صدا باید کامل و روشن باشد. آرام خواندن اشکالی ندارد، اما لطفاً پچ‌پچ یا نجوا نکنید.</p>"""

def line_item(lid, t, part, note=None):
    return {"key": f"{lid}_{t}", "file": f"{lid}_{t}", "line_id": lid, "take": t, "part": part, "part_note": note,
            "label": f"{lid} · {TAKE[t]}", "text": by[lid], "min_s": 1, "max_s": 180}

audition = {"id": "audition", "title": "Audition — 3 lines x 2 takes", "items":
    [line_item(l, "A", "سطرها — اجرای A (طبیعی)") for l in ["VOICE-001", "VOICE-004", "VOICE-009"]] +
    [line_item(l, "B", "سطرها — اجرای B (دور و بالینی)") for l in ["VOICE-001", "VOICE-004", "VOICE-009"]]}

P1 = "بخش ۱ — هفده سطر «صدا»"
full_items = [line_item(l["id"], t, P1) for l in lines for t in "AB"]
P2 = "بخش ۲ — خواندن متن‌های متنوع (برای شناخت صدای شما)"
N2 = "این متن‌ها ربطی به نمایش ندارند. هر بخش را پشت سر هم در یک ضبط بخوانید، ساده و طبیعی، هر جمله یک‌بار، با مکثی کوتاه بین جمله‌ها."
full_items.append({"key": "READING_1", "file": "READING_1", "part": P2, "part_note": N2, "label": "الف) جمله‌های روزمره و رسمی · یک ضبط",
    "text": "\n".join(f"{fa(i+1)}. {t}" for i, t in enumerate(reading)), "long": True, "min_s": 60, "max_s": 1500})
full_items.append({"key": "READING_2", "file": "READING_2", "part": P2, "label": "ب) سطرهایی از شعر ماشینی «گور-ماشین» · یک ضبط (ساده و روشن، بدون تفسیر)",
    "text": "\n".join(f"{fa(i+1)}. {t}" for i, t in enumerate(gm["reading_lines"])), "long": True, "min_s": 60, "max_s": 1500})
P3 = "بخش ۳ — صحبت آزاد"
full_items.append({"key": "FREE", "file": "FREE", "part": P3, "label": "سه تا پنج دقیقه، بی‌متن",
    "text": "آزاد صحبت کنید؛ مثلاً درباره‌ی راه همیشگی‌تان تا خانه، یک روز معمولی، یا اتاقی که در آن بزرگ شده‌اید. لازم نیست جالب یا منظم باشد؛ فقط طبیعی.", "min_s": 60, "max_s": 900})
P4 = "بخش ۴ — سطرهای «گور-ماشین» (آزمایش مونتاژ)"
N4 = "هر سطر را یک‌بار و در حالت «طبیعی» بخوانید. این سطرها را یک ماشین ساخته و ممکن است عجیب به نظر برسند."
for x in gm["pilot"]:
    for d in x["donors"]:
        full_items.append({"key": d["id"], "file": d["id"], "part": P4 + " · سطرهای اول", "part_note": N4, "label": d["id"], "text": d["text"], "min_s": 1, "max_s": 60})
for x in gm["pilot"]:
    full_items.append({"key": x["target_id"], "file": x["target_id"], "line_id": x["target_id"], "take": "A", "part": P4 + " · سطرهای دوم", "label": x["target_id"], "text": x["target_text"], "min_s": 1, "max_s": 60})
full = {"id": "full-session", "title": "Full session — 17 lines x 2, reading, free speech, Grave-Machine pilot", "items": full_items}

tpl = (S / "html" / "recorder_template.html").read_text(encoding="utf-8")
for name, sess, heading, dur in [
    ("01_Audition_Recorder_FA.html", audition, "تست صدا برای نقش «صدا»", "حدود ۱۵ دقیقه · ۶ ضبط"),
    ("02_Full_Session_Recorder_FA.html", full, "جلسه‌ی ضبط کامل برای نقش «صدا»", f"حدود یک تا یک‌ونیم ساعت · {fa(len(full_items))} ضبط · می‌توانید در چند نوبت ضبط کنید"),
]:
    html = (tpl.replace("__TITLE__", heading).replace("__HEADING__", heading).replace("__DURATION__", dur)
            .replace("__DIRECTIONS__", DIRECTIONS).replace("/*__DATA__*/null", json.dumps(sess, ensure_ascii=False)))
    (OUT / name).write_text(html, encoding="utf-8")
    print(name, len(sess["items"]), "items", len(html) // 1024, "KB")

line_texts = {l["id"]: l["fa"] for l in lines}
line_texts.update({x["target_id"]: x["target_text"] for x in gm["pilot"]})
desk = (S / "html" / "desk_template.html").read_text(encoding="utf-8").replace("/*__LINES__*/null", json.dumps(line_texts, ensure_ascii=False))
(OUT / "00_Voice_Casting_Desk.html").write_text(desk, encoding="utf-8")
print("00_Voice_Casting_Desk.html", len(desk) // 1024, "KB")
