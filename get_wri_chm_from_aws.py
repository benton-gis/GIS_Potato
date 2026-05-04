import grass.script as gs
from os import path
import os
import urllib.request

# ---------------------------------------------------------
# 1. Select tiles overlapping the AOI region
# ---------------------------------------------------------
gs.run_command(
    "v.select",
    ainput="tiles",
    binput="AOIregion",
    output="tiles_AOI",
    operator="overlap"
)

# ---------------------------------------------------------
# 2. Extract tile IDs (QuadKeys) from attribute table
#    Strip CRLF to avoid invalid URLs
# ---------------------------------------------------------
qk_raw = gs.read_command(
    "v.db.select",
    flags="c",
    map="tiles_AOI",
    columns="tile",
    separator="comma"
    ).split("\n")

# Clean list: remove empty rows AND strip CRLF
qk = [x.strip() for x in qk_raw if x.strip()]

# ---------------------------------------------------------
# 3. Download + import each tile via HTTPS
# ---------------------------------------------------------
baseurl = "https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm"

for quad in qk:
    url = f"{baseurl}/{quad}.tif"
    local = f"tile_{quad}.tif"
    layer = f"tile_{quad}"

    print(f"Downloading {url}")

    # Pure HTTPS download (no AWS CLI)
    urllib.request.urlretrieve(url, local)

    # Import into GRASS
    gs.run_command("r.in.gdal", input=local, output=layer, memory=40000)

    # Remove temporary file
    os.remove(local)


    # Create the list of layers
    qkl = [f"tile_{x}" for x in qk]

    # Set the region to match the extent of the com
    gs.run_command("g.region", vector="AOIregion", raster=qkl, align=qkl[0])

    # Patch the layers together
    gs.run_command("r.patch", flags="s", input=qkl, output="CHMtmp", nprocs=10, memory=40000)

    # Set color
    color_rules = {
        0: "247:252:245",
        3: "229:245:224",
        6: "199:233:192",
        9: "161:217:155",
        12: "116:196:118",
        15: "65:171:93",
        18: "35:139:69",
        21: "0:109:44",
        24: "0:68:27",
        95: "0:0:0",
    }
    rules_file = gs.tempfile()
    with open(rules_file, "w") as f:
        for value, color in color_rules.items():
            f.write(f"{value} {color}\n")
            
    gs.run_command('r.colors', map="CHMtmp", rules=rules_file)
    
    # InsAOIl the r.clip addon
    gs.run_command("g.extension", extension="r.clip")

    # Set the region to match the extent of the area of interest
    gs.run_command("g.region", vector="AOI_region", align="CHM")

    # Set a mask to mask out all areas outside the areas of interest
    gs.run_command("r.mask", vector="AOI_region")

    # Clip the map
    gs.run_command("r.clip", input="CHMtmp", output="CHM")
