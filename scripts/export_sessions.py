"""Export OpenCode sessions for this repo into readable transcripts + stats for the pain-point study."""
import sqlite3, json, collections, re
from pathlib import Path

DB = r"C:\Users\zubair\.local\share\opencode\opencode.db"
OUT = Path(r"C:\Users\zubair\Documents\GitHub\pdf-to-docx\_temp\painpoints")
(OUT / "transcripts").mkdir(parents=True, exist_ok=True)
c = sqlite3.connect(DB)


def clip(s, n):
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f" …[+{len(s) - n} chars]"


def file_of(inp):
    for k in ("path", "filePath", "file_path"):
        if isinstance(inp, dict) and k in inp:
            return str(inp[k]).replace("/", "\\").lower()
    return None


sessions = c.execute(
    "select id,parent_id,title,cost,time_created,time_updated from session_v2 "
    "where directory like '%pdf-to-docx%' order by time_created").fetchall()
index, all_stats = [], {}
for sid, parent, title, cost, t0, t1 in sessions:
    lines = [f"# {title}\n", f"session {sid} parent {parent} cost ${cost or 0:.2f} minutes {(t1 - t0) / 60000:.0f}\n"]
    st = collections.Counter()
    edits = collections.Counter()
    writes = collections.Counter()
    builds, errors, script_runs = 0, 0, collections.Counter()
    for typ, data in c.execute("select type,data from session_message where session_id=? order by seq", (sid,)):
        d = json.loads(data)
        if typ in ("user", "synthetic"):
            lines.append(f"\n## [{typ.upper()}]\n{clip(d.get('text', ''), 4000)}\n")
            continue
        if typ != "assistant":
            continue
        if d.get("error"):
            errors += 1
            lines.append(f"\n**[ASSISTANT ERROR]** {clip(d['error'].get('message', ''), 300)}\n")
        for part in d.get("content") or []:
            t = part.get("type")
            if t == "text" and part.get("text", "").strip():
                lines.append(f"\n**[ASSISTANT]** {clip(part['text'], 2500)}\n")
            elif t == "tool":
                name = part.get("name")
                state = part.get("state", {})
                inp = state.get("input", {})
                st[name] += 1
                f = file_of(inp)
                if name == "edit" and f:
                    edits[f] += 1
                if name == "write" and f:
                    writes[f] += 1
                if name == "shell":
                    cmd = inp.get("command", "")
                    if "lesson-builder build" in cmd or "build" in cmd:
                        builds += 1
                    for m in re.findall(r"[\w\-./\\]+\.py", cmd):
                        script_runs[m.split("\\")[-1].split("/")[-1]] += 1
                res = ""
                for cpart in state.get("content") or []:
                    if cpart.get("type") == "text":
                        res += cpart.get("text", "")
                status = state.get("status")
                lines.append(f"\n- TOOL `{name}` ({status}): {clip(inp, 600)}\n  -> {clip(res, 500)}\n")
    stats = {"title": title, "parent": parent, "cost": round(cost or 0, 2),
             "minutes": round((t1 - t0) / 60000), "tools": dict(st), "builds": builds, "errors": errors,
             "top_edited": edits.most_common(12), "top_written": writes.most_common(8),
             "scripts_run": script_runs.most_common(10)}
    all_stats[sid] = stats
    safe = re.sub(r"[^\w\-]+", "_", title or "untitled")[:60]
    (OUT / "transcripts" / f"{t0}_{sid[-8:]}_{safe}.md").write_text("".join(lines), encoding="utf-8")
    index.append((t0, sid, parent, title, stats["cost"], stats["minutes"], sum(st.values()), builds, errors))

(OUT / "stats.json").write_text(json.dumps(all_stats, indent=1, ensure_ascii=False), encoding="utf-8")
with open(OUT / "index.md", "w", encoding="utf-8") as fh:
    fh.write("| created | session | parent | title | cost $ | min | tool calls | builds | errors |\n|---|---|---|---|---|---|---|---|---|\n")
    for r in index:
        fh.write("| " + " | ".join(str(x) for x in r) + " |\n")
print(len(index), "sessions exported")
