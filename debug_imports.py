
import sys
from pathlib import Path

# Mimic realesrgan.py path logic
script_dir = Path("d:/Hackathon Projects/CIT_Datathon/PropVisionAI/src/enhancement")
PROJECT_ROOT = script_dir.parent.parent.absolute()
BASI_SR_PATH = str(PROJECT_ROOT / "third_party" / "BasicSR")
REAL_ESRGAN_PATH = str(PROJECT_ROOT / "third_party" / "Real-ESRGAN")

print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"BASI_SR_PATH: {BASI_SR_PATH}")
print(f"REAL_ESRGAN_PATH: {REAL_ESRGAN_PATH}")

sys.path.append(BASI_SR_PATH)
sys.path.append(REAL_ESRGAN_PATH)

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    print("SUCCESS: Both imported")
except Exception as e:
    import traceback
    print("FAILED: Import error")
    traceback.print_exc()
