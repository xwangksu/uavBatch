'''
Created on Aug 25, 2017

@author: xuwang
'''
import os
import argparse
import PhotoScan

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-wp", "--wpath", required=True, help="workingPath")
args = vars(ap.parse_args())
workingPath = args["wpath"]
print("Working path is: %s" % workingPath)
srcImagePath = workingPath+"\\calibrated\\"
project = workingPath+"\\ortho_dem_process.psx"

files = os.listdir(srcImagePath)
file_list=[]
for file in files:
    if file.endswith(".tif"):
        filePath = srcImagePath + file
        file_list.append(filePath)
app = PhotoScan.Application()
doc = PhotoScan.app.document

PhotoScan.app.gpu_mask = 14
PhotoScan.app.cpu_enable = 8

chunk = PhotoScan.app.document.addChunk()
chunk.crs = PhotoScan.CoordinateSystem("EPSG::4326")
# Import photos
chunk.addPhotos(file_list, PhotoScan.MultiplaneLayout)
chunk.matchPhotos(accuracy=PhotoScan.HighAccuracy, preselection=PhotoScan.ReferencePreselection, keypoint_limit = 15000, tiepoint_limit = 10000)
# Align photos                 
chunk.alignCameras(adaptive_fitting=True)
# Save project
doc.save(path=project, chunks=[doc.chunk])
