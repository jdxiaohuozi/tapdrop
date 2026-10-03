#!/bin/bash
# NFC碰传 · 卸载开机自启（macOS LaunchAgent）
set -e
PLIST="$HOME/Library/LaunchAgents/com.king.nfcairdrop.plist"

launchctl unload "$PLIST" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.king.nfcairdrop" 2>/dev/null || true
rm -f "$PLIST"
echo "✅ 已卸载开机自启。接收服务不再随登录启动（本次运行中的进程不受影响）。"
