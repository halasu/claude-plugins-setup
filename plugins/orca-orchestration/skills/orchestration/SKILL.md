---
name: orchestration
description: >-
  Use Orca orchestration for structured multi-agent coordination inside the
  Orca IDE: dispatching tasks to claude/codex/other agent workers, waiting for
  worker_done/escalation, threaded ask/reply flows, task DAGs, decision gates,
  and A/B duels across worktrees. Requires the Orca desktop app with a running
  runtime. Do NOT use for full ownership handoffs the user does not want to
  supervise, or for ordinary terminal control.
---

# Orca Orchestration (cross-platform bootstrap)

This skill is a deliberately thin bootstrap, not the usage guide. The full,
version-matched orchestration reference lives inside the `orca` binary itself
and MUST be loaded at run time. Never rely on a cached or bundled copy of the
command surface — subcommands and flags change between Orca releases.

## 1. Resolve the CLI executable

Pick the executable once per session and reuse it everywhere:

1. If the `ORCA_CLI_COMMAND` environment variable is set, use its value
   (Orca exports this for managed WSL sessions).
2. Else, in a dev checkout that exposes `ORCA_DEV_REPO_ROOT`, use `orca-dev`.
3. Else, on **Linux outside an Orca-managed terminal**, use `orca-ide`.
   Never run bare `orca` there — it usually resolves to the GNOME Orca screen
   reader and starts speech on the user's machine.
4. Otherwise — including **Windows and macOS** — use `orca`.

If the selected executable fails to run, report its exact error and stop.
Do not silently fall through to a different executable.

## 2. Confirm the runtime, then load the real guide

```text
orca status --json          # runtime must be "ready"; start with: orca open --json
orca skills get orchestration
```

`skills get orchestration` prints the complete guide matched to the exact
binary that will execute your next commands: run/task creation, worker-start,
injected lifecycle preambles, worker_done authority, decision gates, and
coordinator loops. Read it before running any orchestration command, and do
not guess flags from memory.

If an older binary reports `skills get` as an unknown command, orient with
this bounded read-only set only, then tell the user that updating Orca
restores the full guide:

```text
orca status --json
orca orchestration task-list --json
orca terminal list --json
```

## 3. Field notes (verified on Windows; applies to macOS too)

- **Injection race after `worker-start`.** The dispatched prompt can land in
  the agent's composer without being submitted. Detect with
  `orca orchestration worker-read --dispatch <id> --limit 20 --json`:
  codex shows `[Pasted Content N chars]` near the composer; claude shows the
  `=== TASK ===` block sitting at the `❯` input line with no activity.
  Fix with a single `orca terminal send --terminal <handle> --enter --json`,
  then re-read to confirm (`source` switching from `terminal` to
  `transcript` proves the agent session is live).
- **One live dispatch per task.** To give the same work to two agents
  (A/B duel), create two tasks with identical specs.
- **Rolling waits, not polling.** Use
  `orca orchestration check --wait --types worker_done,escalation,question
  --timeout-ms <n> --json`, process every message in the returned delivery,
  then `--ack <delivery_id>` atomically with the next wait. A timeout or
  `count: 0` is a checkpoint, not a failure — real tasks run 15–60 minutes.
- **A valid `worker_done` auto-completes the task and dispatch.** Do not
  follow it with a manual `task-update --status completed`.

## Scope boundary

Use orchestration only when the user wants supervision, monitoring, waiting
for results, or DAG/gate coordination. Requests phrased as "hand off" /
"handover" / "give this to another agent or worktree" are full ownership
transfers — use plain Orca terminal/worktree commands and stop monitoring.
