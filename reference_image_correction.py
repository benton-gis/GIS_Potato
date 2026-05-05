'''
conda activate geo_env
f:
cd F:\_RPA_Processing python reference_image_correction.py
'''

import rawpy
import numpy as np
import os
from tqdm import tqdm

# ======================
# SETTINGS
# ======================

input_folder = r"F:\_RPA_Processing\Stage0\FPC_CARBON2_RTK3_20260429\DCIM"

# ✅ Reference image (correct exposure anchor)
reference_image = r"F:\_RPA_Processing\Stage0\FPC_CARBON2_RTK3_20260429\DCIM\IMG_0001.DNG"

# ✅ Brightness measurement
use_percentile = True
percentile_value = 50

# ✅ Exposure control
global_ev_adjust = 0.0

# ✅ Clamp extreme exposure shifts
clamp_ev = True
min_ev = -2.0
max_ev = 2.0

# ✅ OPTIONAL: skip writing XMP for reference image
skip_reference_xmp = True   # 🔁 set to False if you want EV=0 written instead

# ======================
# SETUP
# ======================

files = []
for root, _, filenames in os.walk(input_folder):
    for f in filenames:
        if f.lower().endswith(".dng"):
            files.append(os.path.join(root, f))

files = sorted(files)
print(f"Found {len(files)} DNG files")

# ======================
# FUNCTION: MEASURE BRIGHTNESS
# ======================
def measure_brightness(path):
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=True,
            half_size=True,
            output_bps=16
        )

        if use_percentile:
            return np.percentile(rgb, percentile_value)
        else:
            return np.mean(rgb)

# ======================
# STEP 1: Measure brightness
# ======================
brightness_map = {}

for path in tqdm(files, desc="Measuring brightness"):
    brightness_map[path] = measure_brightness(path)

# ======================
# STEP 2: Reference brightness
# ======================
ref_brightness = brightness_map.get(reference_image)

if ref_brightness is None:
    raise ValueError("Reference image not found in folder!")

print(f"Reference brightness: {ref_brightness:.2f}")

# ======================
# FUNCTION: CREATE XMP
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
# STEP 3: Normalize + write XMP
# ======================
for path in tqdm(files, desc="Writing XMP sidecars"):

    # ✅ OPTIONAL: completely skip reference image
    if skip_reference_xmp and path == reference_image:
        continue

    brightness = brightness_map[path]

    # ✅ Keep reference at EV = 0 (if not skipped)
    if path == reference_image:
        ev_adjust = 0.0
    else:
        ratio = ref_brightness / brightness if brightness > 0 else 1.0
        ev_adjust = np.log2(ratio) + global_ev_adjust

        if clamp_ev:
            ev_adjust = max(min(ev_adjust, max_ev), min_ev)

    # ✅ Write XMP
    base_name = os.path.splitext(path)[0]
    xmp_path = base_name + ".xmp"

    with open(xmp_path, "w", encoding="utf-8") as f:
        f.write(create_xmp_content(ev_adjust))

print("✅ Complete: Reference-normalised XMPs created")
