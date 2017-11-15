'''
Created on Aug 25, 2017

@author: xuwang
'''
import argparse
import csv
import PhotoScan

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-wp", "--wpath", required=True, help="workingPath")
ap.add_argument("-mf", "--mfile", required=True, help="markerFile")
args = vars(ap.parse_args())
workingPath = args["wpath"]+"\\"
markerFile = args["mfile"]
print("Working path is: %s" % workingPath)

project = workingPath+"ortho_dem_process.psx"

app = PhotoScan.Application()
doc = PhotoScan.app.document
doc.open(project)

PhotoScan.app.gpu_mask = 14
PhotoScan.app.cpu_enable = 8

chunk = doc.chunk
chunk.crs = PhotoScan.CoordinateSystem("EPSG::4326")

# Assign GCPs
markerList = open(markerFile, "rt")

eof = False
line = markerList.readline() #reading the line in input file
while not eof:
    photos_total = len(chunk.cameras)         #number of photos in chunk
    markers_total = len(chunk.markers)         #number of markers in chunk
    sp_line = line.rsplit(",", 6)   #splitting read line by four parts
    camera_name = sp_line[0]        #camera label
    marker_name = sp_line[1]        #marker label
    x = int(sp_line[2])                #x- coordinate of the current projection in pixels
    y = int(sp_line[3])                #y- coordinate of the current projection in pixels
    cx = float(sp_line[4])            #world x- coordinate of the current marker
    cy = float(sp_line[5])            #world y- coordinate of the current marker
    cz = float(sp_line[6])            #world z- coordinate of the current marker
    flag = 0
    for i in range (0, photos_total):    
        if chunk.cameras[i].label == camera_name:
            for marker in chunk.markers:    #searching for the marker (comparing with all the marker labels in chunk)
                if marker.label == marker_name:
                    marker.projections[chunk.cameras[i]] = (x,y)        #setting up marker projection of the correct photo)
                    flag = 1
                    break
            if not flag:
                marker = chunk.addMarker()
                marker.label = marker_name
                marker.projections[chunk.cameras[i]] = (x,y)
            marker.reference.location = PhotoScan.Vector([cx, cy, cz])
            break
    line = markerList.readline()        #reading the line in input file
    # print (line)
    if len(line) == 0:
        eof = True
        break # EOF
markerList.close()
# Correct markers
markerList = open(markerFile, "rt")
# Set the corrected markerList file
markerFileCorrected = open(markerFile.replace(".csv","_c.csv"),'wt')
try:
    writer = csv.writer(markerFileCorrected, delimiter=',', lineterminator='\n')
    eof = False
    line = markerList.readline() #reading the line in input file
    while not eof:    
        photos_total = len(chunk.cameras)         #number of photos in chunk
        markers_total = len(chunk.markers)         #number of markers in chunk
        sp_line = line.rsplit(",", 6)   #splitting read line by four parts
        camera_name = sp_line[0]        #camera label
        marker_name = sp_line[1]        #marker label
        x = int(sp_line[2])                #x- coordinate of the current projection in pixels
        y = int(sp_line[3])                #y- coordinate of the current projection in pixels
        cx = float(sp_line[4])            #world x- coordinate of the current marker
        cy = float(sp_line[5])            #world y- coordinate of the current marker
        cz = float(sp_line[6])            #world z- coordinate of the current marker
        for i in range (0, photos_total):    
            if chunk.cameras[i].label == camera_name:
                for marker in chunk.markers:    #searching for the marker (comparing with all the marker labels in chunk)
                    if marker.label == marker_name:
                        # print("marker: %s" % marker.label)
                        # print("camera: %s" % chunk.cameras[i])
                        # Error check
                        projection_m = marker.projections[chunk.cameras[i]].coord
                        reprojection = chunk.cameras[i].project(marker.position)
                        if not (reprojection is None or reprojection == 0):
                            error_pix = (projection_m - reprojection).norm()
                            # print("error pixel: %f" % error_pix)
                            if error_pix < 1.5:
                                writer.writerow((camera_name,marker_name,x,y,cx,cy,cz,error_pix))
                        break
                break
        line = markerList.readline()        #reading the line in input file
        if len(line) == 0:
            eof = True
            break # EOF
    markerList.close()
finally:
    markerFileCorrected.close()
# Remove all markers
for marker in chunk.markers:
    chunk.remove(marker)
# Reinsert markers
markerList = open(workingPath+markerFile+"_c.csv", "rt")
eof = False
line = markerList.readline() #reading the line in input file
while not eof:    
    photos_total = len(chunk.cameras)         #number of photos in chunk
    markers_total = len(chunk.markers)         #number of markers in chunk
    sp_line = line.rsplit(",", 7)   #splitting read line by four parts
    camera_name = sp_line[0]        #camera label
    marker_name = sp_line[1]        #marker label
    x = int(sp_line[2])                #x- coordinate of the current projection in pixels
    y = int(sp_line[3])                #y- coordinate of the current projection in pixels
    cx = float(sp_line[4])            #world x- coordinate of the current marker
    cy = float(sp_line[5])            #world y- coordinate of the current marker
    cz = float(sp_line[6])            #world z- coordinate of the current marker
    flag = 0
    for i in range (0, photos_total):    
        if chunk.cameras[i].label == camera_name:
            for marker in chunk.markers:    #searching for the marker (comparing with all the marker labels in chunk)
                if marker.label == marker_name:
                    marker.projections[chunk.cameras[i]] = (x,y)        #setting up marker projection of the correct photo)
                    flag = 1
                    break
            if not flag:
                marker = chunk.addMarker()
                marker.label = marker_name
                marker.projections[chunk.cameras[i]] = (x,y)
            marker.reference.location = PhotoScan.Vector([cx, cy, cz])
            break    
    line = markerList.readline()        #reading the line in input file
    # print (line)
    if len(line) == 0:
        eof = True
        break # EOF
markerList.close()
# Save project
doc.save(path=project, chunks=[doc.chunk])
