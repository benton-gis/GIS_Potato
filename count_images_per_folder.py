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

if __name__ == "__main__":	
	
	folder_path = r"F:\_RPA_Processing\Stage0\FPC_CARBON2_RTK3_20260429\DCIM"
	output_csv = folder_path + "\\raw_image_count.csv"			 

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
