# -*- coding: utf-8 -*-
"""NFC碰传 - 页面模板

所有页面都是服务端渲染的纯静态 HTML，不依赖任何外部 CDN，
保证在没有外网的情况下也能正常工作。
"""

BASE_CSS = r"""
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#0b0f14; --card:#141a22; --card2:#1a222c; --line:#25313f;
  --fg:#e9eff7; --mut:#8b9cb0; --acc:#3ddc84; --acc-d:#16a35b;
  --blue:#4a9eff; --red:#ff6b6b; --amber:#ffb949;
  --shadow:0 8px 30px rgba(0,0,0,.45);
}
@media (prefers-color-scheme:light){
  :root{
    --bg:#f2f5f9; --card:#ffffff; --card2:#f7f9fc; --line:#e3e9f1;
    --fg:#0e1726; --mut:#64748b; --acc:#0ea864; --acc-d:#0b8a51;
    --blue:#2563eb; --red:#dc2626; --amber:#c2760c;
    --shadow:0 8px 26px rgba(15,23,42,.08);
  }
}
html,body{margin:0;padding:0}
body{
  background:var(--bg); color:var(--fg);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  -webkit-font-smoothing:antialiased;
}
button{font-family:inherit;font-size:inherit;cursor:pointer;border:none;outline:none}
a{color:var(--blue);text-decoration:none}
.wrap{max-width:760px;margin:0 auto;padding:22px 16px calc(30px + env(safe-area-inset-bottom))}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:var(--shadow);margin-bottom:14px}
.mut{color:var(--mut)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.hidden{display:none!important}
"""

# ---------------------------------------------------------------- 手机端 ----

PHONE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0f14">
<title>碰传 · 发送到 __MAC__</title>
<style>
__BASE__
.wrap{max-width:560px}
header{text-align:center;margin:6px 0 18px}
.logo{font-size:40px;line-height:1;margin-bottom:8px}
h1{font-size:21px;margin:0 0 6px;letter-spacing:.2px}
.sub{color:var(--mut);font-size:13.5px;margin:0}
.drop{
  border:2px dashed var(--line);border-radius:20px;background:var(--card);
  padding:34px 18px;text-align:center;transition:.18s;user-select:none;
}
.drop:active{transform:scale(.985)}
.drop.over{border-color:var(--acc);background:var(--card2);border-style:solid}
.drop .plus{
  width:60px;height:60px;margin:0 auto 12px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:300;
  background:linear-gradient(140deg,var(--acc),var(--acc-d));color:#04140b;
}
.drop .t{font-size:17px;font-weight:600;margin-bottom:5px}
.drop .s{font-size:13px;color:var(--mut)}
.qitem{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-top:10px}
.qtop{display:flex;align-items:center;gap:10px}
.qname{flex:1;min-width:0;font-size:14.5px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.qsize{font-size:12px;color:var(--mut);white-space:nowrap}
.bar{height:5px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:9px}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--acc),var(--blue));transition:width .15s linear;border-radius:4px}
.qst{font-size:12px;color:var(--mut);margin-top:6px;display:flex;justify-content:space-between}
.qitem.ok{border-color:var(--acc)}
.qitem.ok .qst{color:var(--acc)}
.qitem.err{border-color:var(--red)}
.qitem.err .qst{color:var(--red)}
.sect-title{font-size:13px;color:var(--mut);margin:20px 4px 9px;letter-spacing:.4px}
textarea{
  width:100%;background:var(--card2);color:var(--fg);border:1px solid var(--line);
  border-radius:11px;padding:11px;font-family:inherit;font-size:15px;resize:vertical;outline:none
}
textarea:focus{border-color:var(--blue)}
.btn{
  display:block;width:100%;margin-top:10px;padding:13px;border-radius:12px;
  background:var(--card2);color:var(--fg);border:1px solid var(--line);
  font-weight:600;font-size:15px;transition:.15s
}
.btn.primary{background:linear-gradient(140deg,var(--acc),var(--acc-d));color:#04140b;border:none}
.btn:active{transform:scale(.985)}
.links{text-align:center;margin:22px 0 10px;font-size:13.5px}
footer{text-align:center;font-size:11.5px;color:var(--mut);margin-top:16px;word-break:break-all}
.toast{
  position:fixed;left:50%;bottom:34px;transform:translate(-50%,20px);
  background:var(--card);border:1px solid var(--acc);color:var(--fg);
  padding:11px 18px;border-radius:12px;font-size:14px;box-shadow:var(--shadow);
  opacity:0;transition:.25s;pointer-events:none;z-index:99;max-width:88vw;text-align:center
}
.toast.show{opacity:1;transform:translate(-50%,0)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">📲</div>
    <h1>发送到 __MAC__</h1>
    <p class="sub">已连上接收服务，文件将直接存入 Mac</p>
  </header>

  <div class="drop" id="drop">
    <div class="plus">＋</div>
    <div class="t">选择要传的文件</div>
    <div class="s">照片 · 视频 · 文档，可多选</div>
  </div>
  <input type="file" id="file" multiple hidden>

  <div class="sect-title hidden" id="qtitle">传输队列</div>
  <div id="queue"></div>

  <div class="sect-title">发送文字 / 链接</div>
  <div class="card">
    <textarea id="txt" rows="3" placeholder="粘贴文字或网址，点下方按钮发到 Mac…"></textarea>
    <button class="btn primary" id="sendtxt">发送到 Mac</button>
  </div>

  <div class="links"><a href="/f/__TOKEN__">查看 Mac 上已收到的文件 →</a></div>
  <footer>__URL__</footer>
</div>
<div class="toast" id="toast"></div>

<script>
var TOKEN = "__TOKEN__";
var $ = function(s){ return document.querySelector(s); };
var drop = $('#drop'), input = $('#file'), queue = $('#queue');

function human(n){
  if (n < 1024) return n + ' B';
  if (n < 1048576) return (n/1024).toFixed(1) + ' KB';
  if (n < 1073741824) return (n/1048576).toFixed(1) + ' MB';
  return (n/1073741824).toFixed(2) + ' GB';
}
function toast(msg, ms){
  var t = $('#toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(t._h); t._h = setTimeout(function(){ t.classList.remove('show'); }, ms || 2600);
}
function buzz(p){ try { navigator.vibrate && navigator.vibrate(p); } catch(e){} }

drop.addEventListener('click', function(){ input.click(); });
input.addEventListener('change', function(){
  if (input.files && input.files.length) enqueue(input.files);
  input.value = '';
});
['dragenter','dragover'].forEach(function(ev){
  drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.add('over'); });
});
['dragleave','drop'].forEach(function(ev){
  drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.remove('over'); });
});
drop.addEventListener('drop', function(e){
  if (e.dataTransfer && e.dataTransfer.files.length) enqueue(e.dataTransfer.files);
});

var chain = Promise.resolve();
function enqueue(list){
  $('#qtitle').classList.remove('hidden');
  for (var i = 0; i < list.length; i++) {
    (function(f){
      var row = makeRow(f);
      chain = chain.then(function(){ return send(f, row); });
    })(list[i]);
  }
}
function makeRow(f){
  var d = document.createElement('div');
  d.className = 'qitem';
  d.innerHTML = '<div class="qtop"><div class="qname"></div><div class="qsize">' + human(f.size) + '</div></div>'
              + '<div class="bar"><i></i></div><div class="qst"><span>等待中</span><span>0%</span></div>';
  d.querySelector('.qname').textContent = f.name;
  queue.insertBefore(d, queue.firstChild);
  return d;
}
function send(file, row){
  return new Promise(function(resolve){
    var bar = row.querySelector('.bar i'), st = row.querySelector('.qst span'), pct = row.querySelectorAll('.qst span')[1];
    var xhr = new XMLHttpRequest();
    xhr.open('PUT', '/api/upload?k=' + encodeURIComponent(TOKEN));
    xhr.setRequestHeader('X-File-Name', encodeURIComponent(file.name));
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.upload.onprogress = function(e){
      if (!e.lengthComputable) return;
      var p = Math.round(e.loaded / e.total * 100);
      bar.style.width = p + '%'; pct.textContent = p + '%';
      st.textContent = '传输中';
    };
    xhr.onload = function(){
      if (xhr.status === 200) {
        var r = {}; try { r = JSON.parse(xhr.responseText); } catch(e){}
        row.classList.add('ok'); bar.style.width = '100%'; pct.textContent = '100%';
        st.textContent = '已完成';
        toast('已存入 Mac：' + (r.name || file.name));
        buzz([18, 40, 18]);
      } else {
        row.classList.add('err'); st.textContent = '失败 ' + xhr.status;
        toast('传输失败，请检查 Mac 端是否仍在运行');
      }
      resolve();
    };
    xhr.onerror = function(){
      row.classList.add('err'); st.textContent = '连接中断';
      toast('连接中断，确认手机与 Mac 在同一 Wi-Fi');
      resolve();
    };
    st.textContent = '准备中';
    xhr.send(file);
  });
}

$('#sendtxt').addEventListener('click', function(){
  var v = $('#txt').value.trim();
  if (!v) { toast('没有内容可发送'); return; }
  var btn = this; btn.disabled = true; btn.textContent = '发送中…';
  fetch('/api/text?k=' + encodeURIComponent(TOKEN), {
    method: 'POST', headers: {'Content-Type':'text/plain;charset=UTF-8'}, body: v
  }).then(function(r){
    btn.disabled = false; btn.textContent = '发送到 Mac';
    if (r.ok) { $('#txt').value = ''; toast('已发送'); buzz(18); }
    else toast('发送失败');
  }).catch(function(){
    btn.disabled = false; btn.textContent = '发送到 Mac'; toast('发送失败');
  });
});

if (location.search.indexOf('auto=1') >= 0) {
  setTimeout(function(){ try { input.click(); } catch(e){} }, 500);
}
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- 电脑端 ----

DESK = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NFC碰传 · 控制台</title>
<style>
__BASE__
.wrap{max-width:880px}
.top{display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.top h1{font-size:20px;margin:0;flex:1;min-width:200px}
.dot{width:9px;height:9px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 4px rgba(61,220,132,.16);flex:none}
.dot.off{background:var(--red);box-shadow:0 0 0 4px rgba(255,107,107,.16)}
.grid{display:grid;grid-template-columns:300px 1fr;gap:14px;align-items:start}
@media (max-width:720px){ .grid{grid-template-columns:1fr} }
.h{font-size:13px;color:var(--mut);letter-spacing:.4px;margin:0 0 12px;font-weight:600}
.tabs{display:flex;gap:6px;background:var(--card2);padding:4px;border-radius:10px;margin-bottom:14px}
.tabs button{flex:1;padding:8px;border-radius:7px;background:transparent;color:var(--mut);font-size:13px;font-weight:600}
.tabs button.on{background:var(--card);color:var(--fg);box-shadow:0 1px 4px rgba(0,0,0,.18)}
.qrbox{background:#fff;border-radius:12px;padding:14px;display:flex;align-items:center;justify-content:center}
.qrbox img{width:100%;max-width:220px;height:auto;display:block}
.url{
  margin-top:12px;background:var(--card2);border:1px solid var(--line);border-radius:10px;
  padding:10px 12px;font-size:12.5px;word-break:break-all;line-height:1.5
}
.row{display:flex;gap:9px;margin-top:10px;flex-wrap:wrap}
.row .btn{width:auto;flex:1;margin:0;padding:10px 12px;border-radius:10px;font-size:13.5px}
.btn{display:block;width:100%;margin-top:10px;padding:12px;border-radius:11px;background:var(--card2);color:var(--fg);border:1px solid var(--line);font-weight:600;font-size:14px;transition:.15s}
.btn:hover{border-color:var(--blue)}
.btn:active{transform:scale(.98)}
.btn.primary{background:linear-gradient(140deg,var(--acc),var(--acc-d));color:#04140b;border:none}
.list{max-height:420px;overflow:auto;margin:-4px -4px 0}
.item{display:flex;align-items:center;gap:11px;padding:10px 8px;border-radius:10px;cursor:pointer}
.item:hover{background:var(--card2)}
.ico{width:34px;height:34px;border-radius:9px;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:16px;flex:none}
.item .nm{flex:1;min-width:0;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item .mt{font-size:12px;color:var(--mut);white-space:nowrap;text-align:right}
.empty{text-align:center;color:var(--mut);font-size:13.5px;padding:30px 0}
details{margin-top:8px}
summary{cursor:pointer;font-size:13.5px;font-weight:600;color:var(--blue);outline:none}
details ol{margin:10px 0 0;padding-left:22px;font-size:13.5px;color:var(--mut);line-height:1.9}
details b{color:var(--fg)}
.step{margin-top:14px}
.step+.step{margin-top:16px}
.step .n{display:inline-flex;width:20px;height:20px;border-radius:50%;background:var(--blue);color:#fff;font-size:12px;align-items:center;justify-content:center;margin-right:7px;font-weight:700}
code{background:var(--card2);padding:2px 6px;border-radius:5px;font-size:12.5px;border:1px solid var(--line)}
.conf{font-size:12.5px;color:var(--mut);line-height:2}
.conf b{color:var(--fg);font-weight:600}
.toast{position:fixed;left:50%;bottom:30px;transform:translate(-50%,20px);background:var(--card);border:1px solid var(--acc);padding:11px 18px;border-radius:12px;font-size:14px;box-shadow:var(--shadow);opacity:0;transition:.25s;pointer-events:none;z-index:99}
.toast.show{opacity:1;transform:translate(-50%,0)}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <span class="dot" id="dot"></span>
    <h1>NFC碰传 · __MAC__</h1>
    <button class="btn" style="width:auto;margin:0;padding:9px 14px" id="openfolder">打开收件箱</button>
  </div>

  <div class="grid">
    <div class="card">
      <p class="h">跟遥控器上的 NFC 标签配对</p>
      <div class="tabs">
        <button class="on" data-h="local">局域网名称</button>
        <button data-h="ip">IP 地址</button>
      </div>
      <div class="qrbox"><img id="qr" alt="二维码"></div>
      <div class="url mono" id="url"></div>
      <div class="row">
        <button class="btn" id="copy">复制链接</button>
        <button class="btn" id="saveqr">导出二维码</button>
      </div>
      <div class="conf" id="conf"></div>
    </div>

    <div class="card">
      <p class="h">收件箱 · <span id="count">0</span> 个文件</p>
      <div class="list" id="list"><div class="empty">还没有收到文件</div></div>
      <div class="row">
        <button class="btn" id="refresh">刷新</button>
        <button class="btn" id="clear">清空列表显示</button>
      </div>

      <details>
        <summary>怎么把链接写进遥控器的 NFC 标签？</summary>
        <div class="step"><span class="n">1</span>手机装一个能写标签的 App（安卓/iOS 都推荐 <b>NFC Tools</b>，免费）。</div>
        <div class="step"><span class="n">2</span>打开 App → <b>写入</b> → 添加记录 → 类型选 <b>URL / URI</b>。</div>
        <div class="step"><span class="n">3</span>把上面复制的链接粘贴进去 → 点 <b>写入</b> → 把手机背面贴到遥控器的 NFC 区域，直到提示写入成功。</div>
        <div class="step"><span class="n">4</span>以后手机解锁状态下碰一下遥控器，就会弹出本机的接收页面，选文件即可。</div>
        <div class="step" style="color:var(--amber)">如果提示“标签已锁定/不可写”，说明遥控器里的标签是小米出厂固化的，无法改写。用一个几块钱的 <b>NTAG213 空白贴纸</b> 写好链接贴在遥控器背面，效果完全一样。</div>
      </details>
    </div>
  </div>

  <div class="card">
    <p class="h">更快的玩法（可选）</p>
    <div class="step"><span class="n">1</span><b>iPhone：</b>用「快捷指令」新建个人自动化 → 触发器选 <b>NFC</b> → 扫描遥控器上的标签 → 添加动作「打开 URL」或「获取网页内容」，把上面的链接填进去，勾选“运行前不询问”。这样碰一下就能直接开始传文件，连浏览器都不用点。</div>
    <div class="step"><span class="n">2</span><b>安卓：</b>用 NFC Tools 的“任务”功能，或者 Tasker + NFC 触发，做同样的事。</div>
    <div class="step"><span class="n">3</span>想让网页一打开就自动弹选择框，把链接结尾改成 <code>…?auto=1</code> 这一类写法会在页面加载后自动尝试唤起文件选择。</div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
var TOKEN = "__TOKEN__";
var HOSTS = __HOSTS__;
var $ = function(s){ return document.querySelector(s); };
var cur = 'local';

function toast(m){
  var t = $('#toast'); t.textContent = m; t.classList.add('show');
  clearTimeout(t._h); t._h = setTimeout(function(){ t.classList.remove('show'); }, 2200);
}
function setHost(k){
  cur = k;
  document.querySelectorAll('.tabs button').forEach(function(b){
    b.classList.toggle('on', b.dataset.h === k);
  });
  $('#qr').src = '/api/qr.svg?h=' + k + '&t=' + Date.now();
  $('#url').textContent = HOSTS[k].url;
}
document.querySelectorAll('.tabs button').forEach(function(b){
  b.addEventListener('click', function(){ setHost(b.dataset.h); });
});
$('#copy').addEventListener('click', function(){
  var u = HOSTS[cur].url;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(u).then(function(){ toast('链接已复制'); }, function(){ fallback(u); });
  } else { fallback(u); }
});
function fallback(u){
  var ta = document.createElement('textarea');
  ta.value = u; ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); toast('链接已复制'); } catch(e){ toast('复制失败，请手动选中'); }
  document.body.removeChild(ta);
}
$('#saveqr').addEventListener('click', function(){
  window.open('/api/qr.png?h=' + cur, '_blank');
});
$('#openfolder').addEventListener('click', function(){
  fetch('/api/open?k=' + TOKEN, {method:'POST'}).then(function(){ toast('已在访达中打开'); });
});
$('#refresh').addEventListener('click', load);
$('#clear').addEventListener('click', function(){
  $('#list').innerHTML = '<div class="empty">还没有收到文件</div>';
  toast('仅清空当前显示，文件仍在收件箱里');
});

function human(n){
  if (n < 1024) return n + ' B';
  if (n < 1048576) return (n/1024).toFixed(1) + ' KB';
  if (n < 1073741824) return (n/1048576).toFixed(1) + ' MB';
  return (n/1073741824).toFixed(2) + ' GB';
}
function icon(name){
  var e = (name.split('.').pop() || '').toLowerCase();
  if (['jpg','jpeg','png','gif','heic','webp','bmp','tiff','svg'].indexOf(e) >= 0) return '🖼';
  if (['mp4','mov','avi','mkv','m4v','webm'].indexOf(e) >= 0) return '🎬';
  if (['mp3','wav','m4a','flac','aac'].indexOf(e) >= 0) return '🎵';
  if (['pdf'].indexOf(e) >= 0) return '📕';
  if (['zip','rar','7z','tar','gz'].indexOf(e) >= 0) return '🗜';
  if (['doc','docx','pages'].indexOf(e) >= 0) return '📄';
  if (['xls','xlsx','numbers','csv'].indexOf(e) >= 0) return '📊';
  if (['ppt','pptx','key'].indexOf(e) >= 0) return '📽';
  if (['txt','md','json','xml','html'].indexOf(e) >= 0) return '📃';
  return '📦';
}
function esc(s){ return s.replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

function load(){
  fetch('/api/inbox?k=' + TOKEN).then(function(r){ return r.json(); }).then(function(d){
    $('#dot').classList.toggle('off', !d.running);
    $('#count').textContent = d.files.length;
    $('#conf').innerHTML = '端口 <b>' + d.port + '</b> · 收件箱 <b>' + esc(d.dir) + '</b>'
      + '<br>Bonjour：<b>' + (d.bonjour ? '已广播' : '未开启') + '</b>'
      + ' · 开机自启：<b>' + (d.autostart ? '已开启' : '未开启') + '</b>';
    if (!d.files.length) { return; }
    var h = '';
    d.files.slice(0, 80).forEach(function(f){
      h += '<div class="item" data-n="' + esc(f.name) + '">'
         + '<div class="ico">' + icon(f.name) + '</div>'
         + '<div class="nm">' + esc(f.name) + '</div>'
         + '<div class="mt">' + human(f.size) + '<br>' + f.mtime + '</div></div>';
    });
    $('#list').innerHTML = h;
    document.querySelectorAll('.item').forEach(function(el){
      el.addEventListener('click', function(){
        fetch('/api/reveal?k=' + TOKEN + '&name=' + encodeURIComponent(el.dataset.n), {method:'POST'});
      });
    });
  }).catch(function(){ $('#dot').classList.add('off'); });
}
setHost('local');
load();
setInterval(load, 3000);
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- 文件列表 ----

LIST_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Mac 上的文件</title>
<style>
__BASE__
.item{display:flex;align-items:center;gap:11px;padding:13px 14px;background:var(--card);border:1px solid var(--line);border-radius:13px;margin-bottom:9px}
.item .nm{flex:1;min-width:0;font-size:14.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item .mt{font-size:12px;color:var(--mut);white-space:nowrap}
.ico{width:34px;height:34px;border-radius:9px;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:16px;flex:none}
.empty{text-align:center;color:var(--mut);padding:44px 0;font-size:14px}
h1{font-size:19px;margin:6px 0 16px;text-align:center}
.back{display:block;text-align:center;margin-top:18px;font-size:14px}
</style>
</head>
<body>
<div class="wrap">
  <h1>Mac 上收到的文件</h1>
  __ITEMS__
  <a class="back" href="/t/__TOKEN__">← 返回发送页</a>
</div>
</body>
</html>
"""
