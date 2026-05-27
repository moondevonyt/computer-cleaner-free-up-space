"""
Moon Dev's Computer Cleaner - Free Up Space
A simple FastAPI app to find and HARD DELETE the biggest files on your system.
Like DaisyDisk but in your browser, dead simple.
"""

import os
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ============================================================
# Moon Dev's settings - tweak these to your taste
# ============================================================
MIN_FILE_SIZE_MB = 500            # Only show files at or above this size
DEFAULT_SCAN_PATH = str(Path.home())  # Where to start scanning
SKIP_HIDDEN_DIRS = True           # Skip .git, .Trash, .cache, etc. for speed
HOST = "127.0.0.1"
PORT = 8000
# ============================================================

app = FastAPI(title="Moon Dev's Computer Cleaner")


class DeleteRequest(BaseModel):
    paths: List[str]


def walk_for_big_files(root_path: str, min_bytes: int):
    """Walk the tree and return (path, size) tuples for regular files >= min_bytes.
    Skips symlinks entirely so what you see is what you delete."""
    results = []
    for root, dirs, files in os.walk(root_path, followlinks=False):
        if SKIP_HIDDEN_DIRS:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            full = os.path.join(root, name)
            # lstat = don't follow symlinks. We only want REAL files.
            try:
                st = os.lstat(full)
            except OSError:
                continue
            # skip symlinks entirely - deleting a symlink doesn't free its target
            import stat as _stat
            if _stat.S_ISLNK(st.st_mode):
                continue
            if not _stat.S_ISREG(st.st_mode):
                continue
            size = st.st_size
            if size >= min_bytes:
                results.append((full, size))
    return results


@app.get("/scan")
def scan(path: str = DEFAULT_SCAN_PATH, min_mb: int = MIN_FILE_SIZE_MB):
    print(f"🌙 Moon Dev scanning '{path}' for files >= {min_mb} MB ...")
    min_bytes = min_mb * 1024 * 1024
    raw = walk_for_big_files(path, min_bytes)
    raw.sort(key=lambda x: x[1], reverse=True)
    files = [
        {"path": p, "size": s, "size_mb": round(s / (1024 * 1024), 2)}
        for p, s in raw
    ]
    total_mb = round(sum(f["size_mb"] for f in files), 2)
    # disk stats for whichever drive the scan path lives on
    du = shutil.disk_usage(path)
    disk = {
        "total_bytes": du.total,
        "used_bytes": du.used,
        "free_bytes": du.free,
        "percent_used": round(du.used / du.total * 100, 1) if du.total else 0,
    }
    print(
        f"🌙 Moon Dev found {len(files)} files, total {total_mb} MB | "
        f"disk: {du.used / 1e9:.1f} GB used / {du.total / 1e9:.1f} GB total "
        f"({disk['percent_used']}%)"
    )
    return {
        "files": files,
        "count": len(files),
        "scan_path": path,
        "min_mb": min_mb,
        "total_mb": total_mb,
        "disk": disk,
    }


@app.post("/delete")
def delete(req: DeleteRequest):
    deleted, failed = [], []
    print(f"🌙 Moon Dev got delete request for EXACTLY {len(req.paths)} file(s):")
    for p in req.paths:
        print(f"   - {p}")
    for p in req.paths:
        # belt-and-suspenders: verify it's a real file before removing.
        # os.path.isfile follows symlinks; os.path.islink catches dangling links.
        # If a directory snuck in here, os.remove would fail anyway, but we
        # short-circuit with a clear error.
        if os.path.islink(p):
            failed.append({"path": p, "error": "refusing to delete symlink"})
            print(f"🌙 Moon Dev SKIPPED symlink: {p}")
            continue
        if not os.path.isfile(p):
            failed.append({"path": p, "error": "not a regular file (gone, dir, or special)"})
            print(f"🌙 Moon Dev SKIPPED non-file: {p}")
            continue
        print(f"🌙 Moon Dev HARD DELETING: {p}")
        try:
            os.remove(p)
            deleted.append(p)
        except OSError as e:
            print(f"🌙 Moon Dev FAILED to delete {p}: {e}")
            failed.append({"path": p, "error": str(e)})
    print(f"🌙 Moon Dev deleted {len(deleted)} files, {len(failed)} failed")
    # snapshot disk usage on the root volume so the UI can show freed space
    du = shutil.disk_usage("/")
    disk = {
        "total_bytes": du.total,
        "used_bytes": du.used,
        "free_bytes": du.free,
        "percent_used": round(du.used / du.total * 100, 1) if du.total else 0,
    }
    return {"deleted": deleted, "failed": failed, "disk": disk}


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML.replace("__DEFAULT_PATH__", DEFAULT_SCAN_PATH).replace(
        "__DEFAULT_MIN_MB__", str(MIN_FILE_SIZE_MB)
    )


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>🌙 Moon Dev's Computer Cleaner</title>
<style>
  :root {
    --bg: #000000;
    --panel: #050a05;
    --row: #0a140a;
    --border: #1f4a1f;
    --text: #c8ffc8;
    --muted: #5a8a5a;
    --accent: #00ff41;     /* matrix neon green */
    --gold: #aaff00;       /* electric lime for sizes */
    --danger: #ff3939;
    --good: #00ff41;
    --glow: 0 0 6px rgba(0, 255, 65, 0.55);
  }
  * { box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    margin: 0;
    padding: 20px;
  }
  h1 {
    color: var(--accent);
    margin: 0 0 6px 0;
    text-shadow: var(--glow);
    letter-spacing: 1px;
  }
  .sub { color: var(--muted); margin-bottom: 18px; }
  .controls {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 14px;
    border-radius: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    margin-bottom: 14px;
  }
  label { color: var(--muted); font-size: 13px; }
  input[type=text], input[type=number] {
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 8px 10px;
    font-family: inherit;
    border-radius: 4px;
  }
  input[type=text] { width: 420px; }
  input[type=number] { width: 90px; }
  button {
    background: var(--accent);
    color: #000;
    border: 1px solid var(--accent);
    padding: 9px 16px;
    cursor: pointer;
    font-family: inherit;
    font-weight: bold;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: var(--glow);
  }
  button:hover { filter: brightness(1.15); }
  button.danger {
    background: #000;
    color: var(--danger);
    border-color: var(--danger);
    box-shadow: 0 0 6px rgba(255, 57, 57, 0.55);
  }
  button.danger:hover { background: var(--danger); color: #000; }
  button:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }
  .status {
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 14px;
    font-size: 13px;
    border: 1px solid var(--border);
  }
  .status.scan { background: #0a1f0a; border-color: #1f4a1f; color: var(--accent); }
  .status.error { background: #2a0808; border-color: #5a1414; color: var(--danger); }
  .status.success { background: #0a2a0a; border-color: #1f6a1f; color: var(--accent); }
  .selected-info { color: var(--gold); margin-left: auto; font-weight: bold; }
  .disk-stats {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 14px;
    display: none;
  }
  .disk-stats.show { display: block; }
  .disk-row {
    display: flex;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }
  .disk-stat { display: flex; flex-direction: column; gap: 2px; }
  .disk-stat .label {
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .disk-stat .value {
    font-size: 18px;
    font-weight: bold;
    color: var(--accent);
    text-shadow: var(--glow);
  }
  .disk-stat.free .value { color: var(--accent); }
  .disk-stat.used .value { color: var(--gold); }
  .disk-stat.total .value { color: var(--text); text-shadow: none; }
  .disk-bar {
    background: #0a140a;
    border: 1px solid var(--border);
    border-radius: 4px;
    height: 14px;
    overflow: hidden;
    position: relative;
  }
  .disk-bar-fill {
    background: linear-gradient(90deg, var(--accent), var(--gold));
    height: 100%;
    transition: width 0.4s ease;
    box-shadow: var(--glow);
  }
  .disk-bar-fill.danger {
    background: linear-gradient(90deg, var(--gold), var(--danger));
    box-shadow: 0 0 6px rgba(255, 57, 57, 0.55);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  th, td {
    padding: 9px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }
  th {
    color: var(--accent);
    background: var(--row);
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
  }
  tr:hover td { background: var(--row); }
  td.size {
    color: var(--gold);
    text-align: right;
    font-weight: bold;
    white-space: nowrap;
  }
  td.path {
    font-family: inherit;
    word-break: break-all;
  }
  .empty { padding: 40px; text-align: center; color: var(--muted); }
  .footer { color: var(--muted); font-size: 12px; margin-top: 18px; }
</style>
</head>
<body>
  <h1>🌙 Moon Dev's Computer Cleaner</h1>
  <div class="sub">find your biggest files. select them. nuke them. free up space.</div>

  <div class="controls">
    <label>scan path:</label>
    <input type="text" id="path" value="__DEFAULT_PATH__">
    <label>min MB:</label>
    <input type="number" id="minmb" value="__DEFAULT_MIN_MB__" min="1">
    <button onclick="scan()" id="scanBtn">🔍 scan</button>
    <button class="danger" onclick="deleteSelected()" id="deleteBtn" disabled>🗑 hard delete selected</button>
    <span class="selected-info" id="selInfo"></span>
  </div>

  <div id="status" class="status scan">🌙 ready. hit scan to find the chonky boys.</div>

  <div id="diskStats" class="disk-stats">
    <div class="disk-row">
      <div class="disk-stat total"><span class="label">total disk</span><span class="value" id="diskTotal">—</span></div>
      <div class="disk-stat used"><span class="label">used</span><span class="value" id="diskUsed">—</span></div>
      <div class="disk-stat free"><span class="label">free / available</span><span class="value" id="diskFree">—</span></div>
      <div class="disk-stat"><span class="label">% used</span><span class="value" id="diskPct">—</span></div>
    </div>
    <div class="disk-bar"><div class="disk-bar-fill" id="diskBar" style="width:0%"></div></div>
  </div>

  <table id="table">
    <thead>
      <tr>
        <th style="width:40px;"><input type="checkbox" id="selectAll" onclick="toggleAll(this)"></th>
        <th style="width:120px; text-align:right;">size</th>
        <th>path</th>
      </tr>
    </thead>
    <tbody id="tbody">
      <tr><td colspan="3" class="empty">no scan yet — click scan to begin</td></tr>
    </tbody>
  </table>

  <div class="footer">🌙 moon dev's computer cleaner — hard delete is permanent. no trash. no undo.</div>

<script>
  let files = [];

  function fmtSize(mb) {
    if (mb >= 1024 * 1024) return (mb / (1024 * 1024)).toFixed(2) + ' TB';
    if (mb >= 1024) return (mb / 1024).toFixed(2) + ' GB';
    return mb.toFixed(2) + ' MB';
  }

  function fmtBytes(b) {
    const tb = b / (1024 ** 4);
    if (tb >= 1) return tb.toFixed(2) + ' TB';
    const gb = b / (1024 ** 3);
    if (gb >= 1) return gb.toFixed(2) + ' GB';
    const mb = b / (1024 ** 2);
    return mb.toFixed(2) + ' MB';
  }

  function renderDisk(d) {
    document.getElementById('diskTotal').textContent = fmtBytes(d.total_bytes);
    document.getElementById('diskUsed').textContent = fmtBytes(d.used_bytes);
    document.getElementById('diskFree').textContent = fmtBytes(d.free_bytes);
    document.getElementById('diskPct').textContent = d.percent_used + '%';
    const bar = document.getElementById('diskBar');
    bar.style.width = d.percent_used + '%';
    bar.classList.toggle('danger', d.percent_used >= 85);
    document.getElementById('diskStats').classList.add('show');
  }

  function setStatus(msg, type) {
    const s = document.getElementById('status');
    s.className = 'status ' + type;
    s.textContent = msg;
  }

  async function scan() {
    const path = document.getElementById('path').value.trim();
    const min_mb = document.getElementById('minmb').value;
    if (!path) { setStatus('🌙 enter a path first', 'error'); return; }
    const scanBtn = document.getElementById('scanBtn');
    scanBtn.disabled = true;
    setStatus(`🌙 scanning ${path} for files >= ${min_mb} MB ... this can take a while on big drives`, 'scan');
    const res = await fetch(`/scan?path=${encodeURIComponent(path)}&min_mb=${min_mb}`);
    scanBtn.disabled = false;
    if (!res.ok) {
      setStatus(`🌙 scan failed: HTTP ${res.status}`, 'error');
      return;
    }
    const data = await res.json();
    files = data.files;
    if (data.disk) renderDisk(data.disk);
    renderTable();
    setStatus(`🌙 found ${data.count} files >= ${data.min_mb} MB — total ${fmtSize(data.total_mb)}`, 'success');
  }

  function renderTable() {
    const tbody = document.getElementById('tbody');
    if (!files.length) {
      tbody.innerHTML = '<tr><td colspan="3" class="empty">nothing found 🌙</td></tr>';
      document.getElementById('selectAll').checked = false;
      updateSelected();
      return;
    }
    tbody.innerHTML = files.map((f, i) => `
      <tr>
        <td><input type="checkbox" class="rowcb" data-idx="${i}" onchange="updateSelected()"></td>
        <td class="size">${fmtSize(f.size_mb)}</td>
        <td class="path">${escapeHtml(f.path)}</td>
      </tr>
    `).join('');
    document.getElementById('selectAll').checked = false;
    updateSelected();
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function toggleAll(cb) {
    document.querySelectorAll('.rowcb').forEach(c => c.checked = cb.checked);
    updateSelected();
  }

  function updateSelected() {
    const checked = document.querySelectorAll('.rowcb:checked');
    document.getElementById('deleteBtn').disabled = checked.length === 0;
    let totalMb = 0;
    checked.forEach(c => totalMb += files[c.dataset.idx].size_mb);
    document.getElementById('selInfo').textContent =
      checked.length ? `${checked.length} selected — ${fmtSize(totalMb)}` : '';
  }

  async function deleteSelected() {
    const checked = [...document.querySelectorAll('.rowcb:checked')];
    const paths = checked.map(c => files[c.dataset.idx].path);
    const totalMb = checked.reduce((acc, c) => acc + files[c.dataset.idx].size_mb, 0);
    if (!confirm(`🌙 HARD DELETE ${paths.length} files (${fmtSize(totalMb)})?\n\nThis is PERMANENT — files do NOT go to trash.`)) return;
    setStatus(`🌙 hard deleting ${paths.length} files ...`, 'scan');
    document.getElementById('deleteBtn').disabled = true;
    const res = await fetch('/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({paths})
    });
    const data = await res.json();
    const deletedSet = new Set(data.deleted);
    files = files.filter(f => !deletedSet.has(f.path));
    if (data.disk) renderDisk(data.disk);
    renderTable();
    if (data.failed.length) {
      const errs = data.failed.map(f => `  ${f.path}: ${f.error}`).join('\n');
      setStatus(`🌙 deleted ${data.deleted.length}, ${data.failed.length} failed. see console.`, 'error');
      console.error('🌙 Moon Dev failed deletes:\n' + errs);
    } else {
      setStatus(`🌙 deleted ${data.deleted.length} files. space freed.`, 'success');
    }
  }
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    print(f"🌙 Moon Dev's Computer Cleaner starting on http://{HOST}:{PORT}")
    print(f"🌙 default scan path: {DEFAULT_SCAN_PATH}")
    print(f"🌙 default min file size: {MIN_FILE_SIZE_MB} MB")
    uvicorn.run(app, host=HOST, port=PORT)
