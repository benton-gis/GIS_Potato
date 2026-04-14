# Sharpen Tiff Images
## Introduction
Script to sharpen Tiff images output from Agisoft 2.2.2

Best practive when processing imagery for Surface from Motion (SfM) is to carryout the least amount of post processing as possible. At a minimum only adjust Exposure and WB. Do not sharpen or adjust tone control. Only use Adobe Lightroom if you have to.

This approach outputs tiffs that require sharpening. The following describes how this can be acheived.
## Setup Python Environment
<pre>conda config --set channel_priority strict
conda config --add channels conda-forge
conda create -n ortho_env -c conda-forge
conda install -n ortho_env -c conda-forge gdal numpy scipy</pre>
