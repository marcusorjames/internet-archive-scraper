# Phase 1: CLI Implementation

## Overview

Phase 1 is a local Python CLI tool that downloads media from Internet Archive and writes it to a configured output directory.

## URL Format

Internet Archive item URLs follow this pattern:

```
https://archive.org/details/<identifier>
https://archive.org/details/<identifier>/<filename>
```

- `identifier` — unique item ID (e.g. `ajc03187_nirvana-1989-09-30`)
- `filename` — optional; when present, only that file is downloaded

## Module Structure

### `scraper.py`

| Function | Input | Output | Description |
|---|---|---|---|
| `parse_ia_url(url)` | Archive.org URL | `(identifier, filename\|None)` | Extracts item ID and optional filename from URL |
| `download_from_ia(identifier, filename)` | Item ID + optional filename | Local path string | Downloads via `internetarchive` library |
| `main(url)` | Archive.org URL | — | CLI entrypoint; calls parse → download |

### `config.py`

Single variable: `OUTPUT_DIR`. Set this to the absolute path of the directory where files should be saved.

## Running Locally vs On a Remote Server

The script behaves identically in both cases — `OUTPUT_DIR` is the only difference:

| Context | `OUTPUT_DIR` |
|---|---|
| Running locally | Any local path |
| SSH'd into a remote server | Target directory on that server |

## Phase 2 Roadmap

Phase 2 adds `server.py` — a FastAPI HTTP endpoint that wraps the same `scraper.py` functions. Deploy it on a remote server and use a browser bookmarklet to POST any Internet Archive page URL to it. Files land immediately without SSH.

```
POST /download
{"url": "https://archive.org/details/..."}
→ {"status": "ok", "path": "/path/to/media/identifier"}
```

Bookmarklet:
```javascript
javascript:(function(){fetch('http://your-server:8000/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:location.href})}).then(r=>r.json()).then(d=>alert(d.status))})();
```
