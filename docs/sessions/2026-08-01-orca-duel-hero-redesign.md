# Orca A/B 듀얼 세션 기록 — Hero.tsx 다크 테마 리디자인 (claude vs codex)

- **일시:** 2026-08-01 (KST) / 2026-07-31 15:34–15:38 UTC
- **환경:** Windows 11, Orca 1.4.162, Claude Code (coordinator = Claude Fable 5)
- **저장소:** `my-app` (단일 브랜치 `master`, Hero.tsx 커밋됨)
- **태스크 (양쪽 동일):** `components/Hero.tsx의 히어로 섹션을 다크 테마로 리디자인해줘. 어두운 배경 + 그라데이션. Hero.tsx만 수정해. 디자인 방향은 자유롭게.`
- **결과:** 두 워커 모두 약 2.5분 만에 `worker_done`(성공). 머지 없이 두 worktree 보존, 사용자가 승자 선택.

## 실행 흐름

```text
1. Preflight
   orca status --json                        # runtime "ready" 확인
   git branch -a / git ls-files components/  # Hero.tsx가 기본 브랜치에 커밋되어 있는지 확인

2. Run + Task (태스크당 라이브 디스패치 1개 → 워커 2명이면 태스크 2개)
   orca orchestration run-create --objective "A/B duel: Hero.tsx 히어로 섹션 다크 테마 리디자인 (claude vs codex)" --json
     → run_ac210bfe8933
   orca orchestration task-create --spec "<태스크 + 가드레일>" --json   # ×2
     → task_fd247fb0f57a (claude용), task_cc1bee4cf1ea (codex용)
   # 스펙에 덧붙인 가드레일: "Work only in your own worktree. Do NOT git commit
   #  unless the task says to. When done, report via worker_done with files modified."

3. Worker 시작 (각자 새 child worktree — 같은 파일을 수정하므로 격리 필수)
   orca orchestration worker-start --task task_fd247fb0f57a --worktree new-child --name duel-claude --agent claude --setup run --json
     → dispatch ctx_0d4ac6e1fb07, worktree ~/orca/workspaces/my-app/duel-claude
   orca orchestration worker-start --task task_cc1bee4cf1ea --worktree new-child --name duel-codex --agent codex --setup run --json
     → dispatch ctx_f1f85fe9c7f2, worktree ~/orca/workspaces/my-app/duel-codex
   # git worktree 락 경합을 피해 순차 실행

4. 인젝션 레이스 감지 + 해결 (이번 세션에서 양쪽 모두 발생!)
   orca orchestration worker-read --dispatch <id> --limit 20 --json
   # 증상: codex → 컴포저에 "[Pasted Content 4013 chars]" 미전송 상태
   #        claude → ❯ 입력줄에 === TASK === 블록이 떠 있고 활동 없음
   orca terminal send --terminal <handle> --enter --json   # 각 1회
   # 재확인: worker-read의 source가 "terminal" → "transcript"로 바뀌면 세션 라이브 확정

5. 롤링 대기 (sleep/poll 금지)
   orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 540000 --json
     → claude worker_done (15:37:36 UTC, succeeded)
   orca orchestration check --ack delivery_36620a83c0d1 --wait --types worker_done,escalation,question --timeout-ms 540000 --json
     → codex worker_done (15:38:02 UTC, succeeded)     # ack과 다음 대기를 원자적으로
   orca orchestration check --ack delivery_a134b75ea3a3 --json   # 마지막 ack

6. 비교 (coordinator는 읽기만, 절대 수정 금지)
   git -C <worktree> branch --show-current / diff --stat / status --short
   + 양쪽 Hero.tsx 전문 읽기
```

## 결과 비교

| | claude (duel-claude) | codex (duel-codex) |
|---|---|---|
| diff | +191 / −4 | +142 / −4 |
| 스타일링 방식 | `<style>` 태그 임베드 + BEM 클래스(`hero__*`) | 순수 인라인 `style` 객체 |
| 배경 | 딥 네이비 `#05060f` + radial 그라데이션 3겹 + 마스크된 그리드 오버레이 + 떠다니는 블러 오브 2개(keyframe) | `#030712→#111827` 대각선 그라데이션 + radial 악센트 2개 + 중앙 대형 블러 글로우 |
| 타이포 | clamp() 반응형, 그라데이션 텍스트 헤드라인 | 최대 7.75rem 초대형 헤드라인, 자간 −0.065em, 그라데이션 스팬 |
| 인터랙션 | hover/active 트랜지션, `prefers-reduced-motion` 대응 | hover 없음 (인라인 스타일 한계) |
| 카피 | 원본 유지 + 서브카피 확장 | **전면 재작성** ("Welcome to My App" → "Ideas that move at your speed.") |
| 범위 준수 | Hero.tsx만, 커밋 없음 ✓ | Hero.tsx만, 커밋 없음 ✓ |
| 한 줄 평 | 분위기·디테일 풍부한 "프로덕트 히어로" | 타이포 중심의 과감한 "에디토리얼 히어로" |

**트레이드오프:** claude는 접근성·모션·원본 카피 보존이 강점이나 `<style>` 태그로 전역 클래스가 새고 중복 렌더 시 스타일이 중복 주입됨. codex는 전역 오염이 없고 첫인상이 강렬하나 hover 피드백이 전무하고 브랜드 카피를 임의 변경("디자인 방향 자유"의 해석 차이).

## 교훈 / Lessons

1. **인젝션 레이스는 실재한다.** `worker-start`가 `input_accepted`를 반환해도 프롬프트가 컴포저에 미전송 상태로 남을 수 있다. 시작 직후 반드시 `worker-read`로 확인하고, 걸렸으면 `terminal send --enter` 1회로 해결. 이번엔 claude/codex **둘 다** 걸렸다.
2. **태스크당 라이브 디스패치는 1개.** A/B 듀얼은 동일 스펙 태스크 2개로.
3. **같은 파일을 두 워커가 수정하면 worktree 격리 필수.** `new-child`로 각자 생성 (git 락 경합 방지를 위해 순차 시작).
4. **유효한 `worker_done`은 태스크/디스패치를 자동 완료.** 수동 `task-update` 불필요.
5. **가이드는 바이너리에서.** 커맨드 표면은 릴리스마다 바뀌므로 `orca skills get orchestration`으로 실행 시점에 로드. 이 원칙이 orca-orchestration 플러그인의 핵심 설계다.
6. **ack은 다음 대기와 원자적으로.** `check --ack <delivery_id> --wait ...` 한 방이 메시지 유실 창을 없앤다.
7. **`.bkit/` 같은 세션 훅 부산물이 worktree에 생길 수 있다.** 범위 위반으로 오판하지 말 것 (untracked 도구 상태 파일).
