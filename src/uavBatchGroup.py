'''
Created on Nov 15, 2017

@author: xuwang
'''
import argparse
import os
import numpy
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import errno
import exifread
import shutil
#------------------------------------------------------------------------
def getGPSExifFromImage(srcImage):
    # Get EXIF GPS attributes
    exifAttrib = open(srcImage, 'rb')
    tags = exifread.process_file(exifAttrib, details=False)
    longiRef = -1
    latiRef = 1
    for tag in tags.keys():
        if tag == 'GPS GPSLongitudeRef':
            longiRefStr = str(tags[tag])
    #         print("Longitude Ref: %s" % longiRefStr)
        elif tag == 'GPS GPSLatitudeRef':
            latiRefStr = str(tags[tag])
    #         print("Latitude Ref: %s" % latiRefStr)
        elif tag == 'GPS GPSLatitude':
            latitudeStr = str(tags[tag])[1:-1]
    #         print("Latitude: %s" % latitudeStr)
        elif tag == 'GPS GPSLongitude':
            longitudeStr = str(tags[tag])[1:-1]
    #         print("Longitude: %s" % longitudeStr)
    if latiRefStr == "N":
        latiRef = 1
    else:
        latiRef = -1
    latitudeDeg = float(latitudeStr.split(',')[0])
    latitudeMin = float(latitudeStr.split(',')[1])
    if len(latitudeStr.split(',')[2].split('/')) == 2:
        latitudeSec = float(latitudeStr.split(',')[2].split('/')[0]) / float(latitudeStr.split(',')[2].split('/')[1])
    else:
        latitudeSec = float(latitudeStr.split(',')[2].split('/')[0])
    latitude = latiRef * (latitudeDeg + latitudeMin / 60 + latitudeSec / 3600)
    # print("Latitude: %.7f" % latitude)
    if longiRefStr == "W":
        longiRef = -1
    else:
        longiRef = 1
    longitudeDeg = float(longitudeStr.split(',')[0])
    longitudeMin = float(longitudeStr.split(',')[1])
    if len(longitudeStr.split(',')[2].split('/')) == 2:
        longitudeSec = float(longitudeStr.split(',')[2].split('/')[0]) / float(longitudeStr.split(',')[2].split('/')[1])
    else:
        longitudeSec = float(longitudeStr.split(',')[2].split('/')[0])
    longitude = longiRef * (longitudeDeg + longitudeMin / 60 + longitudeSec / 3600)
    # print("Latitude: %.7f" % longitude)
    return [longitude, latitude]
# End of function
#------------------------------------------------------------------------
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--srcPath", required=True,
    help="source image folder")
ap.add_argument("-t", "--tgtPath", required=True,
    help="target image folder")
ap.add_argument("-bf", "--bfile", required=True,
    help="boundary coordinate file")
ap.add_argument("-td", "--tdatum", default="EPSG:32614",
    help="Target datum EPSG, default is EPSG:32614")
args = ap.parse_args()
sourcePath = args.srcPath
targetPath = args.tgtPath
boundFile = args.bfile
targetDatum = args.tdatum
#------------------------------------------------------------------------
# Get boundary Coordinates
bCorners = numpy.recfromcsv(boundFile,delimiter=',')
sw_x = float(bCorners[0][1])
sw_y = float(bCorners[1][1])
nw_x = float(bCorners[2][1])
nw_y = float(bCorners[3][1])
ne_x = float(bCorners[4][1])
ne_y = float(bCorners[5][1])
se_x = float(bCorners[6][1])
se_y = float(bCorners[7][1])
fieldPolygon = Polygon([(sw_x, sw_y), (nw_x, nw_y), (ne_x, ne_y), (se_x, se_y)])
#------------------------------------------------------------------------
# Create renamed path
try:
    os.makedirs(targetPath+"\\calibrated")
    print("Creating Renamed directory.")
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
# Get images GPS locations
rawImages = os.listdir(sourcePath)
blueIm = []
for im in rawImages:
    if im.find("_1.tif") != -1:
        blueIm.append(im)
for im in blueIm:
    [longi,lati] = getGPSExifFromImage(sourcePath+"\\"+im)    
    if fieldPolygon.contains(Point(longi,lati)):
        newFile = shutil.copy2(sourcePath+"\\"+im,targetPath+"\\calibrated\\"+im)
        print("Copying %s" % newFile)
        newFile = shutil.copy2(sourcePath+"\\"+im.replace("_1.tif","_2.tif"),targetPath+"\\calibrated\\"+im.replace("_1.tif","_2.tif"))
        print("Copying %s" % newFile)
        newFile = shutil.copy2(sourcePath+"\\"+im.replace("_1.tif","_3.tif"),targetPath+"\\calibrated\\"+im.replace("_1.tif","_3.tif"))
        print("Copying %s" % newFile)
        newFile = shutil.copy2(sourcePath+"\\"+im.replace("_1.tif","_4.tif"),targetPath+"\\calibrated\\"+im.replace("_1.tif","_4.tif"))
        print("Copying %s" % newFile)
        newFile = shutil.copy2(sourcePath+"\\"+im.replace("_1.tif","_5.tif"),targetPath+"\\calibrated\\"+im.replace("_1.tif","_5.tif"))
        print("Copying %s" % newFile)
    