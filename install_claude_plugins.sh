#!/usr/bin/env bash
# =============================================================================
# install_claude_plugins.sh
# 어느 컴퓨터(macOS / Linux)에서든 Patrick의 Claude Code 플러그인 환경을 동일하게 재현.
# 사용법:  bash install_claude_plugins.sh
# 안전:    몇 번을 실행해도 안전(idempotent). 이미 설치된 건 건너뜀.
# =============================================================================
set -uo pipefail

# --- 재현할 환경 정의 (여기만 고치면 됨) ------------------------------------
# 형식:  "marketplace등록명|marketplace소스URL|plugin1 plugin2 ..."
MARKETPLACES=(
  "gptaku-plugins|https://github.com/fivetaku/gptaku_plugins.git|insane-search insane-research insane-design insane-review"
  "bkit-marketplace|https://github.com/popup-studio-ai/bkit-claude-code|bkit"
  "openai-codex|https://github.com/openai/codex-plugin-cc|codex"
  "superpowers-marketplace|https://github.com/obra/superpowers-marketplace|superpowers"
  "claude-plugins-official|https://github.com/anthropics/claude-plugins-official|context7"
  "halasu-plugins|https://github.com/halasu/claude-plugins-setup|shorts-maker"
)
# ---------------------------------------------------------------------------

green() { printf '\033[32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[33m%s\033[0m\n' "$1"; }
red() { printf '\033[31m%s\033[0m\n' "$1"; }

echo "==============================================="
echo "  Claude Code 플러그인 환경 재현 설치"
echo "==============================================="

# 1) claude CLI 존재 확인
if ! command -v claude >/dev/null 2>&1; then
  red "✗ 'claude' CLI를 찾을 수 없습니다. 먼저 Claude Code를 설치하세요:"
  echo "    https://docs.claude.com/claude-code  (또는 npm i -g @anthropic-ai/claude-code)"
  exit 1
fi
green "✓ claude CLI: $(claude --version 2>&1 | head -1)"

FAILED=0

# 2) marketplace 추가 + 플러그인 설치
for entry in "${MARKETPLACES[@]}"; do
  IFS='|' read -r mkt_name mkt_url plugins <<< "$entry"

  echo
  echo "── marketplace: $mkt_name ──"
  if claude plugin marketplace list 2>/dev/null | grep -q "$mkt_name"; then
    yellow "  · 이미 등록됨 (건너뜀)"
  else
    if claude plugin marketplace add "$mkt_url" >/dev/null 2>&1; then
      green "  ✓ 등록: $mkt_url"
    else
      red "  ✗ 등록 실패: $mkt_url"; FAILED=$((FAILED+1)); continue
    fi
  fi

  for p in $plugins; do
    if claude plugin list 2>/dev/null | grep -q "${p}@${mkt_name}"; then
      yellow "  · $p — 이미 설치됨"
    else
      if claude plugin install "${p}@${mkt_name}" >/dev/null 2>&1; then
        green "  ✓ 설치: $p"
      else
        red "  ✗ 설치 실패: $p"; FAILED=$((FAILED+1)); continue
      fi
    fi
    # 활성화 보장 (이미 켜져 있으면 무해)
    claude plugin enable "${p}@${mkt_name}" >/dev/null 2>&1 || true
  done
done

# 3) 개인 스킬 설치 (~/.claude/skills) — 저장소 clone에서 실행한 경우에만
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/skills" ]; then
  echo
  echo "── 개인 스킬 설치 ──"
  mkdir -p "$HOME/.claude/skills"
  for d in "$SCRIPT_DIR/skills"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    mkdir -p "$HOME/.claude/skills/$name"
    cp -R "$d". "$HOME/.claude/skills/$name/"
    green "  ✓ 스킬: $name"
  done
else
  yellow "· skills/ 폴더 없음 — 개인 스킬 설치 건너뜀 (curl 단독 실행 시 정상)"
fi

# 4) 결과 보고
echo
echo "==============================================="
echo "  현재 설치된 플러그인:"
claude plugin list 2>/dev/null | sed 's/^/    /'
echo "==============================================="
if [ "$FAILED" -eq 0 ]; then
  green "✅ 완료 — 모든 플러그인이 설치되었습니다."
else
  red "⚠ ${FAILED}개 항목 실패 — 위 로그를 확인하세요."
fi
echo
echo "다음 단계:"
echo "  1) 실행 중인 Claude Code 세션이 있으면  /reload-plugins  입력 (또는 재시작)"
echo "  2) (선택) insane-design/research 스크립트용 최신 Python:"
echo "        macOS:  brew install python@3.12"
echo "        Linux:  sudo apt install -y python3.12   # 또는 배포판 패키지"
