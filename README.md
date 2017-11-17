# uavBatch
The objective to develop the "uavBatch" Python scripts is to scientifically and automatically generate the ortho-photos from the aerial images captured by the MicaSense RedEdge(-M) camera.

This trial (beta) version of the Python scripts is for local use, meaning no network connection needed. However, that also means necessary meta-data should be provided through files, such as field boundary coordinates and ground control points (GCPs) within in the boundary. Also, this version is only applied to the images captured by the MicaSense RedEdge(-M) cameras with the firmware after v2.1.x.

The radiometric calibration model is according to https://support.micasense.com/hc/en-us/articles/115000351194-RedEdge-Camera-Radiometric-Calibration-Model. The Python scripts to do the radiometric calibration is modified based on https://github.com/micasense/imageprocessing.

Necessary Python libraries need to be pre-installed to run the Python scripts. The Agisoft Python API used in this version is v1.3.2. The trial version has been tested on a Windows machine.

The Python scripts include:

uavBatchPreProcess.py
> uavBatchPreProcess.py <-s sourceFileFolder>

This script recursively searches for all the .tif files within the source file folder. Only the images with five complete bands will be selected and renamed using the date and time stamps, and saved in the "renamed" folder in the source file folder. Next, the images captured on the ground will be moved to the "low_altitude" folder. After that, all images having the color panel in the "low_altitude" folder will be used to calculate the reflectance conversion factor of each band. Then, the images inside the "renamed" folder will be calibrated using the factors calculated in the last step and saved in the "calibrated" folder. At last, all the EXIF and XMP attributes will be copied from the images inside the "renamed" folder to the "calibrated" folder.

uavBatchGroup.py
> uavBatchGroup.py <-s sourceImageFolder> <-t targetFolder> <-bf fieldBoundaryCoordinateFile>

This script selects all the images inside the field boundaries defined by the field boundary coordinate file and copies them to the target folder. An example of the field boundary coordinate file is attached.

uavBatchMarkderDetection.py
> uavBatchMarkderDetection.py <-s sourceImageFolder> <-t targetFolder> <-gf gcpFile>

This script detects the GCPs listed in the GCP file within the images in the source image folder, and saves the "markerList.csv" file in the target folder. An example of the GCP files is attached.

uavBatchImAlignment.py
> photoscan.exe -r uavBatchImAlignment.py <-wp sourceImageFolder>

This script uses the Agisoft Python API to align the multi-band images in the "calibrated" folder inside the source image folder. The Agisoft project will be saved as "ortho_dem_process.psx" inside the source image folder.

uavBatchGcpAssignment.py
> photoscan.exe -r uavBatchGcpAssignment.py <-wp sourceFileFolder> <-mf markerFile>

This script uses the Agisoft Python API to load the Agisoft project - "ortho_dem_process.psx" inside the source file folder and imports the GCP's information listed in the maker file to the project.

uavBatchModelGeneration.py
> photoscan.exe -r uavBatchModelGeneration.py <-wp sourceFileFolder>

This script uses the Agisoft Python API to load the Agisoft project - "ortho_dem_process.psx" inside the source file folder, generate the ortho-photo and DEM model, and saved them as "ortho.tif" and "dem.tif" in the source file folder.

If there is no GCP used, script #3 and script #5 are not necessary.
