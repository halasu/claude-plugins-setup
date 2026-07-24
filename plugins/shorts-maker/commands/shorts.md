---
name: shorts
description: "롱폼 영상(YouTube URL/로컬 파일)에서 하이라이트를 골라 9:16 숏츠로 자동 생성"
argument-hint: "[YouTube URL | 로컬 영상 경로]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---

# /shorts

입력 `$ARGUMENTS` (YouTube URL 또는 로컬 영상 파일)에서 숏츠를 만든다.
`shorts-maker` 스킬의 절차를 그대로 따른다:

1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.py"` — 의존성 점검. 누락이면 설치 안내 후 중단.
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/fetch.py" "$ARGUMENTS" --outdir shorts_work` — 소스+자막 확보, JSON 파싱.
3. 자막(srt)을 Read 로 읽고 하이라이트 구간 3~5개를 골라 **표로 먼저 제시**한다(무단 대량 렌더 금지).
4. 사용자가 고른 구간마다 `python "${CLAUDE_PLUGIN_ROOT}/scripts/clip.py" --input <video> --start <s> --end <e> --out out/clipN.mp4 --srt <srt> --mode crop` 로 렌더.
5. 결과 클립 경로·구간을 표로 보고.

인자가 없으면 사용자에게 YouTube URL 또는 로컬 영상 경로를 물어본다.
