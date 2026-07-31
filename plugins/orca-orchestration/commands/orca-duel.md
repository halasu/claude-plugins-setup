---
description: Orca A/B 듀얼 — 같은 태스크를 claude/codex 워커에 각각 새 worktree로 병렬 디스패치하고 결과를 비교 (머지는 사용자 선택)
argument-hint: <두 워커에게 줄 동일 태스크 설명>
---

Run a supervised Orca A/B duel: dispatch the SAME task to a claude worker and a codex worker, each in its own new worktree, wait for both `worker_done`, then compare — never merge.

First invoke this plugin's `orchestration` skill (`orca-orchestration:orchestration`) with the Skill tool, resolve the CLI executable per its rules, and load the version-matched guide (`orca skills get orchestration`). Then:

1. **Preflight**
   - `orca status --json` must show a ready runtime (start with `orca open --json` if needed).
   - Task text = `$ARGUMENTS`. If empty, ask the user what task to duel.
   - If the task targets specific files (e.g. `components/Hero.tsx`), verify they exist in this repo first. If they only exist on the current feature branch (not the repo default base), the new worktrees must be based on the current branch — state this and pass the branch context explicitly.

2. **Run + Tasks**
   - `orca orchestration run-create --objective "A/B duel: <task 한 줄 요약>" --json`
   - Create TWO tasks with the identical spec (a task allows only one live dispatch, so one task per worker). Append to each spec: "Work only in your own worktree. Do NOT git commit unless the task says to. When done, report via worker_done with files modified."

3. **Workers — separate new worktrees (required: both edit the same files)**
   - `orca orchestration worker-start --task <task_A> --worktree new-child --name duel-claude --agent claude --setup run --json`
   - `orca orchestration worker-start --task <task_B> --worktree new-child --name duel-codex --agent codex --setup run --json`
   - Use `new-top-level` instead of `new-child` only if the duel is unrelated to the current branch's work.
   - Read each receipt; a failed start → inspect `stage`/`effects`, do not blind-retry.

4. **Injection race check (known pitfall)**
   - After each start, `orca orchestration worker-read --dispatch <id> --limit 20 --json` (or `orca terminal read`).
   - If the prompt is sitting unsent in the composer — "[Pasted Content N chars]" (codex) or the TASK block visible at the `❯` input line with no activity (claude) — send `orca terminal send --terminal <handle> --enter --json` once, then re-read to confirm submission (`source: "transcript"` confirms the agent session is live).

5. **Wait until BOTH dispatches settle**
   - Rolling `orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 540000 --json`.
   - Process every message, `--ack <delivery_id>` atomically with the next wait, answer `question` messages with `orca orchestration reply`.
   - Timeout/`count:0` is a checkpoint, not failure: inspect `worker-show`/`terminal read`; if alive, keep waiting. Real tasks can take 15–60 min.

6. **Compare (coordinator reads, never edits)**
   - For each worktree: `git -C <worktreePath> diff --stat` and `git -C <worktreePath> diff`, plus read the modified files.
   - Summarize per worker: design/approach choices, code quality, scope discipline (did it touch only allowed files?), size of change.
   - Then a difference summary: what each did differently and trade-offs.

7. **Report — no merge**
   - Table: worker | worktree path | branch | files modified | one-line verdict.
   - Tell the user how to open each worktree to view results, and that they pick the winner. Do NOT merge, cherry-pick, or edit files yourself; leave both worktrees intact until the user decides.
