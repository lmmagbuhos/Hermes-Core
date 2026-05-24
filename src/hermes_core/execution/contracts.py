from pydantic import BaseModel


class CommandResult(BaseModel):
    command: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str


class InteractiveSession(BaseModel):
    id: str
    run_id: int
    command: list[str]
    cwd: str
    status: str
    transcript_ref: str
    last_prompt: str | None = None

