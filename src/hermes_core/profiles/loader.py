from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AgentProfile(BaseModel):
    id: str
    name: str
    type: str
    version: int
    role_contract: str
    responsibilities: list[str]
    non_responsibilities: list[str]
    allowed_tools: list[str]
    denied_tools: list[str]
    memory_sources: list[str]
    path_scopes: list[str] = Field(default_factory=list)
    learning_rules: dict[str, Any] = Field(default_factory=dict)
    confidence_rubric: dict[str, Any] = Field(default_factory=dict)
    escalation_rules: list[str] = Field(default_factory=list)
    review_rules: list[str] = Field(default_factory=list)
    communication_style: str
    model_config_data: dict[str, Any] = Field(default_factory=dict, alias="model_config")

    @property
    def model_provider(self) -> str:
        provider = self.model_config_data.get("provider")
        if not isinstance(provider, str) or not provider:
            raise ValueError(f"Profile {self.id} is missing model_config.provider")
        return provider


def load_profile(path: str | Path) -> AgentProfile:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return AgentProfile.model_validate(data)


def load_profiles(directory: str | Path) -> list[AgentProfile]:
    paths = sorted(Path(directory).glob("*.yaml"))
    return [load_profile(path) for path in paths]

