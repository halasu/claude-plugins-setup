# orca-orchestration

[Orca](https://orca.dev) 멀티에이전트 IDE의 **오케스트레이션**(멀티에이전트 조율)을 Claude Code에서 쓰게 해주는 플러그인. Windows / macOS 크로스플랫폼.

Use Orca's multi-agent orchestration (task dispatch, `worker_done` waits, A/B duels) from Claude Code, on Windows and macOS.

## 구성 / What's inside

| 구성요소 | 이름 | 역할 |
|----------|------|------|
| Skill | `orca-orchestration:orchestration` | CLI 실행 파일 해석 규칙(Windows/macOS는 `orca`, Linux는 `orca-ide`) + `orca skills get orchestration`으로 **실행 시점에 바이너리가 제공하는 버전 매칭 가이드**를 로드하는 부트스트랩. 검증된 현장 노트(인젝션 레이스 해결법 등) 포함 |
| Command | `/orca-duel <태스크>` | 같은 태스크를 claude/codex 워커에 각각 새 worktree로 병렬 디스패치 → 둘 다 `worker_done` 대기 → 결과 비교 리포트 (머지는 사용자 선택) |

**설계 원칙:** 오케스트레이션 커맨드 표면(서브커맨드/플래그)은 Orca 릴리스마다 바뀝니다. 이 플러그인은 가이드 전문을 번들하지 않고, 실제로 명령을 실행할 `orca` 바이너리에게 가이드를 물어봅니다(`orca skills get orchestration`). 그래서 버전이 어긋날 수 없습니다.

## 전제조건 / Prerequisites

1. [Orca](https://orca.dev) 데스크톱 앱 설치 (Windows / macOS)
2. `orca` CLI가 PATH에 있을 것 (앱 설치 시 기본 제공)
3. Orca **Settings > Experimental**에서 orchestration 기능 활성화
4. 런타임 실행 중: `orca status --json`이 `"state": "ready"` (아니면 `orca open --json`)

## 설치 / Install

```text
/plugin marketplace add https://github.com/halasu/claude-plugins-setup
/plugin install orca-orchestration@halasu-plugins
/reload-plugins
```

또는 이 저장소의 부트스트랩 스크립트(`install_claude_plugins.sh` / `.ps1`)를 실행하면 함께 설치됩니다.

## 사용 / Usage

```text
# A/B 듀얼: 같은 태스크를 claude vs codex에게 주고 결과 비교
/orca-duel components/Hero.tsx의 히어로 섹션을 다크 테마로 리디자인해줘. Hero.tsx만 수정해.

# 일반 오케스트레이션: 자연어로 요청하면 스킬이 트리거됨
"이 작업을 워커 두 명한테 나눠서 디스패치하고 완료까지 감독해줘"
```

듀얼이 끝나면 두 worktree(`duel-claude` / `duel-codex`)가 그대로 남고, 비교 리포트를 보고 사용자가 승자를 고릅니다. 플러그인은 절대 머지하지 않습니다.

## 실전 기록 / Field record

이 플러그인의 워크플로는 실제 세션에서 검증되었습니다:
[docs/sessions/2026-08-01-orca-duel-hero-redesign.md](../../docs/sessions/2026-08-01-orca-duel-hero-redesign.md)
— Hero 컴포넌트 다크 테마 리디자인을 claude vs codex로 듀얼, 약 3분 만에 양쪽 `worker_done` 수신, 인젝션 레이스 함정과 해결 과정 포함.

## License

MIT
