---
name: blogger-publish
description: This skill should be used when the user asks to write, upload, or manage blog drafts for the LED blog (ledcontroller-guide.blogspot.com) via the Blog_Queue → Blogger API pipeline. Korean triggers: "블로그 초안 써줘", "블로그 글 써줘", "블로그 올려줘", "블로거 업로드", "블로그 발행", "애드센스 블로그". English triggers: "write a blog draft", "upload to blogger", "blogger publish", "blog post for the LED blog".
---

# Blogger Publish

LED 전문 블로그 `ledcontroller-guide.blogspot.com`의
초안 작성 → 자동 업로드 → 검토 발행 파이프라인을 운영하는 스킬.

> **운영 전략·심사 대응 원칙은 볼트의 `10_Wiki/SOPs/Blogger 자동 발행 절차.md`가 정본이다.**
> 이 스킬은 메커니즘(작성 형식·업로드 절차)만 다루며, 발행 주기·심사 전략 등은 반드시 볼트 SOP를 따른다.

## Pipeline

```text
영문 SEO 초안 작성 → <vault>/30_Outputs/Blog_Queue/*.md (status: draft)
  → python tools/blogger_publish.py   (Blogger 초안으로 업로드)
  → 사용자가 Blogger 대시보드에서 검토 후 발행
```

`<vault>`는 사용자의 Obsidian 볼트 루트 (동기화 폴더).
스크립트는 볼트의 `tools/blogger_publish.py`에 있으며 볼트 루트에서 실행한다.

## Workflow

### 1. 초안 작성 요청 시 ("블로그 초안 써줘")

`30_Outputs/Blog_Queue/YYYY-MM-DD slug.md` 형식으로 작성한다:

```md
---
title: English SEO Title
labels: Comma, Separated, Labels
status: draft
created: YYYY-MM-DD
---

Body in English Markdown (tables and fenced code supported)
```

**이미지/자산 규칙 (글별 폴더)**:

- 글에 이미지·다이어그램이 필요하면 **글 전용 자산 폴더** `30_Outputs/Blog_Queue/<파일명 stem>/`에 저장한다.
  공용 `images/` 폴더는 쓰지 않는다 (글이 늘면 관리가 어려움).
- 기술 다이어그램(구조도, 비교도 등)은 **인라인 SVG**로 본문에 직접 넣는다.
  인라인 SVG는 호스팅 없이 Blogger에 그대로 발행되고 Obsidian/브라우저에서도 보인다.
  자산 폴더에는 편집용 `.svg`와 래스터 `.png`를 소스로 보관한다.
- SVG 렌더 검수: 헤드리스 Chrome로 PNG 저장 후 Read로 확인.
  `chrome --headless=new --screenshot=out.png --window-size=W,H http://127.0.0.1:PORT/file`
  (임시 http.server는 **반드시 PID로 종료**한다. cwd 폴더를 잠근다.)
- 사진·인포그래픽은 **CDN 호스팅**한다: `python tools/blog_publish_image.py "<이미지>" --slug <슬러그> --md "<글MD>"`
  → WebP 최적화 + 해시 파일명으로 이미지 저장소에 푸시, MD의 `<img src>`를 jsDelivr URL로 교체.
  이 URL은 Blogger 발행/재업로드(update)에도 유지되고 lazy-load된다. `<img>`에 `width`/`height`/`loading="lazy"` 유지.
- 다이어그램(구조도·비교도)은 여전히 **인라인 SVG** 우선(요청 0, 확대 선명). 로컬 상대경로 이미지는 Blogger에서 깨지므로 쓰지 않는다.

**디자인/성능 규칙 (로딩 시간 최우선)**:

- 블로그 테마 CSS는 `30_Outputs/Blog_Pages/blogger-theme.css`(Blogger에 붙여넣기),
  아카이브 스타일은 `tools/blog_archive.css`. 토큰·근거는 볼트의 디자인 시스템 노트 참조.
- **외부 네트워크 요청 0**: `@import`·CDN·웹폰트·외부 이미지 금지. **시스템 폰트 스택만** 사용.
  CSS 수정 후 `grep -E '@import|url\\(|https?://'`로 외부 요청 0을 확인한다.

작성 원칙:

- **영어로 통일**한다 (글로벌 B2B 독자).
- 주제는 LED 컨트롤러/디스플레이 실무: NovaStar·Colorlight 설정, 펌웨어,
  구매 가이드(COB vs SMD, 픽셀피치), 현장 트러블슈팅.
- 800~1,200단어, 실무 표/체크리스트 포함, AI 티 나는 문구("In conclusion",
  "delve", "In today's fast-paced world") 금지.
- 라벨은 기존 체계 재사용: `Controller Guide`, `LED Basics`, `Buying Guide`,
  `NovaStar`, `Firmware`, `Setup`.

### 2. 업로드 요청 시 ("블로그 올려줘")

볼트 루트에서 실행:

```bash
python tools/blogger_publish.py --status   # 대기 목록 확인
python tools/blogger_publish.py            # Blogger 초안으로 업로드
```

- 업로드 성공 시 스크립트가 frontmatter를 `status: uploaded` + `post_id`로 자동 변경한다.
- **재업로드/수정 반영**: `status`를 `draft`로 바꾸고 다시 실행하면, `post_id`(없으면 같은 title)로
  기존 Blogger 글을 **덮어쓴다(update)** → 중복 초안이 생기지 않는다. `--status`가 `[업데이트]`/`[신규]`를 미리 표시.
- update는 MD 본문으로 Blogger 글을 통째로 덮어쓰므로, 최종 이미지 URL은 MD에 반영해 둔다.
- `--publish`(즉시 공개)는 사용자가 명시적으로 요청할 때만 쓴다.
- 자동 업로드는 항상 **초안까지**. 발행은 사람이 검토 후 한다.
- 업로드 후 후처리 (모두 수행):
  1. `python tools/blog_archive_html.py`를 실행해 초안을
     `10_Wiki/Projects/Blogger 수익화/Posts/`에 **HTML로** 아카이브한다
     (발행본과 동일한 마크업, 인라인 SVG 포함, 브라우저로 바로 열림).
     아카이브는 MD가 아니라 HTML로 저장한다.
  2. 진행현황 노트(`10_Wiki/Projects/Blogger 수익화/Blogger 수익화 프로젝트 진행현황.md`)의
     체크리스트와 "작성된 글 아카이브" 목록에 새 글의 `.html` 링크를 추가한다
     (마크다운 링크 형식, 위키링크 아님).

### 3. 운영 원칙

발행 주기, 심사 대응, 콘텐츠 전략은 **볼트의 `10_Wiki/SOPs/Blogger 자동 발행 절차.md`를 따른다.**
이 저장소에는 전략 세부를 기록하지 않는다.

## Prerequisites (최초 1회, 기기마다)

1. `pip install google-api-python-client google-auth-oauthlib markdown`
2. OAuth 클라이언트(데스크톱 앱) JSON을
   `~/.credentials/blogger_publisher/client_secret.json`에 저장
   (Blogger API v3 활성화된 Google Cloud 프로젝트).
3. `python tools/blogger_publish.py --test` → 브라우저 인증 → "연결 확인" 출력.

토큰·클라이언트 시크릿은 **볼트/노트/저장소에 절대 저장하지 않는다.**
상세 절차는 볼트의 `10_Wiki/SOPs/Blogger 자동 발행 절차.md` 참조.

## Troubleshooting

| 증상 | 조치 |
|---|---|
| `client_secret.json이 없습니다` | Prerequisites 2번 수행 |
| 인증 브라우저에서 403 access_denied | Google Cloud 콘솔 > 대상 > 테스트 사용자에 블로그 소유 계정 추가 |
| `invalid_grant` / 토큰 만료 | `~/.credentials/blogger_publisher/token.json` 삭제 후 `--test` 재실행 |
| 업로드 0건 | Blog_Queue에 `status: draft`인 파일이 있는지 확인 |
