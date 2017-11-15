'''
Created on Nov 14, 2017

@author: xuwang
'''
import os
import argparse
from datetime import datetime
import errno
import exiftool
import shutil
import numpy
import cv2
import matplotlib.pyplot as plt
import micasense.metadata as metadata
import micasense.utils as msutils
from pyimagesearch.shapedetector import ShapeDetector
import imutils
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
#------------------------------------------------------------------------
# Parameter settings, MAY NEED MODIFY
# Calibration panel albedo value
panelCalibration = { 
    "Blue": 0.66, 
    "Green": 0.67, 
    "Red": 0.67, 
    "Red edge": 0.66, 
    "NIR": 0.6 
}
# For panel detection
black_th=110
cont_th=7000
#------------------------------------------------------------------------
def panelDetect(image,b_th,ct_th):
    image = cv2.imread(image)
    resized = imutils.resize(image, width=640, height=480)
    ratio = image.shape[0] / float(resized.shape[0])
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, b_th, 255, cv2.THRESH_BINARY)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    sd = ShapeDetector()
    # loop over the contours
    sq=0
    for c in cnts:
        shape = "unidentified"
        M = cv2.moments(c)
        if M["m00"] != 0:
            cX = int(round((M["m10"] / M["m00"]))) # * ratio
            cY = int(round((M["m01"] / M["m00"]))) # * ratio
            shape = sd.detect(c)
        if shape == "square":
            if cv2.contourArea(c)>ct_th:
                sq +=1
                c = c.astype("float")
                c *= ratio
                c = c.astype("int")
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                cv2.drawContours(image, [c], -1, (0, 255, 0), 1)
                cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,0.5, (255, 255, 255), 1)
    if sq == 1:
        return approx
    else:
        return [[[0,0]],[[0,0]],[[0,0]],[[0,0]]]
#------------------------------------------------------------------------
# construct the argument parse and parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("fpath", help="main file path")
args = parser.parse_args()
filePath = args.fpath
#------------------------------------------------------------------------
# Define the output LogFile
logFile = 'Log_'+datetime.now().strftime("%y%m%d_%H%M%S")+'.txt'
logname = os.path.join(filePath,logFile)
with open(logname, 'a') as logoutput:
    logoutput.write("File path is: %s\n" % filePath)
print("File path is: %s" % filePath)
# Create list of all images
exten = '.tif'
imList=[]
for dirpath, dirnames, files in os.walk(filePath):
    for name in files:
        if name.lower().endswith(exten):
            imList.append(os.path.join(dirpath, name))
with open(logname, 'a') as logoutput:
    logoutput.write("Total images in the path: %d\n" % len(imList))
print("Total images in the path: %d" % len(imList))
# Filter questionable images
imNum = 9999
acc = 0
tempImList=[]
finalImList=[]
questionImList=[]
for im in imList:
    imObj = im.split("\\")
    numOfObj = len(imObj)
    imNumNext = int(imObj[numOfObj-1].split("_")[1])
    if imNum != imNumNext:
        imNum = imNumNext
        if acc == 5:
            for i in range(0,acc):
                finalImList.append(tempImList[i])
        else:
            for i in range(0,acc):
                questionImList.append(tempImList[i])
        acc = 1
        tempImList.clear()
        tempImList.append(im)
    else:
        acc += 1
        tempImList.append(im)
if acc ==5:
    for i in range(0,5):
        finalImList.append(tempImList[i])
with open(logname, 'a') as logoutput:
    logoutput.write("Total effective images in the path: %d\n" % len(finalImList))
    logoutput.write(''.join(questionImList)+"\n")
print("Total effective images in the path: %d" % len(finalImList))
#------------------------------------------------------------------------
# Create renamed path
try:
    os.makedirs(filePath+"\\renamed")
    print("Creating Renamed directory.")
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
# Rename and copy into Renamed directory
alti = [] # altitude
for im in finalImList:
    imObj = im.split("\\")
    numOfObj = len(imObj)
    imFile = imObj[numOfObj-1]
    with exiftool.ExifTool() as et:
        dtTags = et.get_tag('EXIF:DateTimeOriginal',im)
        alti.append(float(et.get_tag('GPS:GPSAltitude',im)))
    dtTags = ''.join(dtTags.split(":")).replace(" ","_")
    tgFile = filePath+"\\renamed\\"+dtTags+"_"+imFile
    newFile = shutil.copy2(im,tgFile)
    print("Copying %s" % newFile)
#------------------------------------------------------------------------
# Calculate altitude
alti_min = numpy.min(alti)
alti_mean = numpy.mean(alti)
alti_th = alti_min + 0.5*(alti_mean-alti_min)
with open(logname, 'a') as logoutput:
    logoutput.write("Altitude threshold: %.3f\n" % alti_th)
print("Altitude threshold: %.3f" % alti_th)
# Create low path
try:
    os.makedirs(filePath+"\\low_altitude")
    print("Creating LOW directory.")
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
renamedIm = os.listdir(filePath+"\\renamed")
blueIm = []
for im in renamedIm:
    if im.find("_1.tif") != -1:
        blueIm.append(im)
acc = 0
with exiftool.ExifTool() as et:
    for im in blueIm:
        alti = float(et.get_tag('GPS:GPSAltitude',filePath+"\\renamed\\"+im))
        if alti < alti_th:
            # Move to low directory
            newFile = shutil.move(filePath+"\\renamed\\"+im, filePath+"\\low_altitude\\"+im)
            print("Moving %s" % newFile)
            newFile = shutil.move(filePath+"\\renamed\\"+im.replace("_1.tif","_2.tif"), filePath+"\\low_altitude\\"+im.replace("_1.tif","_2.tif"))
            print("Moving %s" % newFile)
            newFile = shutil.move(filePath+"\\renamed\\"+im.replace("_1.tif","_3.tif"), filePath+"\\low_altitude\\"+im.replace("_1.tif","_3.tif"))
            print("Moving %s" % newFile)
            newFile = shutil.move(filePath+"\\renamed\\"+im.replace("_1.tif","_4.tif"), filePath+"\\low_altitude\\"+im.replace("_1.tif","_4.tif"))
            print("Moving %s" % newFile)
            newFile = shutil.move(filePath+"\\renamed\\"+im.replace("_1.tif","_5.tif"), filePath+"\\low_altitude\\"+im.replace("_1.tif","_5.tif"))
            print("Moving %s" % newFile)
            acc += 5
print("%d files moved to low_altitude" % acc)
with open(logname, 'a') as logoutput:
    logoutput.write("%d files moved to low_altitude\n" % acc)
#------------------------------------------------------------------------
# Calculate converting parameters
if acc > 0:
    imageFiles = os.listdir(filePath+"\\low_altitude")
    exiftoolPath = None
    if os.name == 'nt':
        exiftoolPath = 'D:/ExifTool/exiftool.exe'
    # Sum of each band's radiance 
    sbr_B = 0
    sbr_G = 0
    sbr_R = 0
    sbr_E = 0
    sbr_N = 0
    # Num of each band's radiance 
    nbr_B = 0
    nbr_G = 0
    nbr_R = 0
    nbr_E = 0
    nbr_N = 0
    for im in imageFiles:
        # Read raw image DN values
        imageName = filePath+"\\low_altitude\\"+im
        imageRaw=plt.imread(imageName)
        print("Processing %s" % imageName)
        meta = metadata.Metadata(imageName, exiftoolPath=exiftoolPath)
        bandName = meta.get_item('XMP:BandName')
        radianceImage, L, V, R = msutils.raw_image_to_radiance(meta, imageRaw)
        panel_coords = panelDetect(imageName, black_th, cont_th)
        # Extract coordinates
        if panel_coords[0][0][0]:
            nw_x = int(panel_coords[0][0][0])
            nw_y = int(panel_coords[0][0][1])
            sw_x = int(panel_coords[1][0][0])
            sw_y = int(panel_coords[1][0][1])
            se_x = int(panel_coords[2][0][0])
            se_y = int(panel_coords[2][0][1])
            ne_x = int(panel_coords[3][0][0])
            ne_y = int(panel_coords[3][0][1])
            x_min = numpy.min([nw_x,sw_x,ne_x,se_x])
            x_max = numpy.max([nw_x,sw_x,ne_x,se_x])
            y_min = numpy.min([nw_y,sw_y,ne_y,se_y])
            y_max = numpy.max([nw_y,sw_y,ne_y,se_y])
            panelPolygon = Polygon([(sw_x, sw_y), (nw_x, nw_y), (ne_x, ne_y), (se_x, se_y)])
            numPixel = 0
            sumRadiance = 0
            for x in range(x_min,x_max):
                for y in range(y_min,y_max):
                    if panelPolygon.contains(Point(x,y)):
                        numPixel += 1
                        sumRadiance = sumRadiance+radianceImage[y,x]
            meanRadiance = sumRadiance/numPixel
            if bandName == 'Blue':
                sbr_B = sbr_B + meanRadiance
                nbr_B += 1
            elif bandName == 'Green':
                sbr_G = sbr_G + meanRadiance
                nbr_G += 1
            elif bandName == 'Red':
                sbr_R = sbr_R + meanRadiance
                nbr_R += 1
            elif bandName == 'Red edge':
                sbr_E = sbr_E + meanRadiance
                nbr_E += 1
            else:
                sbr_N = sbr_N + meanRadiance
                nbr_N += 1
    if nbr_B != 0:
        meanRadiance_B = sbr_B / nbr_B
    else:
        meanRadiance_B = 0
    if nbr_G != 0:
        meanRadiance_G = sbr_G / nbr_G
    else:
        meanRadiance_G = 0
    if nbr_R != 0:
        meanRadiance_R = sbr_R / nbr_R
    else:
        meanRadiance_R = 0
    if nbr_E != 0:
        meanRadiance_E = sbr_E / nbr_E
    else:
        meanRadiance_E = 0
    if nbr_N != 0:
        meanRadiance_N = sbr_N / nbr_N
    else:
        meanRadiance_N = 0
    # Select panel region from radiance image
    print("Mean Radiance of each band B-G-R-N-E: %.3f, %.3f, %.3f, %.3f,%.3f" % (meanRadiance_B,meanRadiance_G,meanRadiance_R,meanRadiance_N,meanRadiance_E))
    with open(logname, 'a') as logoutput:
        logoutput.write("Mean Radiance of each band B-G-R-N-E: %.3f, %.3f, %.3f, %.3f,%.3f\n" % (meanRadiance_B,meanRadiance_G,meanRadiance_R,meanRadiance_N,meanRadiance_E))
    radianceToReflectance_B = panelCalibration["Blue"] / meanRadiance_B
    radianceToReflectance_G = panelCalibration["Green"] / meanRadiance_G
    radianceToReflectance_R = panelCalibration["Red"] / meanRadiance_R
    radianceToReflectance_N = panelCalibration["NIR"] / meanRadiance_N
    radianceToReflectance_E = panelCalibration["Red edge"] / meanRadiance_E
    print("Radiance to reflectance conversion factor of each band B-G-R-N-E: %.5f, %.5f, %.5f, %.5f,%.5f" % (radianceToReflectance_B,radianceToReflectance_G,radianceToReflectance_R,radianceToReflectance_N,radianceToReflectance_E))
    with open(logname, 'a') as logoutput:
        logoutput.write("Radiance to reflectance conversion factor of each band B-G-R-N-E: %.5f, %.5f, %.5f, %.5f,%.5f\n" % (radianceToReflectance_B,radianceToReflectance_G,radianceToReflectance_R,radianceToReflectance_N,radianceToReflectance_E))
#------------------------------------------------------------------------
# Calibrate Images
# Create calibrated path
radianceToReflectance = {
    "Blue": radianceToReflectance_B,
    "Green": radianceToReflectance_G,
    "Red": radianceToReflectance_R,
    "Red edge": radianceToReflectance_E,
    "NIR": radianceToReflectance_N
}
try:
    os.makedirs(filePath+"\\calibrated")
    print("Creating Calibrated directory.")
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
rawImages = os.listdir(filePath+"\\renamed")
for im in rawImages:
    print("Calibrating: %s" % filePath+"\\renamed\\"+im)
    flightImageRaw=plt.imread(filePath+"\\renamed\\"+im)
    meta = metadata.Metadata(filePath+"\\renamed\\"+im, exiftoolPath=exiftoolPath)
    bandName = meta.get_item('XMP:BandName')
    bitsPerPixel = meta.get_item('EXIF:BitsPerSample')
    dnMax = float(2**bitsPerPixel)
    flightRadianceImage, _, _, _ = msutils.raw_image_to_radiance(meta, flightImageRaw)
    flightReflectanceImage = flightRadianceImage * radianceToReflectance[bandName]
    flightReflectanceImage_u16=flightReflectanceImage*dnMax
    flightReflectanceImage_u16=flightReflectanceImage_u16.astype(numpy.uint16)
    cv2.imwrite(filePath+"\\calibrated\\"+im, flightReflectanceImage_u16)
#------------------------------------------------------------------------
# Copy EXIF attributes
# Copy EXIF:
rawImages = os.listdir(filePath+"\\renamed")
calPath = filePath+'\\calibrated\\'
for im in rawImages:
    os.system("exiftool -tagsFromFile %s %s" % (filePath+"\\renamed\\"+im, calPath+im))
    os.system("del %s" % calPath+im.replace(".tif",".tif_original"))
    # Copy XMP:
    os.system("exiftool -xmp -b %s > %s" % (filePath+"\\renamed\\"+im, calPath+im.replace(".tif", ".xmp")))
    os.system("exiftool -tagsfromfile %s -xmp %s" % (calPath+im.replace(".tif", ".xmp"), calPath+im))
os.system("del %s*.tif_original" % calPath)
os.system("del %s*.xmp" % calPath)
