"""Wide-screen section markup (python3 scripts/split-sections.py [src-dir]).

Wraps each content section's head (the H2 plus the one-line lede and note paragraphs right after
it) in <div class="sec-head"> and the rest in <div class="sec-body">, so wide screens can lay them
out as two columns (see the "Wide screens" block at the end of src/styles/site.css). A section with
no figure, table, chart or card grid after its head is marked sec-prose instead. Line-based: the
children of a section are the lines at the section's indent + 2. Idempotent: sections that already
carry a sec-* class are left alone. Review the diff; sections it cannot parse are marked by hand.
Adapted from the Hard-Decisions site's script of the same name."""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "src")
HEAD = re.compile(r'^(?:\{[^<]*?(?:&&|\?)\s*)?<(?:h2\b|p class="(?:lede|note|footnote|fnote)[ "]|nav class="reg-links"|ModelsLine\b)')
FIGURE = re.compile(
    r'<(?:table|figure|pre|dl|details|ol class="overall|ul class="around-list)'
    r'|class="(?:[^"]*\b(?:dim-grid|spider-row|table-scroll|cov|ex-grid|og-gallery|around|trope-visual|gaza-visual|nchart|diagram'
    r'|eng-stats|eng-cells|recipe-grid|risk-grid|stim-bars|req-resp|code|vocab|defs)\b)'
    r'|data-legend'
    r'|<(?:Chart|Matrix|FacetTable|Example|Stimulus|NeutralCost|NeutralDirection|TropeVisual|GazaStatusVisual|ProbabilityStrip|Prereg)\b')
OPEN = re.compile(r'^(\s*)(?:\{[^<]*&&\s*)?<section class="wrap section([^"]*)"([^>]*)>\s*$')


def process(path):
    lines = path.read_text().split("\n")
    out, i, changed = [], 0, 0
    while i < len(lines):
        m = OPEN.match(lines[i])
        if not m or "sec-" in lines[i]:
            out.append(lines[i]); i += 1; continue
        ind = m.group(1)
        j = i + 1  # the matching close at the same indent
        while j < len(lines) and not re.match(rf'^{ind}</section>', lines[j]):
            j += 1
        if j >= len(lines):
            out.append(lines[i]); i += 1; continue
        body = lines[i + 1:j]
        cind = ind + "  "
        starts = [k for k, l in enumerate(body) if l.startswith(cind) and not l.startswith(cind + " ") and l.strip()
                  and not l.strip().startswith(("</", ")}", "))}", "); }", "})", ": "))]
        children = [(s, (starts[n + 1] if n + 1 < len(starts) else len(body))) for n, s in enumerate(starts)]
        head_end = 0
        for s, e in children:
            if HEAD.search(body[s].strip()) and sum(1 for l in body[s:e] if l.strip()) == 1:
                head_end = e
            else:
                break
        rest = body[head_end:]
        has_fig = any(FIGURE.search(l) for l in rest)
        if head_end == 0 or not has_fig:
            out.append(lines[i].replace('class="wrap section', 'class="wrap section sec-prose', 1))
            out.extend(body); out.append(lines[j]); i = j + 1; changed += 1; continue
        out.append(lines[i].replace('class="wrap section', 'class="wrap section sec-split', 1))
        out.append(f'{cind}<div class="sec-head">')
        out.extend(body[:head_end])
        out.append(f'{cind}</div>')
        out.append(f'{cind}<div class="sec-body">')
        out.extend(rest)
        out.append(f'{cind}</div>')
        out.append(lines[j]); i = j + 1; changed += 1
    path.write_text("\n".join(out))
    return changed


for p in sorted(ROOT.rglob("*.astro")):
    n = process(p)
    if n: print(f"{p.relative_to(ROOT)}: {n}")
