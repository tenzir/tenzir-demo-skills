# 🎬 Tenzir Demo Skills

Skills used to demo Tenzir functionality, built on the
[Agent Skills](https://agentskills.io) standard.

## 🗂️ Skills

- `harness-check`: Generate nearly all security-relevant native OpenTelemetry
  activity from a real Claude Code or Codex harness — native tools, model
  turns, files, commands, processes, sandbox decisions, web, MCP, skills,
  plugins, hooks, subagents, schedulers, and approvals — to test agent
  telemetry pipelines without fabricating events

## 📦 Install

### With `npx skills`

Install all skills into the current project:

```bash
npx skills add tenzir/tenzir-demo-skills
```

Or install globally:

```bash
npx skills add -g tenzir/tenzir-demo-skills
```

Install a specific skill into the current project, for example:

```bash
npx skills add tenzir/tenzir-demo-skills@harness-check
```

This repository is private, so the installing machine must have access to
`tenzir/tenzir-demo-skills`. The SSH form lets Git use your existing GitHub
credentials:

```bash
npx skills add git@github.com:tenzir/tenzir-demo-skills.git \
  -g -a codex -a claude-code -y
```

## 📄 License

[Apache-2.0](LICENSE)
