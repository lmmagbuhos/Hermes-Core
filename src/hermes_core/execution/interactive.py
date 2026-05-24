import errno
import os
import pty
import select
import signal
import time

from hermes_core.execution.contracts import PtyProcess


class PtyInteractiveRunner:
    def __init__(self) -> None:
        self._exit_codes: dict[int, int] = {}

    def start(self, command: list[str], cwd: str) -> PtyProcess:
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd)
            os.execvp(command[0], command)
        os.set_blocking(fd, False)
        return PtyProcess(pid=pid, fd=fd, command=command, cwd=cwd)

    def read_available(self, process: PtyProcess, timeout: float = 0.2) -> str:
        chunks: list[str] = []
        end_at = time.monotonic() + timeout
        while time.monotonic() < end_at:
            readable, _, _ = select.select([process.fd], [], [], 0.05)
            if not readable:
                continue
            try:
                data = os.read(process.fd, 4096)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not data:
                break
            chunks.append(data.decode(errors="replace"))
        return "".join(chunks)

    def write_stdin(self, process: PtyProcess, value: str) -> None:
        os.write(process.fd, value.encode())

    def poll(self, process: PtyProcess) -> int | None:
        if process.pid in self._exit_codes:
            return self._exit_codes[process.pid]

        try:
            pid, status = os.waitpid(process.pid, os.WNOHANG)
        except ChildProcessError:
            return self._exit_codes.get(process.pid, 0)

        if pid == 0:
            return None
        if os.WIFEXITED(status):
            exit_code = os.WEXITSTATUS(status)
            self._exit_codes[process.pid] = exit_code
            return exit_code
        if os.WIFSIGNALED(status):
            exit_code = 128 + os.WTERMSIG(status)
            self._exit_codes[process.pid] = exit_code
            return exit_code
        self._exit_codes[process.pid] = status
        return status

    def read_until_complete(self, process: PtyProcess, timeout: float = 30) -> str:
        output: list[str] = []
        end_at = time.monotonic() + timeout
        while time.monotonic() < end_at:
            output.append(self.read_available(process, timeout=0.2))
            if self.poll(process) is not None:
                output.append(self.read_available(process, timeout=0.2))
                return "".join(output)
        raise TimeoutError(f"Process did not complete before {timeout} seconds")

    def terminate(self, process: PtyProcess) -> None:
        os.kill(process.pid, signal.SIGTERM)
