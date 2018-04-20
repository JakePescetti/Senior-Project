#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import subprocess
import random
import math
import json
import pickle
import pyproj	#for geo-coordinate transform

# we need to import python modules from the $SUMO_HOME/tools directory
try:
	sys.path.append(os.path.join(os.path.dirname(
		__file__), '..', '..', '..', '..', "tools"))  # tutorial in tests
	sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
		os.path.dirname(__file__), "..", "..", "..")), "tools"))  # tutorial in docs
	from sumolib import checkBinary
except ImportError:
	sys.exit(
		"please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

import traci

#variables
#tuple oldGpsData
#tuple newGpsData

import sumolib

import time
def follow(thefile):		#follow updating gps file
    thefile.seek(0)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line


def generate_routefile():
	with open("campusmap.rou.xml", "w") as routes:
		print("""<routes>
		<vType id="typeBike" accel="0.5" decel="5" sigma="0.5" length="2" minGap="3" maxSpeed="2" guiShape="bicycle"/>
		""", file=routes)
		
		print("</routes>", file=routes)

def run():
	"""execute the TraCI control loop"""
	step = 0
	#while traci.simulation.getMinExpectedNumber() > 0:
	traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
	while True:
		radius = 0.1
		#lat, lon, bear, speed = get_GPS_data()
		#debugging
		if step == 5:
			lat, lon , bear, speed= 34.059297, -117.822937, 160, 5
		
		bear = (bear+360) % 360	#convert -180 -- +180  to 0 - 360 angles
		x, y = net.convertLonLatXY(lon, lat)
		edges = net.getNeighboringEdges(x, y, radius)
		# pick the closest edge (FIX THIS)
		if len(edges) > 0:
			distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])
			dist, closestEdge = distancesAndEdges[0]
		
		#update bike parameters
		traci.vehicle.moveToXY("bike",closestEdge,0,x,y,angle=-1001.0,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
		#traci.vehicle.setSpeed("bike",speed)	#speed update
		#calcSpeed = get_best_speed("bike")	#calc best speed
		
		#send_time_to_grn(calcSpeed)	#send new speed
		
		traci.simulationStep()
		step += 1
	traci.close()
	sys.stdout.flush()

def get_GPS_data():
	file_Name = "gps.pkl"
	#fileObject = open(file_Name,'wb') 
	#pickle.dump(a,fileObject)   
	#fileObject.close()
	fileObject = open(file_Name,'r')  
	gpsData = pickle.load(fileObject) #dictionary with lat, long, speed, direction?
	fileObject.close()
	return gpsData
	
def send_time_to_grn(timeToGrn):
	file_Name = "time.pkl"
	fileObject = open(file_Name,'wb') 
	pickle.dump(newSpeed,fileObject)   
	fileObject.close()

def get_best_speed(vehID):
	lights = traci.vehicle.getNextTLS("bike") 
	tlsid, index, dist, state = lights[0]
	#getCompleteRedYellowGreenDefinition
	#Remaining time in phase = getNextSwitch - simulation.getCurrentTime()
	#find current state in definition and calc time to green 
	#all times in ms
	timeToGrnMS = 120  #debugging
	#TODO: timeToGrn = time in current phase plus total time of phases that aren't green
	timeToGrnHr = ms/3600000	#Convert to hours
	bestSpeed = dist/timeToGrnHr	#dist in meters?
	
	return bestSpeed








def get_options():
	optParser = optparse.OptionParser()
	optParser.add_option("--nogui", action="store_true",
						 default=True, help="run the commandline version of sumo")
	options, args = optParser.parse_args()
	return options
	
def get_value(value):
	datafile.write(value + "\n")


# this is the main entry point of this script
if __name__ == "__main__":
	options = get_options()

	# this script has been called from the command line. It will start sumo as a
	# server, then connect and run
	if options.nogui:
		sumoBinary = checkBinary('sumo')
	else:
		sumoBinary = checkBinary('sumo-gui')

	# first, generate the route file for this simulation
	#generate_routefile()

	# this is the normal way of using traci. sumo is started as a
	# subprocess and then the python script connects and runs
	traci.start([sumoBinary, "-c", "twoint.sumocfg",
							 "--tripinfo-output", "tripinfo.xml"])
	run()
