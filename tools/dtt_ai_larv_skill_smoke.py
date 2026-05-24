#!/usr/bin/env python3
"""Reference DTT-AI client for the Hermes larv:full reporting contract."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if REPO_SRC.exists():
    sys.path.insert(0, str(REPO_SRC))

from hermes_core.integrations.dtt_ai import DttAiEventIdFactory, DttAiHermesClient  # noqa: E402


def main() -> None:
    args = parse_args()
    token = args.token if args.token is not None else os.getenv("HERMES_DTT_AI_SHARED_TOKEN", "")
    event_prefix = args.event_prefix or f"dtt-smoke-{uuid4().hex}"

    with DttAiHermesClient(
        base_url=args.hermes_url,
        token=token,
        timeout=args.timeout,
        event_ids=DttAiEventIdFactory(event_prefix),
    ) as client:
        if args.mode in {"complete", "both"}:
            project_dir_context = project_dir_for_smoke(args.project_dir, args.project_name)
            with project_dir_context as project_dir:
                completed_summary = run_completed_flow(
                    client=client,
                    event_ids=DttAiEventIdFactory(f"{event_prefix}-complete"),
                    project_name=args.project_name,
                    external_session_id=f"{event_prefix}-complete-session",
                    project_dir=project_dir,
                )
                print(json.dumps(completed_summary, indent=2, sort_keys=True))

        if args.mode in {"failed", "both"}:
            failed_summary = run_failed_flow(
                client=client,
                event_ids=DttAiEventIdFactory(f"{event_prefix}-failed"),
                project_name=args.project_name,
                cwd=str(Path(args.project_dir).resolve()) if args.project_dir else os.getcwd(),
                external_session_id=f"{event_prefix}-failed-session",
            )
            print(json.dumps(failed_summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exercise the Hermes Core DTT-AI larv:full reporting contract."
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
    parser.add_argument("--project-name", default="AeroTrack")
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Readable artifact directory for completion flow. A temporary one is created if omitted.",
    )
    parser.add_argument(
        "--mode",
        choices=["complete", "failed", "both"],
        default="both",
        help="Which contract flow to exercise.",
    )
    parser.add_argument(
        "--event-prefix",
        default=None,
        help="Stable prefix for event_id values. Generated when omitted.",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    return parser.parse_args()


class project_dir_for_smoke:
    def __init__(self, project_dir: str | None, project_name: str):
        self.project_dir = Path(project_dir).resolve() if project_dir else None
        self.project_name = project_name
        self.temp_dir: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> str:
        if self.project_dir is not None:
            ensure_minimal_artifacts(self.project_dir)
            return str(self.project_dir)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="hermes-dtt-smoke-")
        project_dir = Path(self.temp_dir.name) / self.project_name
        ensure_minimal_artifacts(project_dir)
        return str(project_dir)

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.temp_dir is not None:
            self.temp_dir.cleanup()


def ensure_minimal_artifacts(project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    package_json = project_dir / "package.json"
    if not package_json.exists():
        package_json.write_text('{"packageManager":"pnpm@9.0.0"}\n', encoding="utf-8")


def run_completed_flow(
    *,
    client: DttAiHermesClient,
    event_ids: DttAiEventIdFactory,
    project_name: str,
    external_session_id: str,
    project_dir: str,
) -> dict[str, Any]:
    client.event_ids = event_ids
    session = client.start_larv_skill_session(
        project_name=project_name,
        external_session_id=external_session_id,
        cwd=project_dir,
    )
    client.record_output(
        session_id=session.id,
        sequence=1,
        stream="stdout",
        output="Which backend stack should be used?",
    )
    prompt = client.record_prompt_shown(
        session_id=session.id,
        prompt_id="stack-choice-001",
        prompt="Which backend stack should be used?",
        choices=["Fastify", "Laravel"],
        default="Fastify",
        is_required=True,
        metadata={"source": "larv:full", "phase": "stack-selection"},
    )
    answer = client.record_human_answer(
        session_id=session.id,
        prompt_id="stack-choice-001",
        answer="Fastify",
    )
    completed = client.complete_session(session_id=session.id, project_dir=project_dir)
    return {
        "flow": "complete",
        "session_id": session.id,
        "prompt_state": prompt["run"]["state"],
        "answer_state": answer["run"]["state"],
        "final_state": completed["run"]["state"],
        "project_dir": project_dir,
    }


def run_failed_flow(
    *,
    client: DttAiHermesClient,
    event_ids: DttAiEventIdFactory,
    project_name: str,
    cwd: str,
    external_session_id: str,
) -> dict[str, Any]:
    client.event_ids = event_ids
    session = client.start_larv_skill_session(
        project_name=project_name,
        external_session_id=external_session_id,
        cwd=cwd,
    )
    failed = client.fail_session(
        session_id=session.id,
        reason="DTT-AI smoke test simulated larv:full failure",
    )
    return {
        "flow": "failed",
        "session_id": session.id,
        "final_state": failed["run"]["state"],
        "session_status": failed["interactive_session"]["status"],
    }


if __name__ == "__main__":
    main()
