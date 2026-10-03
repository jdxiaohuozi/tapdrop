#!/bin/bash
# NFC碰传 · 安装开机自启（macOS LaunchAgent）
set -e
cd "$(dirname "$0")"
SCRIPT_DIR="$PWD"
PLIST="$HOME/Library/LaunchAgents/com.king.nfcairdrop.plist"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.king.nfcairdrop</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$SCRIPT_DIR/nfc_airdrop.py</string>
    <string>--no-open</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$SCRIPT_DIR</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$SCRIPT_DIR/launchd.log</string>
  <key>StandardErrorPath</key>
  <string>$SCRIPT_DIR/launchd.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
if launchctl load "$PLIST" 2>/dev/null; then
  echo "✅ 已安装并载入开机自启，登录后自动运行。"
else
  launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null && echo "✅ 已安装并载入开机自启（bootstrap）。" \
    || echo "⚠️ plist 已写入，但载入失败，请手动执行：launchctl load $PLIST"
fi
echo "如需卸载，请运行“卸载开机自启.command”。"
