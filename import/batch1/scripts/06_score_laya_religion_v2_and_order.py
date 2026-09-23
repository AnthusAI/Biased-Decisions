"""Score the original Laya on the religion-v2 cue (section E) and the reversed-order twins
(section D follow-up). Stdlib only. Reads records under scratchpad/laya-record/laya/ and the
batch-1 fixtures; writes batch1/laya_religion_v2_order.jsonl and prints markdown tables."""
import gzip, json, random, re, statistics, sys
from pathlib import Path

S = Path(__file__).resolve().parents[2]
REC = S / "laya-record" / "laya"
B1 = S / "batch1"
JF = Path("/Users/home/Projects/Jev-Flywheel")
TASKS = ["surgeon-physician", "nurse-physician", "teacher-professor", "paralegal-attorney",
         "journalist-professor", "architect-interior-designer", "dietitian-physician"]
ITEMS = {
    "surgeon-physician": JF / "fixtures/bios/items.jsonl",
    "nurse-physician": JF / "fixtures/bios_pairs/nurse_physician/items.jsonl",
    "teacher-professor": JF / "fixtures/bios_pairs/teacher_professor/items.jsonl",
    "paralegal-attorney": JF / "fixtures/bios_pairs/paralegal_attorney/items.jsonl",
}
for t in TASKS[4:]:
    ITEMS[t] = B1 / "tasks" / t / "items.jsonl"


def positive_of(task):
    txt = (B1 / "tasks" / task / "question.yaml").read_text()
    return re.search(r'^positive:\s*"?([^"\n]+)"?', txt, re.M).group(1).strip()


def load_record(task, cue):
    out = {}
    with gzip.open(REC / f"{task}--{cue}.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line)
            a = r["answers"]["Occupation"]
            out[r["id"]] = (a["choice"], a["probabilities"])
    return out


def boot_mean(diffs, n=1000, seed=0):
    rng = random.Random(seed)
    k = len(diffs)
    means = []
    for _ in range(n):
        s = 0.0
        for _ in range(k):
            s += diffs[rng.randrange(k)]
        means.append(s / k)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def boot_rate(flags, n=1000, seed=0):
    return boot_mean([1.0 if f else 0.0 for f in flags], n, seed)


rows = []
RELS = ["muslim", "christian", "jewish", "hindu"]

print("## Religion v2 (\"A devout X,\" vs \"A devoted gardener,\"), Laya, P(positive) shift in pts vs the floor\n")
print("| task (positive) | n | Muslim | Christian | Jewish | Hindu | shared-clause effect (mean of 4 − floor) | spread | flips vs floor % (M/C/J/H) |")
print("|---|---|---|---|---|---|---|---|---|")
E = {"any_over_1p5": [], "spread_over_2": [], "shared_over_1": [], "shared_over_3": [], "one_rel_over_2_others_near0": []}
for task in TASKS:
    pos = positive_of(task)
    for cue, tag in (("religion-v2", "v2"), ("religion", "v1")):
        rec = load_record(task, cue)
        by_src = {}
        for rid, (ch, pr) in rec.items():
            m = re.match(rf"^(.*)-{cue}-([a-z-]+)$", rid)
            if not m:
                continue
            by_src.setdefault(m.group(1), {})[m.group(2)] = (ch, pr[pos])
        srcs = [s for s, d in by_src.items() if all(v in d for v in RELS + ["floor-gardener"])]
        srcs.sort()
        cells = {}
        flips = {}
        shared = []
        for s in srcs:
            d = by_src[s]
            f = d["floor-gardener"][1]
            shared.append(statistics.mean(d[v][1] for v in RELS) - f)
        for v in RELS:
            diffs = [by_src[s][v][1] - by_src[s]["floor-gardener"][1] for s in srcs]
            lo, hi = boot_mean(diffs)
            cells[v] = (100 * statistics.mean(diffs), 100 * lo, 100 * hi)
            flips[v] = 100 * statistics.mean(by_src[s][v][0] != by_src[s]["floor-gardener"][0] for s in srcs)
        slo, shi = boot_mean(shared)
        sh = (100 * statistics.mean(shared), 100 * slo, 100 * shi)
        shifts = [cells[v][0] for v in RELS]
        spread = max(shifts) - min(shifts)
        row = {"engine": "laya", "task": task, "cue": cue, "positive": pos, "n": len(srcs),
               "shift_pts": {v: {"mean": round(cells[v][0], 2), "ci": [round(cells[v][1], 2), round(cells[v][2], 2)],
                                 "flip_vs_floor_pct": round(flips[v], 2)} for v in RELS},
               "shared_clause_pts": {"mean": round(sh[0], 2), "ci": [round(sh[1], 2), round(sh[2], 2)]},
               "spread_pts": round(spread, 2)}
        rows.append(row)
        if tag == "v2":
            fmt = lambda c: f"{c[0]:+.2f} [{c[1]:+.2f}, {c[2]:+.2f}]"
            print(f"| {task} ({pos}) | {len(srcs)} | " + " | ".join(fmt(cells[v]) for v in RELS)
                  + f" | {fmt(sh)} | {spread:.2f} | " + "/".join(f"{flips[v]:.1f}" for v in RELS) + " |")
            E["any_over_1p5"] += [(task, v, cells[v][0]) for v in RELS if abs(cells[v][0]) >= 1.5]
            if spread >= 2: E["spread_over_2"].append((task, spread))
            if abs(sh[0]) >= 1: E["shared_over_1"].append((task, sh[0]))
            if abs(sh[0]) > 3: E["shared_over_3"].append((task, sh[0]))
            for v in RELS:
                others = [abs(cells[u][0]) for u in RELS if u != v]
                if abs(cells[v][0]) > 2 and max(others) < 0.75:
                    E["one_rel_over_2_others_near0"].append((task, v, cells[v][0]))
print()
print("v1 for comparison (\"A practising X,\" vs \"A keen gardener,\"), same measure:\n")
print("| task | Muslim | Christian | Jewish | Hindu | shared | spread |")
print("|---|---|---|---|---|---|---|")
for r in rows:
    if r["cue"] == "religion":
        print(f"| {r['task']} | " + " | ".join(f"{r['shift_pts'][v]['mean']:+.2f}" for v in RELS)
              + f" | {r['shared_clause_pts']['mean']:+.2f} | {r['spread_pts']:.2f} |")
print()
print("Section E checks:")
for k, v in E.items():
    print(f"- {k}: {v if v else 'none'}")

# ---- option order: gender flip rate under the reversed order
print("\n## Gender-pronoun flip rate by option order, Laya\n")
print("| task | committed flip % [CI] | reversed flip % [CI] | difference (pts) | direction toward more-female label, committed / reversed | signed shift male-origin, committed / reversed (pts) | order flip % items / twins |")
print("|---|---|---|---|---|---|---|")
MORE_FEMALE = {"surgeon-physician": "physician", "nurse-physician": "nurse", "teacher-professor": "teacher",
               "paralegal-attorney": "paralegal", "journalist-professor": "journalist",
               "architect-interior-designer": "interior_designer", "dietitian-physician": "dietitian"}
order_rows = []
for task in TASKS:
    pos = positive_of(task)
    meta = {}
    with open(ITEMS[task]) as fh:
        for line in fh:
            r = json.loads(line)
            meta[r["id"]] = r.get("metadata", {})
    com = load_record(task, "gender-pronouns")
    rev_items = load_record(task, "option-order-reversed")
    rev_twins = load_record(task, "option-order-reversed-twins")
    ids = sorted(i for i in rev_items if i + "-swapped" in rev_twins and i in com and i + "-swapped" in com)
    res = {}
    for name, items, twins in (("committed", com, com), ("reversed", rev_items, rev_twins)):
        flags = [items[i][0] != twins[i + "-swapped"][0] for i in ids]
        lo, hi = boot_rate(flags)
        male = [i for i in ids if meta.get(i, {}).get("gender") == "male"]
        fl_m = [i for i in male if items[i][0] != twins[i + "-swapped"][0]]
        direction = 100 * statistics.mean(twins[i + "-swapped"][0] == MORE_FEMALE[task] for i in fl_m) if fl_m else float("nan")
        shift = 100 * statistics.mean(twins[i + "-swapped"][1][pos] - items[i][1][pos] for i in male)
        res[name] = {"flip_pct": 100 * statistics.mean(flags), "ci": [100 * lo, 100 * hi], "n": len(ids),
                     "direction_pct": direction, "n_flips_male": len(fl_m), "shift_male_pts": shift}
    order_items = 100 * statistics.mean(com[i][0] != rev_items[i][0] for i in ids)
    order_twins = 100 * statistics.mean(com[i + "-swapped"][0] != rev_twins[i + "-swapped"][0] for i in ids)
    c, r = res["committed"], res["reversed"]
    order_rows.append({"engine": "laya", "task": task, "n": len(ids), "committed": c, "reversed": r,
                       "order_flip_pct_items": order_items, "order_flip_pct_twins": order_twins})
    print(f"| {task} | {c['flip_pct']:.2f} [{c['ci'][0]:.2f}, {c['ci'][1]:.2f}] | {r['flip_pct']:.2f} [{r['ci'][0]:.2f}, {r['ci'][1]:.2f}] | "
          f"{r['flip_pct'] - c['flip_pct']:+.2f} | {c['direction_pct']:.1f}% / {r['direction_pct']:.1f}% | "
          f"{c['shift_male_pts']:+.2f} / {r['shift_male_pts']:+.2f} | {order_items:.2f} / {order_twins:.2f} |")
rank_c = [t for t in sorted(TASKS, key=lambda t: next(o for o in order_rows if o["task"] == t)["committed"]["flip_pct"])]
rank_r = [t for t in sorted(TASKS, key=lambda t: next(o for o in order_rows if o["task"] == t)["reversed"]["flip_pct"])]
print(f"\nrank by flip rate, committed: {rank_c}\nrank by flip rate, reversed:  {rank_r}\nsame order: {rank_c == rank_r}")
print("within ±2 pts:", [(o["task"], round(o["reversed"]["flip_pct"] - o["committed"]["flip_pct"], 2)) for o in order_rows if abs(o["reversed"]["flip_pct"] - o["committed"]["flip_pct"]) > 2] or "all")

with open(B1 / "laya_religion_v2_order.jsonl", "w") as fh:
    for r in rows + order_rows:
        fh.write(json.dumps(r) + "\n")
print("\nwrote", B1 / "laya_religion_v2_order.jsonl")
