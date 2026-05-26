import os

# ── Runtime detection ──────────────────────────────────────────────────

IS_VERCEL = bool(os.getenv("VERCEL")) or os.getenv("VERCEL_ENV") is not None
"""True when running on Vercel's serverless platform."""

UPLOAD_DIR = "/tmp/uploads" if IS_VERCEL else "uploads"
OUTPUT_DIR = "/tmp/outputs" if IS_VERCEL else "outputs"


def _safe_remove(filepath: str):
    """Delete a file silently — no error if it doesn't exist."""
    try:
        os.remove(filepath)
        print(f"[Cleanup] Removed {filepath}")
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"[Cleanup] Failed to remove {filepath}: {e}")


def _cleanup_dir(directory: str):
    """Remove all files in a directory."""
    if not os.path.isdir(directory):
        return
    count = 0
    for fname in os.listdir(directory):
        _safe_remove(os.path.join(directory, fname))
        count += 1
    if count:
        print(f"[Cleanup] Removed {count} files from {directory}")
