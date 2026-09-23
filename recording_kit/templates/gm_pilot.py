import json, re, random, sys
S = sys.argv[1]
fa = json.load(open(f"{S}/gm_fa.json", encoding="utf-8"))
tr = fa["materials"]["trays"]; ov = fa["forms"]["overrides"]
dev = {d["id"]: d for d in fa["lineDevices"]}
rng = random.Random(20260924)

def surface(tok, form):
    return ov.get(tok["id"], {}).get(form, tok["literal"]) if form else tok["literal"]

def realize(route, slots, fills):
    out = route["template"]
    for i, (s, f) in enumerate(re.findall(r"\{(\w+)(?::(\w+))?\}", route["template"])):
        out = out.replace("{%s%s}" % (s, ":" + f if f else ""), surface(fills[i], f), 1)
    return out

def draw(slots, keys, avoid=None):
    fills = []
    for i, (s, f) in enumerate(keys):
        pool = tr[slots[s]]
        if avoid is not None and avoid[i] is not None:
            pool = [t for t in pool if t["id"] != avoid[i]["id"]] or pool
        fills.append(rng.choice(pool))
    return fills

d = dev["fa_ledger"]; slots = {x["slot"]: x["tray"] for x in d["inputs"]}
routes = {r["id"]: r for r in d["routes"]}
picked = ["fa_l_agent_body", "fa_l_doc_body", "fa_l_agent_case", "fa_l_body_case", "fa_l_become"]
pilot = []
for n, rid in enumerate(picked, 1):
    r = routes[rid]; keys = re.findall(r"\{(\w+)(?::(\w+))?\}", r["template"])
    target = draw(slots, keys)
    donors = []
    for parity in (0, 1):  # donor keeps units at one parity, changes the others
        keep = [target[i] if i % 2 == parity else None for i in range(len(keys))]
        fresh = draw(slots, keys, avoid=[target[i] if keep[i] is None else None for i in range(len(keys))])
        donors.append([keep[i] or fresh[i] for i in range(len(keys))])
    pilot.append({
        "target_id": f"GM-{n:02d}", "route": rid, "template": r["template"],
        "target_text": realize(r, slots, target),
        "units": [{"slot": s, "form": f or "base", "text": surface(target[i], f), "from_donor": f"GM-{n:02d}{'ab'[i % 2]}"} for i, (s, f) in enumerate(keys)],
        "donors": [{"id": f"GM-{n:02d}{'ab'[k]}", "text": realize(r, slots, donors[k])} for k in (0, 1)],
    })
# extra grammar lines across all devices for the reading session
extra = []
for dv in fa["lineDevices"]:
    sl = {x["slot"]: x["tray"] for x in dv["inputs"]}
    for r in rng.sample(dv["routes"], min(5, len(dv["routes"]))):
        keys = re.findall(r"\{(\w+)(?::(\w+))?\}", r["template"])
        extra.append(realize(r, sl, draw(sl, keys)))
json.dump({"seed": 20260924, "source": "grave-machine fa v1.1.1 (index.html)", "pilot": pilot, "reading_lines": extra},
          open(f"{S}/gm_pilot.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for p in pilot:
    print(p["target_id"], p["target_text"]); [print("   ", x["id"], x["text"]) for x in p["donors"]]
print(len(extra), "reading lines, e.g.:"); [print("  ", x) for x in extra[:6]]
