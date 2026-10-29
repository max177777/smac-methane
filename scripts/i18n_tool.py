"""
Maintenance tool for the site's translations (i18n/<lang>.json).

    python scripts/i18n_tool.py sync     # refresh generated English keys in i18n/en.json
    python scripts/i18n_tool.py check    # report missing / broken keys in every language

WHY "sync"
Some English text lives in code rather than in en.json — country policy
summaries (utils/policy_content.py POLICY), mitigation pathways (PATHWAYS),
quick-action bullets (utils/data_loader.py SECTOR_ACTIONS), Climate TRACE
sub-sector names, and under-construction notes. `sync` copies that text into
en.json under generated keys (policy.*, pathway.*, action.*, subsector.*, uc.*)
so translators see it, and so `check` can tell when the English changed and a
translation went stale. Run it after editing any of those sources.

WHAT "check" REPORTS (per language)
  missing   keys in en.json with no translation (the site falls back to English)
  extra     keys no longer in en.json (safe to delete)
  {fields}  a translation whose {placeholders} differ from English — would break
  <tags>    a translation whose HTML tags differ from English (<strong>, <em> …)
Exit code 1 if any placeholder/tag problem is found, so it can gate a commit.
"""

from __future__ import annotations

import importlib.util
import json
import re
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
LANGS = ["en", "zh", "es", "pt", "ko", "hi"]
GENERATED_PREFIXES = ("policy.", "pathway.", "action.", "subsector.", "uc.")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generated_english() -> dict:
    sys.path.insert(0, str(ROOT))
    pc = _load_module("policy_content", ROOT / "utils" / "policy_content.py")
    bsd = _load_module("build_subsector_data", ROOT / "scripts" / "build_subsector_data.py")
    # data_loader imports streamlit; only its plain dicts are needed
    from utils.data_loader import SECTOR_ACTIONS, UNDER_CONSTRUCTION  # noqa: E402

    out: dict[str, str] = {}
    for iso, p in pc.POLICY.items():
        out[f"policy.{iso}.summary"] = p.get("summary", "")
        for i, (n, d) in enumerate(p.get("policies", [])):
            out[f"policy.{iso}.{i}.name"] = n
            out[f"policy.{iso}.{i}.desc"] = d
    for iso, items in pc.PATHWAYS.items():
        for i, x in enumerate(items):
            out[f"pathway.{iso}.{i}.sector"] = x["sector"]
            out[f"pathway.{iso}.{i}.flag"] = x["flag"]
            for j, a in enumerate(x["actions"]):
                out[f"pathway.{iso}.{i}.action.{j}"] = a
    for sector, bullets in SECTOR_ACTIONS.items():
        for i, b in enumerate(bullets):
            out[f"action.{sector}.{i}"] = b
    subs = set(bsd.SUBSECTOR_TO_BROAD) | {"net-soil-organic-carbon"}
    for slug in sorted(subs):
        out[f"subsector.{slug}"] = " ".join(w.capitalize() for w in slug.split("-"))
    for (iso, loc), note in UNDER_CONSTRUCTION.items():
        out[f"uc.{iso}.{loc}"] = note
    return out


def _read(lang: str) -> dict:
    p = I18N / f"{lang}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _write(lang: str, data: dict) -> None:
    I18N.mkdir(exist_ok=True)
    (I18N / f"{lang}.json").write_text(
        json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")


def sync() -> None:
    en = _read("en")
    gen = generated_english()
    kept = {k: v for k, v in en.items() if not k.startswith(GENERATED_PREFIXES)}
    changed = [k for k in gen if en.get(k) != gen[k]]
    removed = [k for k in en if k.startswith(GENERATED_PREFIXES) and k not in gen]
    _write("en", {**kept, **gen})
    print(f"en.json: {len(gen)} generated keys ({len(changed)} new/changed, {len(removed)} removed)")
    for k in changed[:40]:
        print(f"  ~ {k}")
    if changed:
        print("Re-translate the keys above in the other languages (run `check`).")


_FIELD = string.Formatter()
_TAG = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>")


def _fields(s: str) -> set:
    try:
        return {f for _, f, _, _ in _FIELD.parse(s) if f}
    except ValueError:
        return {"<unparseable braces>"}


def _tags(s: str) -> list:
    return sorted(_TAG.findall(s))


def check() -> int:
    en = _read("en")
    bad = 0
    for lang in LANGS[1:]:
        tr = _read(lang)
        missing = [k for k in en if k not in tr]
        extra = [k for k in tr if k not in en]
        broken = []
        for k, v in tr.items():
            if k not in en:
                continue
            if _fields(v) != _fields(en[k]):
                broken.append((k, "fields", sorted(_fields(en[k])), sorted(_fields(v))))
            elif _tags(v) != _tags(en[k]):
                broken.append((k, "tags", _tags(en[k]), _tags(v)))
        bad += len(broken)
        print(f"[{lang}] {len(tr)}/{len(en)} keys · missing {len(missing)} · extra {len(extra)} "
              f"· broken {len(broken)}")
        for k in missing[:15]:
            print(f"    missing  {k}")
        for k, kind, want, got in broken[:15]:
            print(f"    {kind:7s} {k}: english {want} vs {got}")
    return 1 if bad else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "sync":
        sync()
    elif cmd == "check":
        sys.exit(check())
    else:
        sys.exit(__doc__)
