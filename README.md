# Internet Archive Scraper

Download media from [Internet Archive](https://archive.org) to a local or remote directory.

## Quick Start

```bash
direnv allow
make install
```

Copy the example config and set `OUTPUT_DIR` to wherever you want files saved:

```bash
cp config.example.py config.py
```

```python
# Local
OUTPUT_DIR = "/path/to/media"
# Remote (rsync over SSH)
OUTPUT_DIR = "hostname:/path/to/media"
```

Then run:

```bash
# Download a single file
python scraper.py https://archive.org/details/ajc03187_nirvana-1989-09-30/Nirvana1989-09-30t01.flac

# Download an entire item (all files)
python scraper.py https://archive.org/details/ajc03187_nirvana-1989-09-30
```

Files are saved to `OUTPUT_DIR/<item-identifier>/`.

## Configuration

| Variable     | Description                                    |
|--------------|------------------------------------------------|
| `OUTPUT_DIR` | Absolute path where downloaded files are saved |

## Running on a Remote Server

SSH into the server, clone this repo, set `OUTPUT_DIR` to the target directory, and run the script directly. No file transfer needed.

## Development

```bash
# Install all dependencies including dev tools
make install

# Run tests with coverage
make test

# Check syntax
make lint

# Trigger CI on GitHub without a commit
make ci
```

## Roadmap

- **Phase 2**: HTTP server endpoint + browser bookmarklet — send any Internet Archive page to your server with one click, without needing to SSH in.
