import os
import shutil
import subprocess
import json
import csv

# ========================
# ⚙️ SETTINGS
# ========================

IMAGE_FOLDER = r"F:\_RPA_Processing\Stage2\PROJECT_NAME\IMG"
REVIEW_FOLDER = os.path.join(IMAGE_FOLDER, "_REVIEW_OBLIQUE")
CSV_OUTPUT = os.path.join(IMAGE_FOLDER, "oblique_report.csv")

EXIFTOOL_PATH = r"C:\Exiftool\exiftool.exe"

MAX_TILT_FROM_NADIR = 10   # degrees

# ========================
# ✅ PRE-CHECKS
# ========================
if not os.path.exists(IMAGE_FOLDER):
    print(f"❌ Folder not found:\n{IMAGE_FOLDER}")
    exit()

jpgs = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(".jpg")]

if len(jpgs) == 0:
    print("❌ No JPG images found")
    exit()

print(f"✅ Found {len(jpgs)} JPG images")

if not os.path.exists(EXIFTOOL_PATH):
    print(f"❌ ExifTool not found:\n{EXIFTOOL_PATH}")
    exit()

os.makedirs(REVIEW_FOLDER, exist_ok=True)

# ========================
# 🔧 HELPERS
# ========================
def to_float(val):
    try:
        return float(val)
    except:
        return None

# ========================
# 📸 RUN EXIFTOOL
# ========================
cmd = [
    EXIFTOOL_PATH,
    "-json",
    "-n",
    "-GimbalPitchDegree",
    IMAGE_FOLDER
]

print("\nReading pitch values...")
result = subprocess.run(cmd, capture_output=True, text=True)

if not result.stdout.strip():
    print("❌ No metadata returned")
    exit()

data = json.loads(result.stdout)

# ========================
# 📝 CSV SETUP
# ========================
csv_rows = []

# ========================
# 🚀 PROCESS
# ========================
moved = 0

for entry in data:
    file = entry.get("SourceFile")
    pitch = to_float(entry.get("GimbalPitchDegree"))

    if pitch is None:
        continue

    tilt = abs(pitch + 90)

    if tilt > MAX_TILT_FROM_NADIR:
        filename = os.path.basename(file)

        # record for CSV
        csv_rows.append([filename, pitch, tilt, "oblique"])

        # move file
        dest = os.path.join(REVIEW_FOLDER, filename)
        try:
            shutil.move(file, dest)
            moved += 1
            print(f"Moved: {filename} -> tilt={tilt:.1f}")
        except Exception as e:
            print(f"⚠️ Move failed: {file} ({e})")

# ========================
# 💾 WRITE CSV
# ========================
with open(CSV_OUTPUT, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "filename",
        "pitch_deg",
        "tilt_from_nadir_deg",
        "latitude",
        "longitude",
        "reason"
    ])
    writer.writerows(csv_rows)

# ========================
# ✅ DONE
# ========================
print("\n✅ Finished")
print(f"Oblique images moved: {moved}")
print(f"CSV report saved to:\n{CSV_OUTPUT}")
print(f"Review folder:\n{REVIEW_FOLDER}")
