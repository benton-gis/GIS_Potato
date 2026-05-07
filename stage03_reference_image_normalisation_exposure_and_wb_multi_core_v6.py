r"""
V6 HPC Optimised Version
Batch + Reduced Overhead

python stage03_reference_image_normalisation_exposure_and_wb_multi_core_v6.py
"""

import rawpy
import numpy as np
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

# ======================
# CPU CONTROL (HPC TUNED)
# ======================

max_available = multiprocessing.cpu_count()
num_workers = min(32, max_available)   # ✅ higher safe ceiling

print(f"Using {num_workers}/{max_available} CPU cores")

# ======================
# BATCH SETTINGS (KEY!)
# ======================

BATCH_SIZE = 25   # ✅ critical tuning knob (20–50 ideal)

# ======================
# SETTINGS
# ======================

input_folder = r"H:\_RPA_Processing\Stage0\FPC_CARBON2_RTK3_20260505_2\DCIM"
reference_image = r"H:\_RPA_Processing\Stage0\FPC_CARBON2_RTK3_20260505_2\DCIM\DJI_202605051053_002_FMBAerialOperations-mcalinden1ffpc\DJI_20260505105926_0164_V.DNG"

use_percentile = True
percentile_value = 50

global_ev_adjust = 0.0

clamp_ev = True
min_ev = -2.0
max_ev = 2.0

skip_reference_xmp = True

# ======================
# WHITE BALANCE
# ======================

USE_REFERENCE_WB = True
USE_FIXED_WB_5500K = False
WB_TINT = 10

# ======================
# CLIP SAFETY
# ======================

enable_clip_protection = True

highlight_percentile = 99.8
shadow_percentile = 0.2

white_level = 65535
black_level = 0

highlight_headroom = 0.98
shadow_headroom = 1.5

max_safety_iterations = 10
ev_step_back = 0.1

# ======================
# FILE LIST
# ======================

files = []
for root, _, filenames in os.walk(input_folder):
    for f in filenames:
        if f.lower().endswith(".dng"):
            files.append(os.path.join(root, f))

files = sorted(files)
print(f"Found {len(files)} DNG files")

# ======================
# SPLIT INTO BATCHES ✅
# ======================

def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

batches = list(chunk_list(files, BATCH_SIZE))
print(f"Total batches: {len(batches)}")

# ======================
# WB FIX (STABLE)
# ======================

def get_reference_wb(path):
    with rawpy.imread(path) as raw:
        wb = np.array(raw.camera_whitebalance, dtype=np.float32)
        wb[wb <= 0] = wb[1]
        wb = wb / wb[1]
        return wb.tolist()

ref_wb = get_reference_wb(reference_image) if USE_REFERENCE_WB else None
if ref_wb:
    print(f"Reference WB: {ref_wb}")

# ======================
# MEASURE
# ======================

def measure_stats(raw):

    if USE_REFERENCE_WB and ref_wb:
        rgb = raw.postprocess(
            use_camera_wb=False,
            use_auto_wb=False,
            user_wb=ref_wb,
            no_auto_bright=True,
            half_size=True,
            output_bps=16
        )
    elif USE_FIXED_WB_5500K:
        wb = raw.daylight_whitebalance
        rgb = raw.postprocess(
            use_camera_wb=False,
            use_auto_wb=False,
            user_wb=wb,
            no_auto_bright=True,
            half_size=True,
            output_bps=16
        )
    else:
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=True,
            half_size=True,
            output_bps=16
        )

    brightness = np.percentile(rgb, percentile_value)
    highlights = np.percentile(rgb, highlight_percentile)
    shadows = np.percentile(rgb, shadow_percentile)

    return brightness, highlights, shadows

# ======================
# REFERENCE BRIGHTNESS
# ======================

with rawpy.imread(reference_image) as raw:
    ref_brightness, _, _ = measure_stats(raw)

print(f"Reference brightness: {ref_brightness:.2f}")

# ======================
# CLIP SAFETY
# ======================

def apply_clip_safety(ev, highlights, shadows):
    for _ in range(max_safety_iterations):
        scale = 2 ** ev
        projected_high = highlights * scale
        projected_low = shadows * scale

        if projected_high > white_level * highlight_headroom:
            ev -= ev_step_back
            continue
        if projected_low < shadow_headroom:
            ev += ev_step_back
            continue
        break
    return ev

# ======================
# XMP
# ======================

def create_xmp(ev):
    return f"""<x:xmpmeta xmlns:x='adobe:ns:meta/'>
<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
<rdf:Description xmlns:crs='http://ns.adobe.com/camera-raw-settings/1.0/'>
<crs:Exposure2012>{ev:.4f}</crs:Exposure2012>
</rdf:Description>
</rdf:RDF>
</x:xmpmeta>"""

# ======================
# ✅ BATCH WORKER (BIG WIN)
# ======================

def process_batch(batch):

    for path in batch:
        try:
            if skip_reference_xmp and path == reference_image:
                continue

            with rawpy.imread(path) as raw:
                brightness, highlights, shadows = measure_stats(raw)

            ratio = ref_brightness / brightness if brightness > 0 else 1.0
            ev = np.log2(ratio)

            ev = max(min(ev, max_ev), min_ev)
            ev = apply_clip_safety(ev, highlights, shadows)

            xmp_path = os.path.splitext(path)[0] + ".xmp"
            with open(xmp_path, "w") as f:
                f.write(create_xmp(ev))

        except Exception:
            print(f"⚠️ Error: {path}")

# ======================
# ✅ PARALLEL EXECUTION
# ======================

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=num_workers) as executor:

        for _ in tqdm(
            executor.map(process_batch, batches),
            total=len(batches),
            desc="Processing batches"
        ):
            pass

print("✅ COMPLETE (V6 HPC)")
