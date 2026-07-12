#!/usr/bin/env python3
"""Inject the owner's GitHub repos as portfolio project cards.

Runs in GitHub Actions. Rewrites the block between the PORTFOLIO-REPOS markers in
index.html so every repo shows up automatically — new repos appear on the next run.
Originals first (best-starred), forks after. Self-contained (stdlib only).
"""
import json, os, re, urllib.request

OWNER = os.environ.get("OWNER", "Yashwanth-pilli")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HTML = "index.html"
START, END = "<!-- PORTFOLIO-REPOS:START -->", "<!-- PORTFOLIO-REPOS:END -->"
COLORS = ["var(--violet)", "var(--green)", "var(--gold)", "var(--red)"]

# richer copy for the flagship repos; others use their GitHub description
FEATURE = {
    "illip-ai": ("your AI company, in your device",
                 "FastAPI-based local-first AI platform integrating multiple LLMs for "
                 "assistant & automation workflows — prompt handling, model routing, "
                 "agent crew, memory, and a governance gate."),
    "quantumshield-biodefense-os": ("live cyber command center",
                 "Real-time cybersecurity dashboard — mission control for biodefense "
                 "threat monitoring with live telemetry and an operator-grade UI."),
}


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "portfolio",
        **({"Authorization": f"token {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def all_repos():
    out, page = [], 1
    while True:
        b = api(f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed&page={page}")
        if not b:
            break
        out += b
        if len(b) < 100:
            break
        page += 1
    # drop the profile repo and the pages repo itself
    skip = {OWNER.lower(), f"{OWNER.lower()}.github.io"}
    return [r for r in out if r["name"].lower() not in skip]


def order(repos):
    return sorted(repos, key=lambda r: (-(r.get("stargazers_count") or 0),
                  tuple(-ord(c) for c in (r.get("pushed_at") or "")), r["name"].lower()))


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(repo, color):
    name = repo["name"]
    key = name.lower()
    feat = FEATURE.get(key)
    tag = feat[0] if feat else (repo.get("language") or "project")
    desc = feat[1] if feat else (repo.get("description") or "A project on my GitHub.")
    chips = []
    if repo.get("language"):
        chips.append(repo["language"])
    if repo.get("fork"):
        chips.append("fork")
    if (repo.get("stargazers_count") or 0) > 0:
        chips.append(f"★ {repo['stargazers_count']}")
    chip_html = "".join(f'<span class="chip">{esc(c)}</span>' for c in chips)
    return (f'<div class="card" style="--accent:{color}"><h3>{esc(name)}</h3>'
            f'<div class="tag">{esc(tag)}</div><p>{esc(desc)}</p>'
            f'<div class="chips">{chip_html}</div>'
            f'<a class="lk" href="{repo["html_url"]}" target="_blank" rel="noopener">Repository ↗</a></div>')


def main():
    with open(HTML, encoding="utf-8") as f:
        text = f.read()
    if START not in text or END not in text:
        print("markers missing"); return
    repos = order(all_repos())
    cards = "\n      ".join(card(r, COLORS[i % len(COLORS)]) for i, r in enumerate(repos))
    block = f"{START}\n      {cards}\n    {END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new == text:
        print("no change"); return
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"portfolio updated with {len(repos)} repos")


if __name__ == "__main__":
    main()
