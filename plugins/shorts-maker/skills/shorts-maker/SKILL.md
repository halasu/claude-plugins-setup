---
name: shorts-maker
description: >
  롱폼 영상(YouTube URL 또는 로컬 영상 파일)에서 하이라이트/바이럴 구간을 골라
  9:16 세로 숏츠로 자동 컷하고 자막을 번인한다. yt-dlp + ffmpeg 로컬 파이프라인이라
  API 키가 필요 없고 Windows/macOS 모두에서 동작한다.
  Use when the user wants to turn a long video into short-form vertical clips.
  Korean triggers: 숏츠 만들어줘, 쇼츠 생성, 유튜브 하이라이트 뽑아줘,
  이 영상 짧게 잘라줘, 세로 영상으로 만들어줘, 릴스용으로 잘라줘.
  English triggers: make shorts, create vertical clips, extract highlights,
  cut this video into shorts, turn long video into reels.
---

# shorts-maker

롱폼 → 숏츠 파이프라인. 모든 스크립트는 `${CLAUDE_PLUGIN_ROOT}/scripts/` 에 있고
크로스플랫폼 Python 3(표준 라이브러리만) 이다. 외부 실행 파일은 `yt-dlp` 와 `ffmpeg`.

## 절차

### 0단계 — 의존성 점검 (항상 먼저)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.py"
```
- 종료 코드 1(누락)이면 **출력된 설치 명령을 사용자에게 그대로 안내하고 멈춘다.**
  (이 플러그인은 자동 설치를 하지 않는다. 사용자가 설치 후 재시도.)
- 종료 코드 0이면 다음 단계로.

### 1단계 — 소스 확보
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/fetch.py" "<YouTube URL 또는 로컬파일>" --outdir shorts_work --lang "ko.*,en.*"
```
- stdout 마지막 줄의 JSON(`video`, `srt`, `title`, `duration`)을 파싱한다.
- 로컬 파일이고 자막이 따로 있으면 `--srt <경로>` 를 추가한다.
- `srt` 가 null 이면: (a) 자막 없이 진행하거나, (b) 사용자에게 자막 생성(예: whisper) 여부를 물어본다. 자막 없이도 컷은 가능하다(자막 번인만 생략).

### 2단계 — 하이라이트 구간 선정 (Claude가 직접)
- `srt` 파일을 **Read** 로 열어 타임스탬프가 붙은 자막 전체를 읽는다.
- 다음 기준으로 숏츠 후보 구간을 3~5개 고른다:
  - 한 구간은 **15~60초**, 그 자체로 완결된 메시지(훅 → 핵심 → 마무리).
  - 강한 도입(질문/주장/반전), 정보 밀도, 감정/유머 피크, 인용하기 좋은 문장.
  - 문장 중간에서 자르지 말고 자연스러운 경계에서 start/end 를 잡는다.
- 각 후보를 표로 사용자에게 먼저 제시한다: `#, start, end, 길이, 제목(한 줄), 고른 이유`.
  많은 클립을 무단으로 렌더링하지 말고, 어떤 걸 만들지 확인받는다.

### 3단계 — 클립 렌더 (구간마다)
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/clip.py" \
  --input "<video>" --start <start> --end <end> \
  --out "out/clip1.mp4" --srt "<srt>" --mode crop
```
- `--mode crop`(기본): 중앙을 9:16으로 크롭해 화면을 꽉 채움(말하는 얼굴/중앙 피사체에 적합).
- `--mode pad`: 원본을 축소·중앙 배치 + 흐린 배경(가로 화면 내용 손실 없음). 사용자가 원하면 사용.
- `--srt` 를 넘기면 해당 구간 자막만 클립 기준(0초)으로 재정렬해 번인한다.
- 출력은 1080x1920, H.264/AAC, faststart mp4.

### 4단계 — 보고
- 만든 클립 파일 경로 목록과 각 클립의 구간·제목을 표로 보고한다.
- 필요 시 자막 스타일(`--style`), 모드, 구간을 조정해 재렌더한다.

## 주의
- 저작권: 사용자가 권리를 가졌거나 사용이 허용된 영상에만 쓴다. 무단 재업로드를 유도하지 않는다.
- 긴 원본은 다운로드/인코딩에 시간이 걸린다. 먼저 구간을 확정한 뒤 필요한 클립만 렌더한다.
- Windows에서 한글 자막 폰트가 깨지면 `--style` 에 `FontName=Malgun Gothic` 등을 추가한다(폰트 존재 시). 이 부분은 환경별로 `확인 필요`.
- yt-dlp/ffmpeg 버전에 따라 옵션이 다를 수 있으니 실패 시 stderr 를 읽고 조정한다.

## 파일
- `scripts/check_deps.py` — OS 감지 + 도구 점검/안내
- `scripts/fetch.py` — yt-dlp 다운로드(+자막) / 로컬 파일 수용, JSON 출력
- `scripts/clip.py` — ffmpeg 컷 + 9:16 + 자막 번인
