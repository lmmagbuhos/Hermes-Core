#!/usr/bin/env python3
"""Validate same-server DTT-AI to Hermes Core connectivity."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if REPO_SRC.exists():
    sys.path.insert(0, str(REPO_SRC))

from hermes_core.integrations.dtt_ai import validate_dtt_ai_environment  # noqa: E402


def main() -> None:
    args = parse_args()
    token = args.token if args.token is not None else os.getenv("HERMES_DTT_AI_SHARED_TOKEN", "")
    workspace_path = args.workspace_path or os.getenv("DTT_AI_WORKSPACE_PATH", "")
    if not workspace_path:
        print(
            json.dumps(
                {
                    "ok": False,
                    "checks": [
                        {
                            "name": "workspace_path",
                            "ok": False,
                            "detail": (
                                "Provide --workspace-path or set DTT_AI_WORKSPACE_PATH to the "
                                "same-server directory where DTT-AI writes generated projects."
                            ),
                        }
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(1)

    report = validate_dtt_ai_environment(
        hermes_url=args.hermes_url,
        token=token,
        workspace_path=workspace_path,
        project_name=args.project_name,
        timeout=args.timeout,
    )
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    raise SystemExit(0 if report.ok else 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate same-server DTT-AI to Hermes Core integration readiness."
    )
    parser.add_argument(
        "--hermes-url",
        default=os.getenv("HERMES_URL", "http://127.0.0.1:8000"),
        help="Hermes Core base URL. Defaults to HERMES_URL or http://127.0.0.1:8000.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Shared DTT-AI token. Defaults to HERMES_DTT_AI_SHARED_TOKEN when set.",
    )
    parser.add_argument(
        "--workspace-path",
        default=None,
        help="Same-server directory where DTT-AI writes generated projects.",
    )
    parser.add_argument("--project-name", default="HermesDttValidation")
    parser.add_argument("--timeout", type=float, default=10.0)
    return parser.parse_args()


if __name__ == "__main__":
    main()
