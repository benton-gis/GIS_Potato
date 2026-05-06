import rawpy
import numpy as np
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# ======================
# CPU CONTROL
# ======================

num_workers = 6  # 👈 SET THIS

max_available = multiprocessing.cpu_count()
num_workers = min(num_workers, max_available)

print(f"Using {num_workers}/{max_available} CPU cores")

# ======================
# SETTINGS
# ======================

input_folder = r"F:\_RPA_Processing\Stage0\PROJECT_NAME"
reference_image = r"F:\_RPA_Processing\Stage0\PROJECT_NAME\SUB_FOLDER\DJI_SUB_FOLDER\DJI_20260429132554_0070_V.DNG"

use_percentile = True
percentile_value = 50

global_ev_adjust = 0.0

clamp_ev = True
min_ev = -2.0
max_ev = 2.0

skip_reference_xmp = True

# ======================
# CLIP SAFETY
# ======================

enable_clip_protection = True
strict_protection = False

highlight_percentile = 99.8
shadow_percentile = 0.2

white_level = 65535
black_level = 0

highlight_headroom = 0.98
shadow_headroom = 1.5

if strict_protection:
    highlight_percentile = 99.5
    shadow_percentile = 1.0
    highlight_headroom = 0.95
    shadow_headroom = 5.0

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
# REFERENCE MEASURE (single)
# ======================

def measure_stats(path):
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=True,
            half_size=True,
            output_bps=16
        )

    if use_percentile:
        brightness = np.percentile(rgb, percentile_value)
    else:
        brightness = np.mean(rgb)

    highlights = np.percentile(rgb, highlight_percentile)
    shadows = np.percentile(rgb, shadow_percentile)

    return brightness, highlights, shadows


ref_brightness, _, _ = measure_stats(reference_image)
print(f"Reference brightness: {ref_brightness:.2f}")

# ======================
# CLIP SAFETY
# ======================

def apply_clip_safety(ev, highlights, shadows):
    if not enable_clip_protection:
        return ev

    for _ in range(max_safety_iterations):
        scale = 2 ** ev

        projected_high = highlights * scale
        projected_low = shadows * scale

        safe = True

        if projected_high > white_level * highlight_headroom:
            ev -= ev_step_back
            safe = False

        if projected_low < max(black_level + 1, shadow_headroom):
            ev += ev_step_back
            safe = False

        if safe:
            break

    return ev

# ======================
# XMP CREATION
# ======================

def create_xmp_content(ev_adjust):
    return f"""<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
 <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
  <rdf:Description rdf:about=''
    xmlns:crs='http://ns.adobe.com/camera-raw-settings/1.0/'>
    <crs:Version>15.0</crs:Version>
    <crs:ProcessVersion>11.0</crs:ProcessVersion>
    <crs:Exposure2012>{ev_adjust:.4f}</crs:Exposure2012>
    <crs:Contrast2012>0</crs:Contrast2012>
    <crs:Highlights2012>0</crs:Highlights2012>
    <crs:Shadows2012>0</crs:Shadows2012>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""

# ======================
# WORKER: FULL PIPELINE
# ======================

def process_file(path):
    try:
        # skip writing reference if required
        if skip_reference_xmp and path == reference_image:
            return

        brightness, highlights, shadows = measure_stats(path)

        if path == reference_image:
            ev_adjust = 0.0
        else:
            ratio = ref_brightness / brightness if brightness > 0 else 1.0
            ev_adjust = np.log2(ratio) + global_ev_adjust

            if clamp_ev:
                ev_adjust = max(min(ev_adjust, max_ev), min_ev)

            ev_adjust = apply_clip_safety(ev_adjust, highlights, shadows)

        xmp_path = os.path.splitext(path)[0] + ".xmp"

        with open(xmp_path, "w", encoding="utf-8") as f:
            f.write(create_xmp_content(ev_adjust))

    except Exception as e:
        print(f"⚠️ Error: {path}")

# ======================
# PARALLEL EXECUTION
# ======================

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_file, path) for path in files]

        for _ in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            pass

print("✅ Complete: Streaming multi-core XMP pipeline finished")
