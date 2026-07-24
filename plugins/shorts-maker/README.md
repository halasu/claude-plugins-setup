# shorts-maker

롱폼 영상(YouTube URL 또는 로컬 파일)에서 하이라이트 구간을 골라 **9:16 세로 숏츠**로 자동 컷하고 자막을 번인하는 Claude Code 플러그인.

- **로컬·무료**: `yt-dlp` + `ffmpeg` 만 사용. 외부 API 키 불필요.
- **크로스플랫폼**: Windows / macOS(및 Linux). 모든 로직은 표준 라이브러리만 쓰는 Python 3.
- **Claude가 편집자**: 자막(타임스탬프)을 읽고 바이럴 구간을 직접 선정 → ffmpeg로 렌더.

## 사전 요구사항

| 도구 | 설치 (Windows) | 설치 (macOS) |
|------|----------------|--------------|
| ffmpeg | `winget install --id Gyan.FFmpeg -e` | `brew install ffmpeg` |
| yt-dlp | `winget install --id yt-dlp.yt-dlp -e` | `brew install yt-dlp` |
| Python 3 | 이미 대부분 설치됨 | 이미 대부분 설치됨 |

설치 상태는 `python scripts/check_deps.py` 로 점검. (플러그인은 자동 설치하지 않고 안내만 한다.)

## 설치

이 저장소는 그 자체가 Claude Code 마켓플레이스(`halasu-plugins`)다.

```text
/plugin marketplace add https://github.com/halasu/claude-plugins-setup
/plugin install shorts-maker@halasu-plugins
/reload-plugins
```

## 사용

Claude Code에서:

```text
/shorts https://youtu.be/XXXXXXXXXXX
```

또는 자연어로: "이 유튜브 영상 하이라이트 숏츠로 만들어줘 <URL>".

동작:
1. 의존성 점검(없으면 설치 안내).
2. `yt-dlp` 로 영상 + 자막(srt) 다운로드.
3. Claude가 자막을 읽고 하이라이트 구간 3~5개를 골라 **표로 제안**.
4. 고른 구간마다 `ffmpeg` 로 9:16 컷 + 자막 번인 → `out/clipN.mp4`.

## 스크립트 (직접 실행도 가능)

```bash
python scripts/check_deps.py
python scripts/fetch.py "<URL 또는 로컬파일>" --outdir shorts_work --lang "ko.*,en.*"
python scripts/clip.py --input shorts_work/ID.mp4 --start 00:03:12 --end 00:03:38 \
    --out out/clip1.mp4 --srt shorts_work/ID.ko.srt --mode crop
```

- `--mode crop`(기본): 중앙 9:16 크롭(꽉 참). `--mode pad`: 축소+흐린 배경(손실 없음).
- `--style`: 자막 ASS 스타일. Windows 한글 폰트 깨지면 `FontName=Malgun Gothic` 등 추가.

## 주의

- 저작권: 본인이 권리를 갖거나 사용이 허용된 영상에만 사용. 무단 재업로드 금지.
- 긴 영상은 다운로드·인코딩에 시간이 걸린다. 구간 확정 후 필요한 클립만 렌더.

## License

MIT
