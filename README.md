# agentic-coding-plugin

A Google Antigravity companion plugin for high-quality software engineering and clean code review.

## Contents

- **`plugin.json`**: Plugin manifest declaring metadata and post-install scripts.
- **`pyproject.toml`**: Package specification and testing dependencies managed via `uv`.
- **`scripts/post_install.sh`**: Post-installation script that runs `uv sync` to provision `.venv`.
- **`agents/`**: Declarative subagent definitions for the 6-stage lifecycle (`@coding`, `@coding-clarify`, `@coding-specify`, `@coding-plan`, `@coding-develop`, `@coding-review`, `@coding-merge`).
- **`rules/AGENTS.md`**: Core engineering principles, testing constraints, and code style rules applied whenever this plugin is active.
- **`skills/coding-orchestrator/`**: Progressive skill orchestrating full-lifecycle software delivery.
- **`skills/clean-code-reviewer/`**: Progressive skill for auditing codebases for anti-patterns, code smells, and architecture boundaries.
- **`CONTRIBUTING.md`**: Contribution guidelines, development workflows, and checklists.
- **`LICENSE`**: MIT License.

---

## Architecture & Subagents

The `agentic-coding-plugin` coordinates a 6-stage development lifecycle:

1. **Clarification (`@coding-clarify`)**: Interrogates edge cases and dependencies one question at a time.
2. **Specification (`@coding-specify`)**: Authors `specification.md` with interactive approval gate.
3. **Planning (`@coding-plan`)**: Breaks down tasks and git branches in `plan.md` with interactive approval gate.
4. **Development (`@coding-develop`)**: Parallel implementation workers per repository.
5. **Review (`@coding-review`)**: Audits changes against specification and verifies tests.
6. **Release & Merge (`@coding-merge`)**: Merges locally or creates GitHub pull requests.

### Companion Plugins & Ecosystem Subagents

This plugin collaborates seamlessly with companion plugins in the `agentic` workspace:
- **`@coding-investigate`** ([`agentic-investigate-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-investigate-plugin)): Autonomous multi-repo root cause diagnosis and issue resolution.
- **`@coding-monitor`** ([`agentic-monitoring-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-monitoring-plugin)): Telemetry, log surveillance, and Docker stream observation.
- **`@coding-document`** ([`agentic-obsidian-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-obsidian-plugin)): Centralized Obsidian documentation vault maintenance.
- **`@coding-research`** ([`agentic-research-plugin`](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-research-plugin)): Autonomous web and literature research briefs.

---

## Contributing

See [CONTRIBUTING.md](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/CONTRIBUTING.md) for details on branching, subagent authoring, testing, and pull requests.

## License

This project is licensed under the [MIT License](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-coding-plugin/LICENSE).

---

## Installation & Setup

### 1. Provision Virtual Environment
Run the automated post-install script (requires `uv`):

```bash
./scripts/post_install.sh
```

This creates `.venv` and installs development dependencies.

### 2. Enable Plugin in Antigravity
```bash
agy plugin enable agentic-coding-plugin
```

### 3. Run Automated Tests
```bash
.venv/bin/pytest tests/test_plugin.py -v
```
