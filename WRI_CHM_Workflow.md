## Run in GRASS Console
v.import input=F:\WRI_Canopy_Height_Model\gpkg\aoi.gpkg layer=aoi output=AOIregion

## Download the file to the working directory (run from CMD)
e:
cd E:\map_data\common\WRI_Canopy_Height_Model\Scripts
aws s3 cp --no-sign-request s3://dataforgood-fb-data/forests/v1/alsgedi_global_v6_float/tiles.geojson tiles.geojson

## Run in GRASS Console. 
v.import input=F:\WRI_Canopy_Height_Model\aws_data\tiles.geojson output=tiles

# Run in GRASS Python Code Editor
get_wri_chm_from_aws.py
