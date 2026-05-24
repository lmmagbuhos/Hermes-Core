# Hermes Documentation

The Markdown files in this folder are the source of truth for Hermes architecture docs.

To generate the browsable standalone HTML version:

```bash
node tools/build-hermes-docs.mjs
```

Open `docs/hermes/index.html` in a browser to read the rendered documentation.

The generated page follows the standalone HTML pattern from `ThariqS/html-effectiveness`: no build step is needed to view it after generation, and it has no runtime dependencies.

For DTT-AI integration with the `larv:full` skill, start with `11-dtt-ai-handoff.md`, then use `10-dtt-ai-larv-skill-contract.md` as the detailed API contract.
