<#
=============================================================================
 install_claude_plugins.ps1
 어느 Windows PC에서든 Patrick의 Claude Code 플러그인 환경을 동일하게 재현.
 사용법:  powershell -ExecutionPolicy Bypass -File install_claude_plugins.ps1
 안전:    몇 번을 실행해도 안전(idempotent). 이미 설치된 건 건너뜀.
=============================================================================
#>

# --- 재현할 환경 정의 (여기만 고치면 됨) ------------------------------------
$Marketplaces = @(
  @{ Name = "gptaku-plugins";          Url = "https://github.com/fivetaku/gptaku_plugins.git";        Plugins = @("insane-search","insane-research","insane-design","insane-review") },
  @{ Name = "bkit-marketplace";        Url = "https://github.com/popup-studio-ai/bkit-claude-code";   Plugins = @("bkit") },
  @{ Name = "openai-codex";            Url = "https://github.com/openai/codex-plugin-cc";             Plugins = @("codex") },
  @{ Name = "superpowers-marketplace"; Url = "https://github.com/obra/superpowers-marketplace";       Plugins = @("superpowers") },
  @{ Name = "claude-plugins-official"; Url = "https://github.com/anthropics/claude-plugins-official"; Plugins = @("context7") },
  @{ Name = "halasu-plugins";          Url = "https://github.com/halasu/claude-plugins-setup";       Plugins = @("shorts-maker","orca-orchestration") }
)
# ---------------------------------------------------------------------------

Write-Host "==============================================="
Write-Host "  Claude Code 플러그인 환경 재현 설치 (Windows)"
Write-Host "==============================================="

# 1) claude CLI 존재 확인
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "✗ 'claude' CLI를 찾을 수 없습니다. 먼저 Claude Code를 설치하세요:" -ForegroundColor Red
  Write-Host "    https://docs.claude.com/claude-code  (또는 npm i -g @anthropic-ai/claude-code)"
  exit 1
}
Write-Host ("✓ claude CLI: " + ((claude --version 2>&1) | Select-Object -First 1)) -ForegroundColor Green

$Failed = 0
$mktList = (claude plugin marketplace list 2>$null) -join "`n"
$plgList = (claude plugin list 2>$null) -join "`n"

foreach ($m in $Marketplaces) {
  Write-Host ""
  Write-Host ("── marketplace: " + $m.Name + " ──")
  if ($mktList -match [regex]::Escape($m.Name)) {
    Write-Host "  · 이미 등록됨 (건너뜀)" -ForegroundColor Yellow
  } else {
    claude plugin marketplace add $m.Url *> $null
    if ($LASTEXITCODE -eq 0) { Write-Host ("  ✓ 등록: " + $m.Url) -ForegroundColor Green }
    else { Write-Host ("  ✗ 등록 실패: " + $m.Url) -ForegroundColor Red; $Failed++; continue }
  }

  foreach ($p in $m.Plugins) {
    $id = "$p@" + $m.Name
    if ($plgList -match [regex]::Escape($id)) {
      Write-Host ("  · $p — 이미 설치됨") -ForegroundColor Yellow
    } else {
      claude plugin install $id *> $null
      if ($LASTEXITCODE -eq 0) { Write-Host ("  ✓ 설치: $p") -ForegroundColor Green }
      else { Write-Host ("  ✗ 설치 실패: $p") -ForegroundColor Red; $Failed++; continue }
    }
    # 활성화 보장 (이미 켜져 있으면 무해)
    claude plugin enable $id *> $null
  }
}

# 3) 개인 스킬 설치 (~/.claude/skills) — 저장소 clone에서 실행한 경우에만
$SkillsSrc = Join-Path $PSScriptRoot "skills"
if (Test-Path $SkillsSrc) {
  Write-Host ""
  Write-Host "── 개인 스킬 설치 ──"
  $SkillsDest = Join-Path $env:USERPROFILE ".claude\skills"
  New-Item -ItemType Directory -Force $SkillsDest | Out-Null
  Get-ChildItem $SkillsSrc -Directory | ForEach-Object {
    Copy-Item $_.FullName $SkillsDest -Recurse -Force
    Write-Host ("  ✓ 스킬: " + $_.Name) -ForegroundColor Green
  }
} else {
  Write-Host "· skills/ 폴더 없음 — 개인 스킬 설치 건너뜀" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==============================================="
Write-Host "  현재 설치된 플러그인:"
(claude plugin list 2>$null) | ForEach-Object { "    $_" }
Write-Host "==============================================="
if ($Failed -eq 0) { Write-Host "✅ 완료 — 모든 플러그인이 설치되었습니다." -ForegroundColor Green }
else { Write-Host ("⚠ $Failed개 항목 실패 — 위 로그를 확인하세요.") -ForegroundColor Red }
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1) 실행 중인 Claude Code 세션이 있으면  /reload-plugins  입력 (또는 재시작)"
Write-Host "  2) (선택) 최신 Python:  winget install Python.Python.3.12"
