#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shorts-maker 의존성 점검 (크로스플랫폼).

python / ffmpeg / yt-dlp 존재를 확인하고, 없으면 현재 OS에 맞는
설치 명령을 안내한다. 자동 설치는 하지 않는다(사용자 선택 존중).

종료 코드: 0 = 전부 준비됨, 1 = 하나 이상 누락.
"""
import platform
import shutil
import subprocess
import sys

# Windows에서 출력이 파이프로 캡처될 때 cp949 인코딩 오류를 막는다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def version_of(cmd, args=("--version",)):
    exe = shutil.which(cmd)
    if not exe:
        return None, None
    try:
        out = subprocess.run(
            [exe, *args], capture_output=True, text=True, timeout=15
        )
        line = (out.stdout or out.stderr or "").strip().splitlines()
        return exe, (line[0] if line else "")
    except Exception:
        return exe, ""


def install_hint(tool, os_name):
    hints = {
        "ffmpeg": {
            "Windows": "winget install --id Gyan.FFmpeg -e   (또는 choco install ffmpeg-full)",
            "Darwin": "brew install ffmpeg",
            "Linux": "sudo apt install -y ffmpeg   (또는 배포판 패키지)",
        },
        "yt-dlp": {
            "Windows": "winget install --id yt-dlp.yt-dlp -e   (또는 pip install -U yt-dlp)",
            "Darwin": "brew install yt-dlp   (또는 pip install -U yt-dlp)",
            "Linux": "pipx install yt-dlp   (또는 pip install -U yt-dlp)",
        },
    }
    return hints.get(tool, {}).get(os_name, f"pip install -U {tool}")


def main():
    os_name = platform.system()  # Windows / Darwin / Linux
    print(f"[shorts-maker] OS: {os_name} ({platform.platform()})")
    print(f"[shorts-maker] Python: {sys.version.split()[0]}")

    missing = []
    for tool, args in (("ffmpeg", ("-version",)), ("yt-dlp", ("--version",))):
        exe, ver = version_of(tool, args)
        if exe:
            print(f"  OK  {tool:8} -> {ver or exe}")
        else:
            print(f"  --  {tool:8} 없음")
            missing.append(tool)

    if not missing:
        print("\n준비 완료. fetch.py / clip.py 를 실행할 수 있습니다.")
        return 0

    print("\n[누락] 아래 도구를 설치한 뒤 새 터미널에서 다시 시도하세요:")
    for tool in missing:
        print(f"  * {tool}: {install_hint(tool, os_name)}")
    print("\n설치 후 PATH 인식을 위해 터미널(또는 Claude Code)을 재시작하세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
