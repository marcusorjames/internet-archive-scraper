import os

# Local path:  OUTPUT_DIR = "/path/to/media"
# Remote path: OUTPUT_DIR = "hostname:/path/to/media"  (uses rsync over SSH)
OUTPUT_DIR = "hostname:/path/to/media"

# Downloads stage here first, enabling resume on interrupted downloads.
# Cleaned up automatically after a successful transfer.
STAGING_DIR = os.path.expanduser("~/.ia-scraper/staging")
