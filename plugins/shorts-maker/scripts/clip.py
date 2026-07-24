#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""구간 컷 + 9:16 세로 변환 + (선택) 자막 번인. 크로스플랫폼(ffmpeg 호출).

예:
  python clip.py --input shorts_work/abc.mp4 --start 00:03:12 --end 00:03:38 \\
      --out out/clip1.mp4 --srt shorts_work/abc.ko.srt --mode crop --title "핵심 요약"

--mode crop : 중앙을 9:16으로 잘라 1080x1920 (기본, 화면 꽉 참)
--mode pad  : 원본을 축소해 중앙 배치 + 흐린 배경 (내용 손실 없음)

자막(--srt)이 있으면 [start,end] 구간만 잘라 클립 기준(0초 시작)으로 재정렬해 번인한다.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

# Windows에서 출력이 파이프로 캡처될 때 cp949 인코딩 오류를 막는다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def to_seconds(t):
    """'SS(.ms)' | 'MM:SS' | 'HH:MM:SS(.ms)' -> float seconds."""
    t = str(t).strip()
    if re.fullmatch(r"\d+(\.\d+)?", t):
        return float(t)
    parts = t.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    raise ValueError(f"시간 형식을 해석할 수 없습니다: {t}")


def sec_to_srt(ts):
    if ts < 0:
        ts = 0.0
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = int(ts % 60)
    ms = int(round((ts - int(ts)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


SRT_TIME = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


def parse_srt(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    blocks = re.split(r"\n\s*\n", raw.strip())
    cues = []
    for b in blocks:
        m = SRT_TIME.search(b)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0
        lines = b.split("\n")
        # 자막 텍스트: 타임코드 줄 이후
        txt_start = 0
        for i, ln in enumerate(lines):
            if SRT_TIME.search(ln):
                txt_start = i + 1
                break
        text = "\n".join(lines[txt_start:]).strip()
        if text:
            cues.append((start, end, text))
    return cues


def slice_srt(cues, start, end, out_path):
    """[start,end] 와 겹치는 자막을 클립 기준(0초)으로 재정렬해 저장."""
    kept = []
    for s, e, text in cues:
        if e <= start or s >= end:
            continue
        ns = max(0.0, s - start)
        ne = min(end - start, e - start)
        if ne <= ns:
            continue
        kept.append((ns, ne, text))
    if not kept:
        return None
    with open(out_path, "w", encoding="utf-8") as f:
        for i, (s, e, text) in enumerate(kept, 1):
            f.write(f"{i}\n{sec_to_srt(s)} --> {sec_to_srt(e)}\n{text}\n\n")
    return out_path


def build_vf(mode, srt_name, style):
    """비디오 필터(-vf) 문자열. srt_name 은 ffmpeg cwd 기준 상대 파일명."""
    if mode == "pad":
        base = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,gblur=sigma=20[bg];"
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
    else:  # crop
        base = (
            "crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)':"
            "x='(iw-ow)/2':y='(ih-oh)/2',scale=1080:1920,setsar=1"
        )
    if srt_name:
        sub = f"subtitles={srt_name}:force_style='{style}'"
        base = base + "," + sub if mode != "pad" else base + "," + sub
    return base, (mode == "pad")


def main():
    ap = argparse.ArgumentParser(description="shorts-maker: 구간 컷 + 9:16 + 자막")
    ap.add_argument("--input", required=True, help="원본 영상 경로")
    ap.add_argument("--start", required=True, help="시작 (SS | MM:SS | HH:MM:SS)")
    ap.add_argument("--end", required=True, help="끝 (SS | MM:SS | HH:MM:SS)")
    ap.add_argument("--out", required=True, help="출력 mp4 경로")
    ap.add_argument("--srt", default=None, help="원본 자막(srt) 경로(선택)")
    ap.add_argument("--mode", choices=["crop", "pad"], default="crop")
    ap.add_argument("--style",
                    default="Fontsize=16,Outline=2,Shadow=0,MarginV=60,Alignment=2",
                    help="자막 force_style (ASS 스타일)")
    args = ap.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ERROR: ffmpeg 가 없습니다. check_deps.py 를 먼저 실행하세요.",
              file=sys.stderr)
        return 2
    if not os.path.exists(args.input):
        print(f"ERROR: 입력 없음: {args.input}", file=sys.stderr)
        return 2

    start = to_seconds(args.start)
    end = to_seconds(args.end)
    dur = end - start
    if dur <= 0:
        print("ERROR: end 는 start 보다 커야 합니다.", file=sys.stderr)
        return 2

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)

    # 자막 슬라이스: ffmpeg subtitles 필터는 Windows 경로(콜론) 이스케이프가 까다로워
    # ffmpeg 를 out_dir 에서 실행하고 상대 파일명만 넘긴다.
    srt_name = None
    tmp_srt = None
    if args.srt and os.path.exists(args.srt):
        cues = parse_srt(args.srt)
        tmp_srt = os.path.join(out_dir, "_clip_sub.srt")
        if slice_srt(cues, start, end, tmp_srt):
            srt_name = "_clip_sub.srt"

    vf, is_complex = build_vf(args.mode, srt_name, args.style)
    input_abs = os.path.abspath(args.input)
    out_name = os.path.basename(args.out)

    cmd = [ffmpeg, "-y", "-ss", f"{start:.3f}", "-i", input_abs, "-t", f"{dur:.3f}"]
    if is_complex:
        cmd += ["-filter_complex", vf]
    else:
        cmd += ["-vf", vf]
    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_name,
    ]

    print(f"[clip] {args.start}~{args.end} ({dur:.1f}s) mode={args.mode} "
          f"sub={'yes' if srt_name else 'no'} -> {args.out}")
    r = subprocess.run(cmd, cwd=out_dir, capture_output=True, text=True)
    if tmp_srt and os.path.exists(tmp_srt):
        try:
            os.remove(tmp_srt)
        except OSError:
            pass
    if r.returncode != 0:
        print("ERROR: ffmpeg 실패\n" + (r.stderr[-2000:] if r.stderr else ""),
              file=sys.stderr)
        return 2
    print(f"[clip] 완료: {os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
