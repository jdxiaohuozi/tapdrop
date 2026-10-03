# 碰传 · TapDrop for Mac

> 把 **小米蓝牙遥控器 2 Pro** 的 NFC，变成 Mac 的「碰传 / 轻量 AirDrop」：
> 手机碰一下遥控器，挑文件，直接存进 Mac。

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-zero-success)
![License](https://img.shields.io/badge/license-MIT-green)

![碰传演示](demo.png)

[📖 中文详细使用说明](使用说明.md) · [English](#english)

---

## ✨ 一句话看懂

你的遥控器已经能**按键控制、语音录入**，但「传文件」是另一块独立功能——它需要一个电脑端的常驻**接收服务**。本项目就是那个服务：**NFC 负责握手，数据走 Wi-Fi**，思路同华为 / 荣耀碰传。

> Mac 本身**没有 NFC 读卡器**，遥控器里的 NFC 只是一张可被手机读取的标签。所以「碰一下」物理上只做一件事：把一张 **URL 卡片**递给手机，真正的文件搬运由 Mac 程序 + 手机网页经 Wi-Fi 完成。

## 🔧 它是怎么工作的

```mermaid
flowchart LR
    A[📱 手机选文件] --> B[👆 碰一下遥控器 NFC]
    B --> C[🔗 读到 URL 自动打开接收页]
    C --> D[📂 选文件 / 文字]
    D --> E[📡 经同一 Wi-Fi 上传]
    E --> F[💻 Mac 收件箱 + 弹通知]
```

## 🚀 三步上手

1. **双击 `启动.command`** → 浏览器自动弹出控制台（含二维码与链接）
2. **用手机把链接写入遥控器 NFC 标签**（步骤见 [使用说明](使用说明.md)）
3. **以后手机碰一下遥控器 → 选文件 → 完成** ✅

> 若标签只读（小米出厂固化不可写），买一张几块钱的 **NTAG213 空白贴纸**写好贴上即可，效果完全一样。

## 🌟 功能亮点

- 📲 手机网页选文件（图片 / 视频 / 文档，可多选），经同一 Wi-Fi 传入 Mac
- 🔤 顺手也能发文字 / 链接
- 🔔 收到即弹系统通知，自动存入收件箱
- 🔑 自带访问口令，远程非授权请求直接拒绝
- 📡 Bonjour 广播，控制台一键复制链接 / 导出二维码
- 🚀 **零第三方依赖**：纯 Python 标准库 + macOS 内置 CoreImage 生成二维码

## 📋 环境要求

- macOS（用到 CoreImage / `open` / 系统通知）
- Python 3（系统自带 3.9 或 3.13 均可），**无需 pip 安装任何库**
- 手机与 Mac 在同一 Wi-Fi

## 📁 文件结构

| 文件 | 作用 |
|------|------|
| `nfc_airdrop.py` | 接收服务主程序 |
| `ui.py` | 手机发送页 / 桌面控制台 / 文件列表页模板 |
| `启动.command` | 双击启动（自动开控制台） |
| `安装开机自启.command` / `卸载开机自启.command` | 登录自启管理 |
| `使用说明.md` | 完整使用步骤与故障排查 |
| `config.example.json` | 配置示例（实际运行的 `config.json` 由程序自动生成，不提交） |

## 📜 许可证

[MIT](LICENSE) — 可自由使用、修改、再分发。

---

## English

**TapDrop for Mac** turns the NFC tag inside your **Xiaomi Bluetooth Remote 2 Pro**
into a tap-to-send "AirDrop" for your Mac.

Your Mac has no NFC reader, and the remote's NFC is just a readable tag. Tapping the remote
only hands the phone a URL; the actual file transfer runs over Wi-Fi between this Mac service
and a phone web page — the same idea as Huawei/Honor "碰传" (Share).

**How it works:** phone picks a file → tap the remote (NFC delivers the URL) → phone opens the
receive page → pick file → uploaded over the same Wi-Fi → lands in Mac inbox with a notification.

**Features:** multi-file upload from phone, text/link send, macOS notifications, token auth,
Bonjour broadcast, QR export. **Zero third-party dependencies** (Python stdlib + CoreImage).

**Quick start:** double-click `启动.command` → write the shown URL into the remote's NFC tag →
tap the remote with your phone → pick a file → done.

[📖 Full guide (中文)](使用说明.md)
