#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""롱폼 소스 확보 (크로스플랫폼).

YouTube URL -> yt-dlp 로 mp4 + 자막(srt) 다운로드.
로컬 파일 경로 -> 그대로 사용(자막은 별도 --srt 로 지정 가능).

결과를 JSON 한 줄로 stdout에 출력한다:
  {"video": "...mp4", "srt": "...srt"|null, "title": "...", "duration": 123.4}

Claude Code는 이 srt(타임스탬프 포함 자막)를 읽고 하이라이트 구간을 고른 뒤
clip.py 로 각 구간을 숏츠로 만든다.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

# Windows에서 출력이 파이프로 캡처될 때 cp949 인코딩 오류를 막는다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe_duration(video):
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    r = run([exe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", video])
    try:
        return float(r.stdout.strip())
    except Exception:
        return None


def find_one(outdir, stem, exts):
    for ext in exts:
        p = os.path.join(outdir, stem + ext)
        if os.path.exists(p):
            return p
    # fallback: prefix match
    for name in sorted(os.listdir(outdir)):
        for ext in exts:
            if name.startswith(stem) and name.endswith(ext):
                return os.path.join(outdir, name)
    return None


def fetch_youtube(url, outdir, langs):
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        print("ERROR: yt-dlp 가 없습니다. check_deps.py 를 먼저 실행하세요.",
              file=sys.stderr)
        return 2
    os.makedirs(outdir, exist_ok=True)
    stem = "%(id)s"
    out_tmpl = os.path.join(outdir, stem + ".%(ext)s")
    cmd = [
        ytdlp,
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format", "mp4",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", langs,
        "--convert-subs", "srt",
        "--restrict-filenames",
        "--no-playlist",
        "-o", out_tmpl,
        "--print", "after_move:%(id)s",
        url,
    ]
    r = run(cmd)
    if r.returncode != 0:
        print("ERROR: yt-dlp 다운로드 실패\n" + (r.stderr or ""), file=sys.stderr)
        return 2
    vid_id = (r.stdout.strip().splitlines() or [""])[-1].strip()
    if not vid_id:
        print("ERROR: 영상 ID를 확인하지 못했습니다.\n" + r.stdout, file=sys.stderr)
        return 2

    video = find_one(outdir, vid_id, [".mp4", ".mkv", ".webm"])
    # 자막: id.<lang>.srt 형태 → 가장 먼저 발견되는 것
    srt = None
    for name in sorted(os.listdir(outdir)):
        if name.startswith(vid_id) and name.endswith(".srt"):
            srt = os.path.join(outdir, name)
            break

    # 제목
    title = vid_id
    tr = run([ytdlp, "--no-playlist", "--print", "%(title)s", "--skip-download", url])
    if tr.returncode == 0 and tr.stdout.strip():
        title = tr.stdout.strip().splitlines()[0]

    result = {
        "video": video,
        "srt": srt,
        "title": title,
        "duration": ffprobe_duration(video) if video else None,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


def use_local(path, srt, outdir):
    if not os.path.exists(path):
        print(f"ERROR: 파일 없음: {path}", file=sys.stderr)
        return 2
    result = {
        "video": os.path.abspath(path),
        "srt": os.path.abspath(srt) if srt and os.path.exists(srt) else None,
        "title": os.path.splitext(os.path.basename(path))[0],
        "duration": ffprobe_duration(path),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="shorts-maker: 소스 영상/자막 확보")
    ap.add_argument("source", help="YouTube URL 또는 로컬 영상 파일 경로")
    ap.add_argument("--outdir", default="shorts_work", help="작업 폴더 (기본 ./shorts_work)")
    ap.add_argument("--lang", default="ko.*,en.*",
                    help="자막 언어 우선순위 (yt-dlp sub-langs, 기본 'ko.*,en.*')")
    ap.add_argument("--srt", default=None, help="로컬 파일용 자막(srt) 경로(선택)")
    args = ap.parse_args()

    is_url = args.source.startswith("http://") or args.source.startswith("https://")
    if is_url:
        return fetch_youtube(args.source, args.outdir, args.lang)
    return use_local(args.source, args.srt, args.outdir)


if __name__ == "__main__":
    sys.exit(main())
