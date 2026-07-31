#!/usr/bin/env python3
"""
Quick video vault scale-up - generate 7 more videos to reach 10 total.
Runs once then exits (not a daemon).
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path("C:/github hunter/MoneyPrinterTurbo")
PY = ROOT / ".venv-mpt/Scripts/python.exe"
VAULT = Path("C:/github hunter/video_vault")

SUBJECTS = [
    "The 2-minute rule that ends procrastination",
    "How compound interest actually works, explained simply",
    "Signs you are ready to start investing",
    "The psychology of saving money without feeling poor",
    "What billionaires actually do with their time",
    "Passive income ideas that work in 2026",
    "Why most people never get rich (and how to be different)",
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

if not PY.exists():
    log("⚠ MoneyPrinterTurbo venv not found - skipping video generation")
    sys.exit(0)

current_count = len(list(VAULT.glob("*.mp4")))
log(f"📊 Current vault: {current_count} videos")

if current_count >= 10:
    log(f"✓ Vault already at target size ({current_count}/10)")
    sys.exit(0)

needed = min(7, 10 - current_count)
log(f"🎬 Generating {needed} more videos...")

try:
    subprocess.run(
        [str(PY), "video_factory.py", "--count", str(needed)],
        cwd=str(ROOT),
        timeout=needed * 900,  # 15min per video
        check=True
    )
    
    final_count = len(list(VAULT.glob("*.mp4")))
    log(f"")
    log(f"✅ Video generation complete")
    log(f"📊 Vault: {current_count} → {final_count} videos")
    
except subprocess.TimeoutExpired:
    log("⚠ Video generation timed out - partial batch may be complete")
except Exception as e:
    log(f"❌ Error: {e}")
    sys.exit(1)
