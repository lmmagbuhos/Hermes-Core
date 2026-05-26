# Scenario A Checkpoint

Date: 2026-05-26

## Verdict

Scenario A core runtime loop is proven.

```text
New Project page -> SSH/tmux Codex session -> larv:full -> real larv question -> DTT-AI answer UI -> same session continues -> generated website/sandbox output
```

## What Was Proven

```text
DTT-AI can run the New Project flow from the browser.
DTT-AI can start a real SSH/tmux runtime session.
DTT-AI can run codex --yolo in the project directory.
DTT-AI can invoke larv:full with the accepted trigger: larv:full.
DTT-AI can display real larv output.
DTT-AI can accept a human answer through the browser UI.
DTT-AI can send the answer back through the backend answer endpoint.
The same tmux/Codex session continues after the answer.
larv creates docs/larv/STATE.yaml.
The workflow produced website/sandbox output.
Hermes lifecycle reporting exists behind HERMES_ENABLED=true.
```

## Important Runtime Facts

```text
LARV_REMOTE_HOST=localhost works for same-server testing.
LARV_TRIGGER='larv:full' is correct.
/larv:full is not accepted by the current Codex TUI.
The SSH/tmux runtime is the active path.
Codex app-server is research-only for this scenario.
```

## Deferred Productization

These are important, but no longer block the core Scenario A proof:

```text
durable New Project session persistence
project cards
reconnect/resume after browser close or backend restart
better larv question display
chat/output filtering polish
loading states
runtime details panel refinements
final operator documentation
full completion-to-Hermes ProjectContextCandidate smoke with Hermes enabled
```

## Strategic Conclusion

The next highest-value proof is Scenario B: issue fixing.

Scenario A should remain available for follow-up productization, but continuing UI polish now would not reduce the largest remaining product risk.

