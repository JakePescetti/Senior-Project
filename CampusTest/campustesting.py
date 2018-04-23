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
import multiprocessing
import sumolib
import traci
import rtree
import time

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
		<vType id="typeBike" accel="0.5" decel="5" sigma="0.5" length="2" minGap="3" maxSpeed="15" guiShape="bicycle"/>
		<route id="bike1" edges="430638860#0 430638860#1 430638860#2 430638860#3 434953517#0 434953517#1 434953517#2"/>""", file=routes)
		
		print("</routes>", file=routes)

def run():
	net = sumolib.net.readNet('campusmap.net.xml')
	oldUpcomingLightID = ''
	"""execute the TraCI control loop"""
	step = 0

	#while traci.simulation.getMinExpectedNumber() > 0:
	traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
	traci.vehicle.setSpeed("bike",0)
	while True:
		radius = 0.1
		closestEdge = 0
		#lat, lon, bear, speed = get_GPS_data()
		#debugging
		if step == 1:
			data = (34.058250,-117.82232,160,5)
			fileObject = open("gps.pkl","wb") 
			pickle.dump(data,fileObject)   
			fileObject.close()
		
		if step == 5:
			fileObject2 = open("gps.pkl","r")
			data2 = pickle.load(fileObject2)
			print(data2)
			lat,lon,bear,speed = data2
			# lat = 34.058250
			# lon = -117.82232
			# bear = 160
			# speed= 5
		
		#bear = (bear+360) % 360	#convert -180 -- +180  to 0 - 360 angles
			x, y = net.convertLonLat2XY(lon, lat)
			#print(x)
			#print(y)
			
			edges = net.getNeighboringEdges(x, y, 0.6)
			# numedges = len(edges)
			# print(numedges)
			# for elem in edges:
				# print(elem)
			 
 
			
		# pick the closest edge (FIX THIS)
			if len(edges) > 0:
				distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])
				dist, closestEdge = distancesAndEdges[0]
				edge_id = closestEdge.getID()
				# temp = closestEdge.split(' ')
				# temp2 = temp[1].split('"')
				# print(temp2[-1])
		
		#update bike parameters
			traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=bear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
			traci.vehicle.setSpeed("bike",speed)	#speed update
		timeRemainingInPhase = 0	
		if step == 8:
			lights = traci.vehicle.getNextTLS("bike")
			newUpcomingLightID = str(lights[0][0])
			if newUpcomingLightID != oldUpcomingLightID:
				oldUpcomingLightID = newUpcomingLightID
				
				upcomingLightPhase = traci.trafficlights.getPhase(newUpcomingLightID)
				nextLightProg = traci.trafficlights.getCompleteRedYellowGreenDefinition(newUpcomingLightID)
				lightProg = str(nextLightProg[0])
				nextSwitch = traci.trafficlights.getNextSwitch(newUpcomingLightID)
				timeRemainingInPhase += nextSwitch - traci.simulation.getCurrentTime()
			
				p = multiprocessing.Process(target=timeWorker, args=(lightProg,upcomingLightPhase,timeRemainingInPhase,))
				p.start()
		#print(step)	
			

			
		if False: #step > 6:
			lights = traci.vehicle.getNextTLS("bike")
			nextLightID = str(lights[0][0])
			nextSwitch = traci.trafficlights.getNextSwitch(nextLightID)
			
			
			#duration = traci.trafficlights.getPhaseDuration(nextLightID)
			#print(nextSwitch - traci.simulation.getCurrentTime())
			
		if False:#step == 10:
			lat = 34.057634
			lon = -117.822184
			bear = 165
			speed= 2
			
			#34.057634, -117.822184
		
		#bear = (bear+360) % 360	#convert -180 -- +180  to 0 - 360 angles
			x, y = net.convertLonLat2XY(lon, lat)
			print(x)
			print(y)
			
			edges = net.getNeighboringEdges(x, y, 0.6)
			# numedges = len(edges)
			# print(numedges)
			# for elem in edges:
				# print(elem)
			# file = open('testfile.txt','w') 
 
			# file.write(edges) 
			# file.close() 
			# for dist,edge in edges:
				# print(dist)
				# print('---'.join(edge))
		# pick the closest edge (FIX THIS)
			if len(edges) > 0:
				distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])
				dist, closestEdge = distancesAndEdges[0]
				edge_id = closestEdge.getID()
				# temp = closestEdge.split(' ')
				# temp2 = temp[1].split('"')
				# print(temp2[-1])
		
		#update bike parameters
			traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=bear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
			traci.vehicle.setSpeed("bike",speed)	#speed update
		#calcSpeed = get_best_speed("bike")	#calc best speed
			lights = traci.vehicle.getNextTLS("bike")
			print(lights)
			#parse light id
			for light in lights[0]:
				print(light)
			#getCompleteRedYellowGreenDefinition()
			
		
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
	pickle.dump(timeToGrn,fileObject)   
	fileObject.close()

def timeWorker(program, currentPhase, remainingPhaseTime):
	timeToGrn = 0
	timeToGrn2 = 0
	lightProgSplit = program.split('\n')
	phaseList = []
	tempTime = 0
	tempDef = ''
	for line in lightProgSplit:
		if line.startswith('duration:'):
			parts = line.split(' ')
			tempTime = int(parts[1])
		if line.startswith('phaseDef:'):
			parts = line.split(' ')
			tempDef = parts[1]
			phaseList.append((tempDef, tempTime))
			
	i = currentPhase
	while True:
		pattern,time = phaseList[i]
		
		if i == currentPhase:
			timeToGrn += remainingPhaseTime
		else:
			timeToGrn += time
			
		if pattern.startswith('G'):
			break
		i += 1
		if i == len(phaseList):
			i = 0
			
	for pattern,time in phaseList:
		timeToGrn2 += time
		
	greenTimes = (timeToGrn/1000, (timeToGrn+timeToGrn2)/1000)
	send_time_to_grn(greenTimes)
	return

# def get_time_to_green(tlsID):
	# timeToGrn = 0
	# timeToGrn2 = 0
	# #nextLightID = str(lights[0][0])
	# upcomingLightPhase = traci.trafficlights.getPhase(tlsID)
	# #print(upcomingLightPhase)
	# nextLightProg = traci.trafficlights.getCompleteRedYellowGreenDefinition(tlsID)
	# #phases = next.getLogics()
	# #print(phases)
	# lightProg = str(nextLightProg[0])
	
	# lightProgSplit = lightProg.split('\n')
	# phaseList = []
	# tempTime = 0
	# tempDef = ''
	# for line in lightProgSplit:
		# if line.startswith('duration:'):
			# parts = line.split(' ')
			# tempTime = int(parts[1])
		# if line.startswith('phaseDef:'):
			# parts = line.split(' ')
			# tempDef = parts[1]
			# phaseList.append((tempDef, tempTime))
			
	# i = upcomingLightPhase
	# while True:
		# pattern,time = phaseList[i]
		# if i == upcomingLightPhase:
			# nextSwitch = traci.trafficlights.getNextSwitch(tlsID)
			# timeToGrn += nextSwitch - traci.simulation.getCurrentTime()
		# else:
			# timeToGrn += time
		# if pattern.startswith('GG'):
			# break
		# i += 1
		# if i == len(phaseList):
			# i = 0
			
	# for pattern,time in phaseList:
		# timeToGrn2 += time
		
	# greenTimes = (timeToGrn/1000, (timeToGrn+timeToGrn2)/1000)
	# send_time_to_grn(greenTimes)
	# return



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
							 "--tripinfo-output", "tripinfo.xml"])
	run()