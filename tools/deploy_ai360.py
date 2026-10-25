"""Copy the v3 sales page into the ai360 site under /double-agent/ (thank-you page at /double-agent/thanks/,
the done-for-you purchase thank-you page at /double-agent/thanks-dfy/,
and the dice-roll test page at /double-agent/dice/ when tools/dice/build.py --live has produced it).
Only the assets the two pages reference are copied, and relative ../../assets/ paths become /double-agent/assets/.
Usage: python3 tools/deploy_ai360.py [ai360_repo_path]   (then commit and push the ai360 repo)
"""
import re, sys, shutil, pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent
PAGE = SRC / "variations" / "v3-indigo"
DST = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else SRC.parent / "ai360") / "double-agent"
PREFIX = "/double-agent/assets/"
REF = re.compile(r"\.\./\.\./assets/([^\"')\s]+)")

# Replace only what this script owns; other folders under /double-agent/ (e.g. Peleg's webinar/) stay untouched
for owned in ("index.html", "thanks", "thanks-dfy", "dice", "assets"):
    target = DST / owned
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
(DST / "thanks").mkdir(parents=True, exist_ok=True)
(DST / "thanks-dfy").mkdir(parents=True, exist_ok=True)
(DST / "dice").mkdir(parents=True, exist_ok=True)

needed = set()
PAGES = (("index.html", "index.html"), ("thank-you.html", "thanks/index.html"), ("thank-you-dfy.html", "thanks-dfy/index.html"))
if (PAGE / "index-dice-live.html").exists():
    PAGES += (("index-dice-live.html", "dice/index.html"),)
for src_name, dst_rel in PAGES:
    html = (PAGE / src_name).read_text(encoding="utf-8")
    needed.update(REF.findall(html))
    (DST / dst_rel).write_text(html.replace("../../assets/", PREFIX), encoding="utf-8")

copied = 0
for rel in sorted(needed):
    src = SRC / "assets" / rel
    if src.is_dir():
        shutil.copytree(src, DST / "assets" / rel, dirs_exist_ok=True)
        copied += sum(1 for f in src.rglob("*") if f.is_file())
    elif src.is_file():
        (DST / "assets" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, DST / "assets" / rel)
        copied += 1
    else:
        sys.exit(f"missing asset: {rel}")

size = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file()) / 1e6
print(f"{DST}: {len(PAGES)} pages, {copied} asset files, {size:.1f} MB")
