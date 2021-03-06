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
#import multiprocessing
import threading
import sumolib
import traci
import rtree
import time
#from watchdog.observers import Observer
#from watchdog.events import FileSystemEventHandler

#Global variables
#fileChanged = False



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

def generate_routefile():
	with open("campusmap.rou.xml", "w") as routes:
		print("""<routes>
		<vType id="typeBike" accel="0.5" decel="5" sigma="0.5" length="2" minGap="3" maxSpeed="15" guiShape="bicycle"/>
		<route id="bike1" edges="430638860#0 430638860#1 430638860#2 430638860#3 434953517#0 434953517#1 434953517#2"/>""", file=routes)
		
		print("</routes>", file=routes)

def run():
	net = sumolib.net.readNet('campusmap.net.xml')
	oldUpcomingLightID = ''
	"""execute the TraCI control loop"""
	step = 0
	fileChanged = False
	newGPSFileTime = os.stat("gps.pkl").st_mtime
	oldGPSFileTime = newGPSFileTime

	#while traci.simulation.getMinExpectedNumber() > 0:
	traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
	traci.vehicle.setSpeed("bike",0)
	while True:
		starttime=time.time()
		radius = 0.1
		closestEdge = 0
		#lat, lon, bear, speed = get_GPS_data()
		
		#Check for file update	
		newGPSFileTime = os.stat("gps.pkl").st_mtime
		if newGPSFileTime != oldGPSFileTime:
			#print(newGPSFileTime)
			fileObject2 = open("gps.pkl","r")
			data2 = pickle.load(fileObject2)
			#print(data2)
			lat,lon,bear,speed = data2
			oldGPSFileTime = newGPSFileTime
		#bear = (bear+360) % 360	#convert -180 -- +180  to 0 - 360 angles
			x, y = net.convertLonLat2XY(lon, lat)
			
			edges = net.getNeighboringEdges(x, y, 0.6)
			if len(edges) > 0:
				distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])
				dist, closestEdge = distancesAndEdges[0]
				edge_id = closestEdge.getID()
				#update bike parameters
				traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=bear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
				traci.vehicle.setSpeed("bike",speed)	#speed update
			fileChanged = False
			timeRemainingInPhase = 0	
			lights = traci.vehicle.getNextTLS("bike")
			if len(lights) > 0:
				newUpcomingLightID = str(lights[0][0])
				if newUpcomingLightID != oldUpcomingLightID:
					oldUpcomingLightID = newUpcomingLightID
					
					upcomingLightPhase = traci.trafficlights.getPhase(newUpcomingLightID)
					nextLightProg = traci.trafficlights.getCompleteRedYellowGreenDefinition(newUpcomingLightID)
					lightProg = nextLightProg[0]
					nextSwitch = traci.trafficlights.getNextSwitch(newUpcomingLightID)
					timeRemainingInPhase += nextSwitch - traci.simulation.getCurrentTime()
					timeWorker(lightProg,upcomingLightPhase,timeRemainingInPhase)
					
		traci.simulationStep()
		step += 1
		time.sleep(1.0 - ((time.time() - starttime) % 1.0))
		
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
	pickle.dump(timeToGrn,fileObject) 
	print(timeToGrn)	
	fileObject.close()

def timeWorker(program, currentPhase, remainingPhaseTime):
	timeToGrn = 0
	timeToGrn2 = 0
	
	phaseList = [] # set up an empty list
	
	for p in program._phases: # extract the list of phases from the logic class
		phaseList.append((p._phaseDef,p._duration)) # each phase in a list ('Marker', duration)

	i = currentPhase
	while True:
		pattern,time = phaseList[i]
		
		if i == currentPhase:
			timeToGrn += remainingPhaseTime
		else:
			timeToGrn += time
			
		if pattern.startswith('G'):
			break

		i = (i + 1)%len(phaseList)
		
		timeToGrn2 = timeToGrn #timeToGrn2 is not really needed but this stops the extra math at greentimes
		
	for pattern,time in phaseList:
		timeToGrn2 += time
		
	greenTimes = (timeToGrn//1000, (timeToGrn2)//1000) #double div makes it int division throw away that extra stuff hand grenades not sniper bullets
	
	send_time_to_grn(greenTimes)
	return

def get_options():
	optParser = optparse.OptionParser()
	optParser.add_option("--nogui", action="store_true",
						 default=False, help="run the commandline version of sumo")
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
	generate_routefile()

	# this is the normal way of using traci. sumo is started as a
	# subprocess and then the python script connects and runs
	traci.start([sumoBinary, "-c", "campusmap.sumocfg",
							 "--full-output", "tripinfo.sbx"])
	#run()
	# event_handler = MyHandler()
    # observer = Observer()
    # observer.schedule(event_handler, path='gps.pkl', recursive=False)
    # observer.start()
	run()
	
	
    # try:
		# while True:
			# time.sleep(1)
	# except KeyboardInterrupt:
		# observer.stop()
	# observer.join()