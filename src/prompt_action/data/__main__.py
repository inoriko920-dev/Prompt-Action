from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from prompt_action.data.fixtures import build_corruption_fixture, is_corruption_descriptor
from prompt_action.data.repository import VersionRepository
from prompt_action.domain.validation import VersionValidator, parse_json_text
from prompt_action.services.version_engine import VersionEngine


def _root() -> Path:
    return Path.cwd().resolve()


def _dump(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(prog="python -m prompt_action.data")
    parser.add_argument("--root", type=Path, default=None)
    subs=parser.add_subparsers(dest="command",required=True)
    pval=subs.add_parser("validate"); pval.add_argument("--file",type=Path,default=None)
    subs.add_parser("inspect-active")
    pp=subs.add_parser("inspect-prompt"); pp.add_argument("prompt_id")
    pr=subs.add_parser("plan-release"); pr.add_argument("--primary",required=True); pr.add_argument("--sync",nargs="*",default=[])
    args=parser.parse_args(argv)
    root=(args.root or _root()).resolve(); repo=VersionRepository(root)
    try:
        if args.command=="validate":
            if args.file:
                text=(root/args.file).read_text(encoding="utf-8") if not args.file.is_absolute() else args.file.read_text(encoding="utf-8")
                document, syntax_report=parse_json_text(text)
                if document is None:
                    _dump(syntax_report.to_dict()); return 2
                if is_corruption_descriptor(document):
                    document=build_corruption_fixture(document, repo.load().document)
                report=VersionValidator(root).validate(document)
            else:
                report=repo.validate(repo.load())
            _dump(report.to_dict()); return 0 if report.is_valid else 2
        engine=VersionEngine(repo)
        if args.command=="inspect-active": _dump(engine.get_active_context()); return 0
        if args.command=="inspect-prompt": _dump(engine.get_prompt_history(args.prompt_id, repo.load().active_system)); return 0
        if args.command=="plan-release":
            plan=engine.plan_release({"primary":args.primary,"sync":args.sync}); _dump(plan.to_dict()); return 0
    except Exception as exc:
        _dump({"valid":False,"error_type":type(exc).__name__,"message":str(exc)}); return 2
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
