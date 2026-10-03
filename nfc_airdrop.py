#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFC碰传 · macOS 接收端
================================================================
手机碰一下（遥控器上的）NFC 标签 -> 打开本机页面 -> 选文件 -> 走 Wi-Fi 存进 Mac。

为什么必须要有这个程序：
    Mac 自身没有 NFC 读卡器，遥控器里的 NFC 是一张"只能被读"的标签。
    所以"碰一下"唯一能做的事，就是把一张 URL 卡片递给手机；
    真正的文件搬运必须由 Mac 上一个常驻的接收服务 + 手机上的网页来完成。
    本程序就是那个接收服务（思路与华为/荣耀碰传一致：NFC 负责握手，Wi-Fi 负责搬数据）。

用法:
    python3 nfc_airdrop.py                 # 启动 ，默认端口 8787
    python3 nfc_airdrop.py --port 9000     # 换端口
    python3 nfc_airdrop.py --dir ~/收文件   # 换收件目录
    python3 nfc_airdrop.py --no-open       # 不自动打开控制台页面
    python3 nfc_airdrop.py --reset-token   # 重新生成访问口令（旧标签需重写）

仅使用 Python 标准库；二维码直接用 macOS 内置的 CoreImage 生成。
"""

import argparse
import json
import logging
import os
import re
import secrets
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import urllib.parse
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui  # noqa: E402

# ---------------------------------------------------------------- 常量 ----

APP_NAME = "NFC碰传"
VERSION = "1.0"

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / "config.json"
LOG_FILE = HERE / "运行日志.log"

DEFAULT_PORT = 8787
DEFAULT_DIR = Path.home() / "Downloads" / "NFC碰传"

PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / "com.king.nfcairdrop.plist"
PLIST_LABEL = "com.king.nfcairdrop"

TOKEN_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"   # 去掉易混字符
MAX_NAME_BYTES = 180

MOBILE_UA = re.compile(r"Mobile|Android|iPhone|iPad|iPod|Windows Phone", re.I)

log = logging.getLogger("nfc")


# ---------------------------------------------------------------- 工具 ----


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0


def random_token(n=6):
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(n))


def run_cmd(args, timeout=4):
    try:
        r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=timeout)
        return r.stdout.decode("utf-8", "replace").strip()
    except Exception:
        return ""


def detect_lan_ip():
    """找一个真实的局域网 IPv4（优先 Wi-Fi/以太网口）。"""
    out = run_cmd(["/sbin/ifconfig"], timeout=5)
    ifaces = {}
    cur = None
    for line in out.splitlines():
        m = re.match(r"^(\w+):", line)
        if m:
            cur = m.group(1)
            ifaces.setdefault(cur, [])
            continue
        m = re.search(r"\binet (\d+\.\d+\.\d+\.\d+)\b", line)
        if m and cur:
            ifaces[cur].append(m.group(1))
    for name in sorted(ifaces.keys()):
        if name == "lo0" or name.startswith("utun") or name.startswith("bridge"):
            continue
        for ip in ifaces[name]:
            if not ip.startswith("169.254."):
                return ip
    # 兜底
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def detect_local_hostname():
    h = run_cmd(["/usr/sbin/scutil", "--get", "LocalHostName"])
    if not h:
        h = socket.gethostname().split(".")[0]
    h = h.strip().lower()
    return (h + ".local") if h else None


def detect_device_name():
    n = run_cmd(["/usr/sbin/scutil", "--get", "ComputerName"])
    return n or "这台 Mac"


def notify(title, text):
    def clean(s):
        return s.replace("\\", "").replace('"', "'")[:110]
    try:
        script = 'display notification "%s" with title "%s"' % (clean(text), clean(title))
        subprocess.Popen(["/usr/bin/osascript", "-e", script],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def autostart_enabled():
    return PLIST_PATH.exists()


# ---------------------------------------------------------------- 二维码 ----
# 用 macOS 自带的 CoreImage 生成二维码位图，再用纯 Python 解出来，
# 好处是零第三方依赖，而且能转成矢量 SVG，打印、写入标签都够清晰。

QR_JS = r"""
ObjC.import('CoreImage');
ObjC.import('AppKit');
function run(argv) {
  var url = argv[0], out = argv[1], ecl = argv[2] || 'M';
  var data = $.NSString.stringWithString(url).dataUsingEncoding($.NSUTF8StringEncoding);
  var f = $.CIFilter.filterWithName('CIQRCodeGenerator');
  f.setValueForKey(data, $.NSString.stringWithString('inputMessage'));
  f.setValueForKey($.NSString.stringWithString(ecl), $.NSString.stringWithString('inputCorrectionLevel'));
  var img = f.outputImage;
  if (!img) { console.log('ERR'); return; }
  var n = Math.round(img.extent.size.width);
  var rep = $.NSBitmapImageRep.alloc.initWithCIImage(img);
  var png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
  png.writeToFileAtomically(out, true);
  console.log('OK ' + n);
}
"""

_qr_cache = {}
_qr_lock = threading.Lock()


def _png_to_matrix(data):
    """解析 8bit PNG（非隔行），返回二维布尔矩阵。True = 黑色模块。"""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG")
    pos, idat, w, h, ct = 8, bytearray(), 0, 0, 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct, cm, fl, il = struct.unpack(">IIBBBBB", body)
            if bd != 8 or il != 0:
                raise ValueError("不支持的 PNG 格式")
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln

    channels = {0: 1, 2: 3, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(bytes(idat))
    stride = w * channels
    rows = []
    prev = bytearray(stride)
    p = 0
    for _ in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif ft != 0:
            raise ValueError("PNG 过滤器 %d 不支持" % ft)
        rows.append(line)
        prev = line

    matrix = []
    for line in rows:
        row = []
        for x in range(w):
            o = x * channels
            if channels >= 4:
                alpha = line[o + 3]
                lum = line[o]
            elif channels == 3:
                alpha = 255
                lum = line[o]
            elif channels == 2:
                alpha = line[o + 1]
                lum = line[o]
            else:
                alpha = 255
                lum = line[o]
            row.append(alpha > 128 and lum < 128)
        matrix.append(row)
    return matrix


def qr_matrix(text):
    """生成二维码模块矩阵（带进程内缓存）。"""
    with _qr_lock:
        if text in _qr_cache:
            return _qr_cache[text]
    with tempfile.TemporaryDirectory() as td:
        js = os.path.join(td, "qr.js")
        png = os.path.join(td, "qr.png")
        with open(js, "w", encoding="utf-8") as f:
            f.write(QR_JS)
        r = subprocess.run(["/usr/bin/osascript", "-l", "JavaScript", js, text, png],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if not os.path.exists(png):
            raise RuntimeError("二维码生成失败：%s" % r.stderr.decode("utf-8", "replace")[:200])
        with open(png, "rb") as f:
            data = f.read()
    m = _png_to_matrix(data)
    with _qr_lock:
        _qr_cache[text] = m
    return m


def qr_svg(text, margin=4, dark="#000000", light="#ffffff"):
    m = qr_matrix(text)
    n = len(m)
    total = n + margin * 2
    parts = []
    for y, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                x0 = x
                while x < n and row[x]:
                    x += 1
                parts.append('<rect x="%d" y="%d" width="%d" height="1"/>' % (x0, y, x - x0))
            else:
                x += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'shape-rendering="crispEdges">'
            '<rect width="%d" height="%d" fill="%s"/>'
            '<g transform="translate(%d,%d)" fill="%s">%s</g></svg>'
            % (total, total, total, total, light, margin, margin, dark, "".join(parts)))


def _png_chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def qr_png(text, scale=10, margin=4):
    """生成放大后的灰度 PNG，方便打印或直接存到手机。"""
    m = qr_matrix(text)
    n = len(m)
    size = (n + margin * 2) * scale
    scan = bytearray()
    blank = b"\xff" * size
    for _ in range(margin * scale):
        scan += b"\x00" + blank
    for row in m:
        line = bytearray(b"\xff" * (margin * scale))
        for v in row:
            line += (b"\x00" if v else b"\xff") * scale
        line += b"\xff" * (margin * scale)
        scan += b"\x00" + bytes(line)
    for _ in range(margin * scale):
        scan += b"\x00" + blank
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", zlib.compress(bytes(scan), 9))
            + _png_chunk(b"IEND", b""))


# ---------------------------------------------------------------- 配置 ----


class Config(object):
    def __init__(self, port=None, save_dir=None, reset_token=False):
        data = {}
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text("utf-8"))
            except Exception:
                data = {}
        self.port = int(port or data.get("port") or DEFAULT_PORT)
        self.save_dir = Path(save_dir or data.get("save_dir") or DEFAULT_DIR).expanduser()
        self.token = None if reset_token else data.get("token")
        if not self.token:
            self.token = random_token(6)
        self.notify = bool(data.get("notify", True))
        self.advertise = bool(data.get("advertise", True))
        self.last_port = data.get("last_port")
        self._save()

    def _save(self):
        try:
            CONFIG_FILE.write_text(json.dumps({
                "port": self.port,
                "last_port": self.last_port,
                "save_dir": str(self.save_dir),
                "token": self.token,
                "notify": self.notify,
                "advertise": self.advertise,
            }, ensure_ascii=False, indent=2) + "\n", "utf-8")
        except Exception as e:
            log.warning("配置写入失败：%s", e)

    def remember_port(self, port):
        self.last_port = port
        self._save()


# ---------------------------------------------------------------- 收件箱 ----


def safe_filename(name):
    name = unicodedata.normalize("NFC", name or "")
    name = name.replace("\\", "/").split("/")[-1]
    name = name.replace(":", "-")                      # 冒号在 macOS 上会显示成斜杠
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    name = name.strip().lstrip(".")
    if not name:
        name = "未命名文件"
    if len(name.encode("utf-8")) > MAX_NAME_BYTES:
        stem, ext = os.path.splitext(name)
        keep = MAX_NAME_BYTES - len(ext.encode("utf-8")) - 1
        while len(stem.encode("utf-8")) > keep and stem:
            stem = stem[:-1]
        name = (stem or "文件") + ext
    return name


def reserve_path(directory, name):
    """原子地占坑，避免并发重名覆盖。返回 (最终路径, 占位文件句柄已关闭)。"""
    stem, ext = os.path.splitext(name)
    i = 0
    while True:
        cand = directory / (name if i == 0 else "%s-%d%s" % (stem, i, ext))
        try:
            fd = os.open(str(cand), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return cand
        except FileExistsError:
            i += 1
            if i > 9999:
                raise RuntimeError("同名文件太多")


def list_inbox(directory, limit=200):
    items = []
    try:
        for p in directory.iterdir():
            if p.name.startswith(".") or not p.is_file():
                continue
            st = p.stat()
            items.append({
                "name": p.name,
                "size": st.st_size,
                "ts": st.st_mtime,
                "mtime": time.strftime("%m-%d %H:%M", time.localtime(st.st_mtime)),
            })
    except FileNotFoundError:
        return []
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:limit]


# ---------------------------------------------------------------- Bonjour ----


class Bonjour(threading.Thread):
    """广播 _http._tcp 服务，方便同网段的设备发现。失败不影响主流程。"""

    daemon = True

    def __init__(self, port, name):
        threading.Thread.__init__(self)
        self.port = port
        self.name = name
        self.proc = None
        self.ok = False

    def run(self):
        exe = "/usr/bin/dns-sd"
        if not os.path.exists(exe):
            return
        try:
            self.proc = subprocess.Popen(
                [exe, "-R", self.name, "_http._tcp", "local", str(self.port)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.6)
            self.ok = self.proc.poll() is None
            if self.ok:
                log.info("Bonjour 广播已开启（_http._tcp, 端口 %d）", self.port)
            self.proc.wait()
        except Exception as e:
            log.debug("Bonjour 广播失败：%s", e)
        self.ok = False

    def stop(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass


# ---------------------------------------------------------------- 服务 ----


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "NFCAirDrop/" + VERSION
    sys_version = ""

    cfg = None
    bonjour = None

    # ---------- 基础设施 ----------

    def log_message(self, fmt, *args):
        msg = fmt % args
        if "favicon" in msg:
            return
        peer = self.client_address[0]
        if peer in ("127.0.0.1", "::1"):
            return  # 本机轮询不刷屏
        log.info("%s %s", peer, msg)

    def _split(self):
        u = urllib.parse.urlparse(self.path)
        return u.path, urllib.parse.parse_qs(u.query)

    def _is_local(self):
        return self.client_address[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1")

    def _authed(self, q):
        if self._is_local():
            return True
        k = (q.get("k") or [""])[0]
        return bool(k) and secrets.compare_digest(k, self.cfg.token)

    def _send(self, code, body=b"", ctype="text/html; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}):
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD" and body:
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                self.close_connection = True

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False),
                   "application/json; charset=utf-8")

    def _redirect(self, to):
        self._send(302, b"", extra=[("Location", to)])

    def _deny(self):
        self._send(403, "<html><meta charset='utf-8'><body style='font-family:-apple-system;"
                        "padding:40px;text-align:center'><h3>链接无效或已过期</h3>"
                        "<p style='color:#888'>请用遥控器上的 NFC 标签重新打开，"
                        "或在 Mac 控制台里复制最新链接。</p></body></html>")

    def _hosts(self):
        c = self.cfg
        hosts = {}
        hosts["ip"] = {"label": "IP 地址", "url": "http://%s:%d/t/%s" % (self.lan_ip, c.port, c.token)}
        if self.hostname:
            hosts["local"] = {"label": "局域网名称",
                              "url": "http://%s:%d/t/%s" % (self.hostname, c.port, c.token)}
        else:
            hosts["local"] = hosts["ip"]
        return hosts

    # ---------- GET ----------

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path, q = self._split()
        cfg = self.cfg

        if path == "/favicon.ico":
            self._send(204, b"")
            return
        if path == "/health":
            self._json({"ok": True, "app": APP_NAME, "version": VERSION})
            return

        # 手机碰 NFC 之后落到的页面
        if path.startswith("/t/"):
            if secrets.compare_digest(path[3:], cfg.token):
                html = (ui.PHONE
                        .replace("__BASE__", ui.BASE_CSS)
                        .replace("__MAC__", self.device_name)
                        .replace("__TOKEN__", cfg.token)
                        .replace("__URL__", self._hosts()["local"]["url"]))
                self._send(200, html)
            else:
                self._deny()
            return

        # 手机端浏览 Mac 上已收到的文件
        if path.startswith("/f/"):
            if not secrets.compare_digest(path[3:], cfg.token):
                self._deny()
                return
            files = list_inbox(cfg.save_dir)
            if not files:
                items = "<div class='empty'>还没有收到任何文件</div>"
            else:
                rows = []
                for f in files:
                    rows.append(
                        "<div class='item'><div class='ico'>📦</div>"
                        "<div class='nm'>%s</div><div class='mt'>%s<br>%s</div></div>"
                        % (self._esc(f["name"]), human_size(f["size"]),
                           "<a href='/dl/%s/%s'>下载</a>"
                           % (cfg.token, urllib.parse.quote(f["name"]))))
                items = "".join(rows)
            html = (ui.LIST_PAGE
                    .replace("__BASE__", ui.BASE_CSS)
                    .replace("__TOKEN__", cfg.token)
                    .replace("__ITEMS__", items))
            self._send(200, html)
            return

        # 电脑端控制台
        if path in ("/desk", "/desk/"):
            if not self._authed(q):
                self._deny()
                return
            html = (ui.DESK
                    .replace("__BASE__", ui.BASE_CSS)
                    .replace("__MAC__", self._esc(self.device_name))
                    .replace("__TOKEN__", cfg.token)
                    .replace("__HOSTS__", json.dumps(self._hosts(), ensure_ascii=False)))
            self._send(200, html)
            return

        # 根路径：手机 -> 发送页，电脑 -> 控制台
        if path in ("/", "/u", "/index.html"):
            if MOBILE_UA.search(self.headers.get("User-Agent", "")):
                self._redirect("/t/%s" % cfg.token)
            else:
                self._redirect("/desk?k=%s" % cfg.token)
            return

        if path == "/api/qr.svg":
            h = (q.get("h") or ["local"])[0]
            hosts = self._hosts()
            url = hosts.get(h, hosts.get("local"))["url"]
            try:
                self._send(200, qr_svg(url), "image/svg+xml; charset=utf-8")
            except Exception as e:
                self._send(500, str(e), "text/plain; charset=utf-8")
            return

        if path == "/api/qr.png":
            h = (q.get("h") or ["local"])[0]
            hosts = self._hosts()
            url = hosts.get(h, hosts.get("local"))["url"]
            try:
                self._send(200, qr_png(url), "image/png")
            except Exception as e:
                self._send(500, str(e), "text/plain; charset=utf-8")
            return

        if path == "/api/inbox":
            if not self._authed(q):
                self._deny()
                return
            self._json({
                "running": True,
                "port": cfg.port,
                "dir": str(cfg.save_dir).replace(str(Path.home()), "~"),
                "bonjour": bool(self.bonjour and self.bonjour.ok),
                "autostart": autostart_enabled(),
                "files": list_inbox(cfg.save_dir),
            })
            return

        if path.startswith("/dl/"):
            self._download(path, q)
            return

        self._send(404, "404", "text/plain; charset=utf-8")

    def _download(self, path, q):
        parts = path.split("/")
        if len(parts) < 4:
            self._send(404, "404", "text/plain")
            return
        if not (self._is_local() or secrets.compare_digest(parts[2], self.cfg.token)):
            self._deny()
            return
        name = urllib.parse.unquote("/".join(parts[3:]))
        if os.path.basename(name) != name:
            self._send(400, "bad name", "text/plain")
            return
        p = self.cfg.save_dir / name
        if not p.is_file():
            self._send(404, "not found", "text/plain")
            return
        size = p.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition",
                         "attachment; filename*=UTF-8''" + urllib.parse.quote(name))
        self.end_headers()
        with open(p, "rb") as f:
            while True:
                chunk = f.read(1 << 20)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    self.close_connection = True
                    return

    # ---------- PUT：文件上传 ----------

    def do_PUT(self):
        path, q = self._split()
        if path != "/api/upload":
            self._send(404, "404", "text/plain")
            return
        if not self._authed(q):
            self._deny()
            return

        p = self.cfg.save_dir
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._json({"ok": False, "error": "无法创建收件目录：%s" % e}, 500)
            return

        raw_name = urllib.parse.unquote(self.headers.get("X-File-Name", ""))
        if not raw_name:
            raw_name = "未命名文件-%s" % time.strftime("%H%M%S")
        name = safe_filename(raw_name)

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            self._json({"ok": False, "error": "缺少内容长度"}, 411)
            return

        tmp = p / (".接收中-%s.part" % secrets.token_hex(6))
        received = 0
        started = time.time()
        try:
            with open(tmp, "wb") as f:
                remaining = length
                while remaining > 0:
                    chunk = self.rfile.read(min(1 << 20, remaining))
                    if not chunk:
                        raise IOError("连接提前中断")
                    f.write(chunk)
                    remaining -= len(chunk)
                    received += len(chunk)
                f.flush()
                os.fsync(f.fileno())
            final = reserve_path(p, name)
            os.replace(str(tmp), str(final))
        except Exception as e:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            self.close_connection = True
            self._json({"ok": False, "error": str(e)}, 500)
            return

        cost = max(time.time() - started, 0.001)
        log.info("收到 %s（%s，%.1f MB/s）", final.name, human_size(received),
                 received / cost / 1048576.0)
        if self.cfg.notify and received > 0:
            notify("%s · 收到文件" % APP_NAME, final.name)

        self._json({"ok": True, "name": final.name, "size": received,
                    "path": str(final), "mtime": time.strftime("%H:%M")})

    # ---------- POST：文字 / 打开目录 / 定位文件 ----------

    def do_POST(self):
        path, q = self._split()
        if not self._authed(q):
            self._deny()
            return


        if path == "/api/text":
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
            except Exception:
                body = b""
            text = body.decode("utf-8", "replace").strip()
            if not text:
                self._json({"ok": False, "error": "内容为空"}, 400)
                return
            self.cfg.save_dir.mkdir(parents=True, exist_ok=True)
            name = "文字-%s.txt" % time.strftime("%Y%m%d-%H%M%S")
            final = reserve_path(self.cfg.save_dir, name)
            final.write_text(text + "\n", "utf-8")
            log.info("收到文字 %d 字 -> %s", len(text), final.name)
            if self.cfg.notify:
                notify("%s · 收到文字" % APP_NAME, text[:60].replace("\n", " "))
            self._json({"ok": True, "name": final.name})
            return

        if path == "/api/open":
            subprocess.Popen(["/usr/bin/open", str(self.cfg.save_dir)])
            self._json({"ok": True})
            return

        if path == "/api/reveal":
            name = (q.get("name") or [""])[0]
            if name and os.path.basename(name) == name:
                p = self.cfg.save_dir / name
                if p.exists():
                    subprocess.Popen(["/usr/bin/open", "-R", str(p)])
                    self._json({"ok": True})
                    return
            self._json({"ok": False}, 404)
            return

        self._send(404, "404", "text/plain")

    # ---------- 小工具 ----------

    @staticmethod
    def _esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------- 启动 ----


def pick_free_port(preferred):
    """优先用上次成功的端口，被占用则往后找一个空闲端口。"""
    for port in [preferred] + list(range(preferred + 1, preferred + 20)):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", port))
            s.close()
            return port
        except OSError:
            s.close()
            continue
    return preferred


def setup_logging(verbose):
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    try:
        fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(fh)
    except Exception:
        pass


def banner(cfg, hosts, bonjour_on):
    line = "─" * 58
    print("")
    print("  " + line)
    print("   %s · macOS 接收端 v%s" % (APP_NAME, VERSION))
    print("  " + line)
    print("   收件箱   %s" % cfg.save_dir)
    print("   局域网   %s" % hosts.get("local", {}).get("url"))
    print("   IP 地址  %s" % hosts["ip"]["url"])
    print("   控制台   http://127.0.0.1:%d/desk?k=%s" % (cfg.port, cfg.token))
    print("   Bonjour  %s" % ("已广播" if bonjour_on else "未开启"))
    print("  " + line)
    print("  把下面这个链接写进遥控器上的 NFC 标签：")
    print("      %s" % (hosts.get("local") or hosts["ip"])["url"])
    print("  " + line)
    print("   保持本窗口开着即可接收文件，按 Control-C 退出。")
    print("")


def main():
    ap = argparse.ArgumentParser(description="%s · macOS 接收端" % APP_NAME)
    ap.add_argument("--port", type=int, help="监听端口（默认 8787）")
    ap.add_argument("--dir", help="文件保存目录（默认 ~/Downloads/NFC碰传）")
    ap.add_argument("--no-open", action="store_true", help="启动后不自动打开控制台")
    ap.add_argument("--no-notify", action="store_true", help="收到文件不弹系统通知")
    ap.add_argument("--no-bonjour", action="store_true", help="不广播 Bonjour 服务")
    ap.add_argument("--reset-token", action="store_true", help="重新生成访问口令")
    ap.add_argument("--verbose", action="store_true", help="输出更多日志")
    args = ap.parse_args()

    setup_logging(args.verbose)
    cfg = Config(port=args.port, save_dir=args.dir, reset_token=args.reset_token)
    if args.no_notify:
        cfg.notify = False
    if args.no_bonjour:
        cfg.advertise = False

    port = pick_free_port(cfg.port)
    cfg.port = port
    cfg.save_dir.mkdir(parents=True, exist_ok=True)

    Handler.cfg = cfg
    Handler.lan_ip = detect_lan_ip()
    Handler.hostname = detect_local_hostname()
    Handler.device_name = detect_device_name()

    try:
        httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    except OSError as e:
        log.error("端口 %d 无法监听：%s", port, e)
        return 1
    httpd.daemon_threads = True

    bj = None
    if cfg.advertise:
        bj = Bonjour(port, APP_NAME)
        Handler.bonjour = bj
        bj.start()
        time.sleep(0.7)

    hosts = {
        "local": {"label": "局域网名称",
                  "url": "http://%s:%d/t/%s" % (Handler.hostname, port, cfg.token)}
                 if Handler.hostname else None,
        "ip": {"label": "IP 地址",
               "url": "http://%s:%d/t/%s" % (Handler.lan_ip, port, cfg.token)},
    }
    if not hosts["local"]:
        hosts["local"] = hosts["ip"]

    cfg.remember_port(port)
    banner(cfg, hosts, bool(bj and bj.ok))

    # 把二维码和链接落到磁盘，方便写入标签时直接看
    try:
        tag_url = hosts["local"]["url"]
        (HERE / "NFC标签链接.txt").write_text(tag_url + "\n", "utf-8")
        (HERE / "NFC标签二维码.svg").write_text(qr_svg(tag_url), "utf-8")
        with open(str(HERE / "NFC标签二维码.png"), "wb") as f:
            f.write(qr_png(tag_url, scale=12))
    except Exception as e:
        log.debug("二维码导出失败：%s", e)

    if not args.no_open:
        try:
            subprocess.Popen(["/usr/bin/open",
                              "http://127.0.0.1:%d/desk?k=%s" % (port, cfg.token)])
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
        log.info("已停止接收服务")
    finally:
        if bj:
            bj.stop()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
