import json
from pathlib import Path

from pydantic import BaseModel


class HermesProjectBlueprint(BaseModel):
    project_name: str
    project_dir: str
    package_manager: str | None
    implementation_slices: list[str]
    transcript_summary: str


def ingest_project_artifacts(project_dir: Path, transcript: str) -> HermesProjectBlueprint:
    package_manager = _detect_package_manager(project_dir)
    slices = sorted(
        str(path.relative_to(project_dir)) for path in project_dir.glob("docs/Handsoff/slice-*.md")
    )
    return HermesProjectBlueprint(
        project_name=project_dir.name,
        project_dir=str(project_dir),
        package_manager=package_manager,
        implementation_slices=slices,
        transcript_summary=transcript.strip(),
    )


def _detect_package_manager(project_dir: Path) -> str | None:
    package_json = project_dir / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text(encoding="utf-8"))
        package_manager = data.get("packageManager")
        if isinstance(package_manager, str) and package_manager:
            return package_manager.split("@", maxsplit=1)[0]
    if (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_dir / "yarn.lock").exists():
        return "yarn"
    if (project_dir / "package-lock.json").exists():
        return "npm"
    return None
