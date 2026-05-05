import os
import csv
from pathlib import Path
'''
conda activate geo_env
cd V:\OD_Work\Scripts\_Aerial_Processing\Scripts\Stage0
v:
python count_images_per_folder_2.py
'''


def count_dng_per_folder(root_folder):
    results = []
    total = 0

    for dirpath, dirnames, filenames in os.walk(root_folder):
        count = sum(1 for f in filenames if f.lower().endswith(".dng"))

        results.append((dirpath, count))
        total += count

    return results, total
    
project_name = 'THOMPSON_BROOK'
    
#Get drive letter
'''
if os.getenv('COMPUTERNAME') == 'DBCA-4719331859':

	print('DBCA-4719331859')
	v_drive = Path('H:/')
	print(v_drive)

elif os.getenv('COMPUTERNAME') == 'DBCA-M1M0FM1524':

	print('DBCA-M1M0FM1524')
	v_drive = Path('F:/')
	print(v_drive)

elif os.getenv('COMPUTERNAME') == 'DBCA-M1M0FM1524':

	print('DBCA-9CMXBB4')
	v_drive = Path('D:/')
	print(v_drive)

else:

	hostname = os.getenv('COMPUTERNAME')  # Windows
	print(hostname)
'''

if __name__ == "__main__":
    
    folder_path = "X:\\FMB\\AERIAL_PHOTOGRAPHY_WORKING\\2025-2026\\RPA\\RAW\\FPC\\Thompson_Brook_SeedlingCount_RTK3_20260426\\"    
    #folder_path = v_drive / '_RPA_Processing/Stage0/' + project_name + '/RAW/'
    #output_csv = project_name + "_dng_report.csv"             # Output file
    
    #folder_path = r'H:\_RPA_Processing\Stage0\THOMPSON_BROOK'
    output_csv = "\\_dng_report.csv"             # Output file

    results, total = count_dng_per_folder(folder_path)

    # Write CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Folder", "DNG_Count"])
        for folder, count in results:
            writer.writerow([folder, count])

        # Add total row
        writer.writerow([])
        writer.writerow(["TOTAL", total])

    print(f"Report saved to {output_csv}")
    print(f"Total .DNG files: {total}")
