# claude-plugins-setup

어느 컴퓨터(macOS · Linux · Windows)에서든 **한 번의 실행으로 동일한 Claude Code 플러그인 환경**을 재현하는 부트스트랩 스크립트.

Reproduce the same [Claude Code](https://docs.claude.com/claude-code) plugin environment on any machine with a single command.

## 왜 필요한가 / Why

Claude Code의 스킬·에이전트·플러그인은 계정(클라우드)이 아니라 **각 컴퓨터의 로컬 `~/.claude/`** 에 저장됩니다. 계정 로그인만으로는 기기 간 동기화가 안 되므로, 새 기기마다 설치가 필요합니다. 이 스크립트가 그 설치를 자동화합니다.

Claude Code stores skills/agents/plugins locally per machine, not in your account. This script automates reinstalling them on a fresh machine.

## 사용법 / Usage

**전제:** [Claude Code](https://docs.claude.com/claude-code)가 설치되어 있어야 합니다 (`claude` CLI).

### macOS / Linux
```bash
bash install_claude_plugins.sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File install_claude_plugins.ps1
```

> **Windows 참고:** `install_claude_plugins.ps1` 은 **UTF-8 with BOM** 으로 저장되어 있습니다. Windows PowerShell 5.1(Desktop)이 BOM 없는 UTF-8 파일의 한글 문자열을 시스템 코드페이지(cp949)로 잘못 읽어 `ParserError` 로 실행이 실패하는 문제를 피하기 위함입니다. 파일을 수정할 때 인코딩을 UTF-8(BOM 포함)으로 유지하세요. PowerShell 7(`pwsh`)에서는 BOM 없이도 정상 동작합니다.

실행 후 Claude Code 세션에서 `/reload-plugins` 를 입력하거나 재시작하세요.

## 무엇을 설치하나 / What it installs

| Plugin | Marketplace |
|--------|-------------|
| insane-search / insane-research / insane-design / insane-review | [fivetaku/gptaku_plugins](https://github.com/fivetaku/gptaku_plugins) |
| bkit | [popup-studio-ai/bkit-claude-code](https://github.com/popup-studio-ai/bkit-claude-code) |
| codex | [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) |
| superpowers | [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) |
| context7 | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| **shorts-maker** (자체 제작) | 이 저장소 (`halasu-plugins` 마켓플레이스) — [plugins/shorts-maker](plugins/shorts-maker) |

설치할 플러그인을 바꾸려면 스크립트 상단의 목록(`MARKETPLACES` / `$Marketplaces`)만 수정하면 됩니다.

### 이 저장소 = 마켓플레이스(`halasu-plugins`)이기도 함

이 저장소는 부트스트랩 스크립트뿐 아니라 **자체 제작 Claude Code 플러그인**도 담고 있어, 그 자체가 마켓플레이스입니다. 부트스트랩 없이 플러그인만 설치하려면:

```text
/plugin marketplace add https://github.com/halasu/claude-plugins-setup
/plugin install shorts-maker@halasu-plugins
/reload-plugins
```

- **shorts-maker** — 롱폼 영상(YouTube URL/로컬 파일)에서 하이라이트를 골라 9:16 숏츠로 자동 컷·자막 번인. `yt-dlp`+`ffmpeg` 로컬, API 키 불필요, Windows/macOS 크로스플랫폼. → [plugins/shorts-maker/README.md](plugins/shorts-maker/README.md)

## 개인 스킬 / Personal skills

저장소를 clone해서 설치 스크립트를 실행하면 `skills/` 아래의 개인 스킬도 `~/.claude/skills/`에 함께 설치됩니다. (`curl | bash` 단독 실행 시에는 건너뜁니다)

| Skill | 용도 |
|-------|------|
| [blogger-publish](skills/blogger-publish/SKILL.md) | LED 블로그(Blogger) 초안 작성 → API 업로드 → 검토 발행 파이프라인. 인증 파일은 스킬에 포함되지 않으며 기기별 OAuth 설정이 별도로 필요합니다. |

## 특징 / Features

- **Idempotent** — 몇 번을 실행해도 안전. 이미 설치된 건 건너뜁니다.
- 설치 후 자동 활성화(enable) 보장.
- 비밀정보(토큰·키) 없음 — 공개 저장소 URL만 참조합니다.

## 보안 / Security

`curl … | bash` 한 줄 설치는 편하지만, **원격 스크립트를 그대로 실행**합니다. 신중하게 쓰려면 먼저 내용을 확인한 뒤 실행하세요:

```bash
# 1) 내려받아 내용 확인
curl -sL https://raw.githubusercontent.com/halasu/claude-plugins-setup/main/install_claude_plugins.sh -o install.sh
less install.sh          # 내용 검토
# 2) 확인 후 실행
bash install.sh
```

이 저장소를 신뢰의 기준점으로 쓰므로, **소유 계정에 2단계 인증(2FA)을 반드시 활성화**하세요. 이 스크립트는 비밀정보를 담지 않으며, 공개 저장소 URL만 참조하고 어떤 플러그인도 재배포하지 않습니다.

If you prefer not to pipe to a shell, download and review the script first, then run it. Keep 2FA enabled on the account that owns this repo.

## License

MIT — see [LICENSE](LICENSE).

플러그인 자체의 저작권/라이선스는 각 제작자에게 있습니다. 이 저장소는 설치 편의를 위한 스크립트만 제공하며, 어떤 플러그인도 재배포하지 않습니다.
Each plugin belongs to its respective author; this repo only automates installation and redistributes nothing.
