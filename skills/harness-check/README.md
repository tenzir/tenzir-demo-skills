# harness-check

Generate nearly all of the security-relevant OpenTelemetry an AI coding agent
emits, using the agent itself, so you can test whether your telemetry pipeline
collects, maps, and detects it.

## Overview

Modern coding agents such as Claude Code and Codex emit OpenTelemetry for
almost everything they do: model turns, tool calls and their allow or deny
decisions, file and process activity, web and MCP access, hook and plugin
lifecycle, subagents, schedulers, and session start and stop. `harness-check`
drives a real harness through that whole surface on purpose, so you can
confirm the events actually reach your collector and map correctly, for
example into OCSF.

The guiding rule is that every event is **real**. The skill never fabricates a
span, never hand-drives a protocol to imitate the agent, and never counts a
lookalike file or process action as a native lifecycle event. When a surface
cannot be exercised safely or is not available, it is recorded as an explicit
gap rather than faked.

Three layers produce the workload:

1. **Scripted probes** (plain Bash plus `python3`) generate dense file,
   command, process, failure, CLI, network, and security-shaped activity. They
   run under any agent, or by hand.
2. **Native agent probes** are actions the running agent performs through its
   own tools: native file and web tools, plan mode, subagents, schedulers,
   tool search, artifacts, and more.
3. **A real child session** is launched to generate startup-only telemetry the
   current session cannot emit after the fact: plugin load, hook registration
   and firing, MCP connection, session resume, transport choice, and the
   vendor API-error path.

A small number of events require a person, such as approving or declining a
permission dialog. Those are presented one at a time as guided manual steps.

## Install

Install it globally for both Codex and Claude Code:

```sh
npx skills@latest add git@github.com:zedoraps/harness-check.git \
  -g -a codex -a claude-code -y
```

Omit `-g` to install it only in the current project. To inspect what the CLI
discovers before installing:

```sh
npx skills@latest add git@github.com:zedoraps/harness-check.git --list
```

The SSH form lets Git use your existing GitHub credentials for this private
repository. The installing machine must have access to
`zedoraps/harness-check`.

As a manual project-local fallback, clone it once and link both harness
discovery paths to the clone:

```sh
git clone git@github.com:zedoraps/harness-check.git .agents/harness-check
mkdir -p .agents/skills .claude/skills
ln -s ../harness-check .agents/skills/harness-check
ln -s ../../.agents/harness-check .claude/skills/harness-check
```

## Run

### Claude Code

Invoke the installed slash command, or just ask for the skill by name:

```text
/harness-check
```

Claude runs the scripted workload and a real child Claude session on its own,
then walks you through only the unavoidable approval and permission-mode steps,
one per turn.

### Codex

Invoke the skill by name:

```text
$harness-check
```

Codex runs the scripted workload and a real ephemeral child Codex session
without a scope prompt, then guides you through the unavoidable approval
decisions one at a time.

### Agent-agnostic, by hand

The scripted core needs no agent at all:

```sh
scripts/run-all.sh              # all scripted probes, including network
scripts/run-all.sh --no-net     # skip outbound network
scripts/run-all.sh --clean      # remove the sandbox and exit
```

`run-all.sh` creates its own run directory. Every other stateful command
requires `HARNESS_CHECK_DIR` to point at a directory created by
`python3 scripts/harness_check.py new-run` and refuses to run without one, so
results from unrelated runs can never mix. The bookkeeping CLI exposes the
rest:

```sh
# report what can be probed here, right now (telemetry posture, tools, network)
python3 scripts/harness_check.py inventory --agent claude

# run one real child session for startup-only telemetry
python3 scripts/harness_check.py run-child --agent claude
python3 scripts/harness_check.py run-child --agent claude --transport grpc
python3 scripts/harness_check.py run-child --agent codex --sandbox workspace-write

# effective results for the current run (latest result per probe wins)
python3 scripts/harness_check.py summarize
```

Review [SKILL.md](SKILL.md) for the complete workflow and safety boundaries.

## Actions performed

### Scripted probes

| Probe | Activity it generates |
| --- | --- |
| `probe-files.sh` | File create, read, modify, rename, delete, nested directories, and the failure modes: bad parent, read after delete. |
| `probe-bash.sh` | Shell arguments, environment, pipes, exit codes, heredocs, quoting, timeout, background jobs, generated-script execution. |
| `probe-process.sh` | Process launch with image resolution, SIGTERM, SIGKILL, distinct exit codes, and a nested spawn. |
| `probe-cli.sh` | Resolves and runs real CLIs (`git`, `gh`, `jq`, `rg`, `python3`, `node`), outbound `curl`, and a `uvx` package download; read-only vendor auth-status checks. |
| `probe-security.sh` | Harmless, sandbox-confined commands matching real attack shapes (see below). |
| `probe-fixtures.sh` | Builds the material the native file probes are pointed at: text, a windowed file, an image, a PDF, a notebook. |

### Security-relevant shapes

`probe-security.sh` reproduces the structure of techniques a detection is meant
to flag, with marker payloads instead of real secrets and a loopback HTTP
fixture instead of the internet:

- credential-file and private-key reads;
- single-variable environment capture;
- base64 decode-and-execute;
- download-and-run and chmod-then-execute against the loopback fixture;
- a `.git/hooks` implant;
- an agent editing its own `.claude` and `.codex` configuration;
- a gated `sudo` escalation attempt;
- package-install attempts (dry run);
- a `git push` to a local bare remote (exfiltration shape).

The loopback fixture logs every request it serves, so egress is verifiable
server-side without leaving the host.

### Native agent probes

Performed by the running agent through its own tools, recorded only when the
harness actually exposes each one: native file read, edit, search, image, PDF,
and notebook access; web search and fetch; plan-mode enter and exit; bounded,
forked, and isolated subagents; background task output and stop; progress
monitoring; the full scheduler lifecycle; tool search; disposable private
artifacts including republish, comments, and a database round-trip; and one
local inter-agent message to a subagent the session spawned.

### Real child session

A non-interactive child `claude` or `codex` generates telemetry the main
session cannot emit retroactively:

- plugin load from a bundled disposable plugin;
- registration and firing of PreToolUse, PostToolUse, UserPromptSubmit,
  SessionStart, SessionEnd, Stop, and SubagentStop hooks, plus best-effort
  PreCompact and Notification hooks;
- hook-sourced and config-sourced tool denials, and a failing hook;
- MCP initialize, tool and resource and prompt listing, resource read, tool
  call, and notification channel, against a bundled stdio fixture server;
- a native fetch of the loopback fixture, verified server-side;
- session start and stop, and a session resume by fixed session id;
- the vendor API-error path, by pointing the API base URL at a closed loopback
  port so the first request fails without sending a usable credential;
- the content-inclusion posture run both redacted and verbose;
- for Codex, sandbox outcomes under each policy and `apply_patch` file ops.

Two side logs make receipt verifiable without trusting the model's transcript:
the MCP method log records which protocol operations the real client sent, and
the hook-event log records which hooks actually fired.

### Guided manual steps

A few events require a person and are presented one at a time: approving and
declining a real permission dialog; switching to a permission mode the agent
cannot set itself; typing a `!`-prefixed shell command; answering an
agent-raised question; and, only when you ask for one, approving a multi-agent
workflow.

## Output and verification

Every probe appends one tab-separated row to `probes.tsv` in the run directory:
timestamp, result, probe id, and detail. `summarize` collapses that to the
effective result per probe, so a `FAIL` later followed by a `PASS` reads as a
recovered attempt rather than a current failure.

Generating the workload and confirming collector receipt are separate
outcomes. Exporter configuration alone is not evidence of delivery. If a
telemetry query or capture endpoint is available, the skill looks for a fresh
sentinel such as `harness-check-shell-success` within the current run window
and records delivery as verified. Otherwise it states plainly that the workload
was generated but delivery was not checked.

## Requirements

- Bash and standard Unix command-line utilities.
- Python 3 for fixture generation and the disposable MCP and HTTP servers.
- An authenticated Codex or Claude Code installation for native and child
  harness probes.
- An OTLP exporter configured in the harness if telemetry output is required.

Optional tools (`git`, `gh`, `jq`, `rg`, `curl`, `node`, `pdftoppm`) are
inventoried at runtime and reported as conditional gaps when absent.

## Safety

- All file and process activity is confined to a run directory the skill owns;
  it refuses to operate on a non-owned, non-empty directory and guards against
  concurrent runs sharing one sandbox.
- Network probes target a bundled loopback fixture or well-known public
  endpoints; nothing real is uploaded off the host.
- The skill never logs in or out, mutates an account, changes credentials,
  installs software for real, messages another user's or a remote session, or
  prints secrets. Actions it cannot perform safely are recorded as gaps.

## Development

CI lints every shell script with ShellCheck, smoke-tests the MCP fixture
server's protocol surface, and runs the full agent-agnostic probe suite on
every push and pull request. Run the same checks locally from the skill
directory (the repository root when this skill is its own repo, or
`skills/harness-check/` when it is vendored into a multi-skill repo):

```sh
shellcheck -S warning scripts/*.sh
python3 tests/mcp-server-smoke.py
bash scripts/run-all.sh
```

The child-session probes (`python3 scripts/harness_check.py run-child`) need an
authenticated Claude Code or Codex CLI and therefore run only on a real
workstation, not in CI.

## Layout

```text
SKILL.md                 the operational contract the agent follows
README.md                this file
scripts/                 scripted probes, shared library, and the bookkeeping CLI
assets/                  disposable fixtures: MCP server, HTTP server, hooks, plugin, settings
reference/               the coverage matrix and per-area probe instructions
integrations/            the Claude Code command and Codex prompt entry points
agents/                  the Codex agent interface definition
tests/                   CI smoke tests
```
