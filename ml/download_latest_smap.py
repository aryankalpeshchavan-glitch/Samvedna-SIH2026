from pathlib import Path
from datetime import datetime, timedelta, timezone
import earthaccess


# ============================================================
# CrisisCore - Download latest SMAP L4 V008 soil moisture
# ============================================================

OUT_DIR = Path("data/raw/soil/smap_l4")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SHORT_NAME = "SPL4SMGP"
VERSION = "008"

# NER approximate bounding box
# west, south, east, north
BBOX = (88.0, 21.0, 98.0, 30.0)


print("=" * 70)
print("CrisisCore - Latest SMAP L4 V008 Downloader")
print("=" * 70)

# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
print("\n[1] Earthdata login...")

auth = earthaccess.login(
    strategy="interactive",
    persist=True
)

print("✓ Earthdata login successful")


# ------------------------------------------------------------
# Search recent period
# ------------------------------------------------------------
now = datetime.now(timezone.utc)

# Search the previous 4 days so we don't miss the latest
# available product because of SMAP latency.
start = now - timedelta(days=4)
end = now

print("\n[2] Searching SMAP L4 V008...")
print(f"Search start: {start.isoformat()}")
print(f"Search end:   {end.isoformat()}")

results = earthaccess.search_data(
    short_name=SHORT_NAME,
    version=VERSION,
    bounding_box=BBOX,
    temporal=(
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
)

print(f"\nGranules found: {len(results)}")


if not results:
    raise RuntimeError(
        "No SMAP L4 V008 granules found in the search window."
    )


# ------------------------------------------------------------
# Display results
# ------------------------------------------------------------
print("\nAvailable granules:")

for i, granule in enumerate(results, start=1):
    print(f"{i:3d}. {granule}")


# ------------------------------------------------------------
# Download
# ------------------------------------------------------------
print("\n[3] Downloading latest SMAP granules...")
print(f"Output directory: {OUT_DIR.resolve()}")

downloaded = earthaccess.download(
    results,
    local_path=str(OUT_DIR)
)

print(f"\nDownloaded/available files: {len(downloaded)}")


# ------------------------------------------------------------
# Final HDF5 inventory
# ------------------------------------------------------------
h5_files = sorted(OUT_DIR.glob("*.h5"))

print("\n[4] Final SMAP HDF5 inventory:")
print(f"Total HDF5 files: {len(h5_files)}")

for f in h5_files:
    size_mb = f.stat().st_size / (1024 * 1024)
    print(f"  {f.name} ({size_mb:.1f} MB)")


print("\n" + "=" * 70)
print("LATEST SMAP DOWNLOAD COMPLETE")
print("=" * 70)