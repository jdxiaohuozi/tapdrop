#!/bin/bash
# NFC碰传 · 双击启动（macOS）
# 终端窗口会保持打开以持续接收文件，关掉窗口即停止服务。
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
cd "$(dirname "$0")" || exit 1

# 优先用 WorkBuddy 自带的 Python 3.13，否则退回系统 python3
if [ -x "/Users/king/.workbuddy/binaries/python/versions/3.13.12/bin/python3" ]; then
  PY="/Users/king/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  PY="/usr/bin/python3"
fi

echo "NFC碰传 · 正在启动接收服务 …"
exec "$PY" nfc_airdrop.py
