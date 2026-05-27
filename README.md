# 🌙 Moon Dev's Computer Cleaner

**Stop paying for disk cleaner apps.** This is a free, dead-simple, browser-based tool to find and **hard delete** the biggest files on your computer.

Built by [Moon Dev](https://github.com/moondevonyt) with Claude Code — under 500 lines of Python.

---

## The Problem

Apps like DaisyDisk, CleanMyMac, and other "disk cleaner" tools cost **$10–$100+** just to do something your computer can already do: list your biggest files so you can delete them.

This tool does exactly that — for free, in your browser, with no telemetry, no subscriptions, no nonsense.

## What It Does

- 🔍 **Scans** any folder on your computer for big files (default: 500 MB and up)
- 📊 **Shows live disk stats** — total / used / free / % used with a visual bar
- ✅ **Select what you want gone** via checkboxes
- 🗑 **Hard deletes** the files you pick — permanently, no Trash, no undo
- 🛡 **Safety**: refuses to follow symlinks, double-checks each file before deleting

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/moondevonyt/computer-cleaner-free-up-space.git
cd computer-cleaner-free-up-space
```

### 2. Set up a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run it
```bash
python main.py
```

### 5. Open your browser
Go to **http://127.0.0.1:8000**

That's it.

## How to Use

1. **Set your scan path** — defaults to your home directory. Point it anywhere.
2. **Set the minimum file size in MB** — defaults to 500 MB. Lower it to find smaller files, raise it to only see the chonkers.
3. **Hit `🔍 scan`** — wait a moment while it walks the file tree.
4. **Review the table** — files sorted biggest first, with paths and sizes.
5. **Tick the checkboxes** for what you want gone.
6. **Hit `🗑 hard delete selected`** — confirm the popup, and the files are wiped.

The disk usage bar updates after every delete so you can see exactly how much space you freed.

## ⚠️ Warning

**Hard delete is PERMANENT.** Files do NOT go to your trash/recycle bin. Once you click delete and confirm, they are gone for good.

Double-check before you click. Don't delete things you don't recognize. Don't run this as root/admin unless you know exactly what you're doing.

## Configuration

Tweak these at the top of `main.py`:

```python
MIN_FILE_SIZE_MB = 500            # Default minimum file size
DEFAULT_SCAN_PATH = str(Path.home())  # Default folder to scan
SKIP_HIDDEN_DIRS = True           # Skip .git, .cache, etc. for speed
HOST = "127.0.0.1"
PORT = 8000
```

## Tech Stack

- **FastAPI** — the web framework
- **Uvicorn** — the ASGI server
- **Vanilla HTML/CSS/JS** — no build step, no npm, no nonsense

## License

Do whatever you want with it. 🌙

---

*Made by Moon Dev — follow along at [@moondevonyt](https://twitter.com/moondevonyt)*
