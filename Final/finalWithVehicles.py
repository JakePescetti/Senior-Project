from __future__ import absolute_import
from __future__ import print_function
from datetime import date, timedelta, time, datetime
import os
import sys
import optparse

#import multiprocessing
import threading
import sumolib
import traci
import pyproj
import rtree
import time
import random
#!/usr/bin/env python


from threading import Thread
#from multiprocessing import Process, Pipe
from flask import Flask
from flask import request
from flask import jsonify
#from datetime import *




app = Flask(__name__)
global p 
global greenTimes
global dirty #locks the data command
global Lat
global Long
global TTL # time to live - set to 30 in main

""" These two were reversed but it has been fixed"""
Lat = 0
Long = 0


""" these variables hold the information on the bike, pull data from these """
global BikeLat, BikeSpeed, BikeBear, BikeLong #hold the position of the bike
BikeLat = 0
BikeLong = 0
BikeSpeed = 0
BikeBear = 0

@app.route('/data', methods=['POST', 'GET'])
def names():
	global BikeLat, BikeLong, BikeBear, BikeSpeed
	if request.method == 'POST':
		content = request.get_json()
		if content is not None:
			global BikeLat, BikeLong, BikeBear, BikeSpeed
			BikeLat = content.get('Lat','')
			BikeLong = content.get('Lng','')
			BikeBear = content.get('Bear','')
			BikeSpeed = content.get('speed','')	
		return "Tinker Bell"
	
	
	if request.method == 'GET': 
		global dirty # lock variable for update
		dirty = True #sets the lock
		while (dirty == True): #locks until next simulation step is done
			pass # do nothing
		
		global Lat, Long #pull data in from global
	
		global greenTimes
		
		now = datetime.utcnow()
		arive1 = (now + timedelta(seconds = greenTimes[0])).isoformat() # change from seconds to times
		arive2 = (now + timedelta(seconds = greenTimes[1])).isoformat() #change from seconds to times
		
		
		mydict = dict({"Lat" : Lat, "Lng" : Long, "Bear" : BikeBear, "Speed" : BikeSpeed, "BikeLat": BikeLat, "BikeLong": BikeLong, "TTL": TTL,"Times": [arive1, arive2]}) # payload to send back
		return jsonify(mydict) #return payload

def greenz(TraficID): #get the next two green times from TraficID
	tinker = traci.trafficlights.getCompleteRedYellowGreenDefinition(TraficID)[0]

	timeToGrn = 0
	timeToGrn2 = 0
   

	phaseList = [] # set up an empty list
	del phaseList[:] #I'm running Python 2.7
	#phaseList.clear() #make sure its empty
	for p in tinker._phases: # extract the list of phases from the logic class
		phaseList.append((p._phaseDef,p._duration)) # each phase in a list ('Marker', duration)
		
	current = traci.trafficlights.getPhase(TraficID)
	i = current		
	#how long is the current phase - getNextSwitch returns the simulation time of the next switch
	#so we have to subtract from it the current simulation time to get the remaining phaes time
	thisTime = traci.trafficlights.getNextSwitch(TraficID) - traci.simulation.getCurrentTime() # how long the current phase
	while 1:
		pattern,timey = phaseList[i]
		
		if pattern.startswith('G'): #must go first because if the phase is green then go on through
			break
			
		if i == current:
			timeToGrn += thisTime
		else:
			timeToGrn += timey
			
		i = (i + 1)%len(phaseList)
					
	timeToGrn2 = timeToGrn #timeToGrn2 is not really needed but this stops the extra math at greentimes
	
	for pattern,timey in phaseList:
		if(pattern.startswith('G') != 1): #excludeds the total curent phase time
			timeToGrn2 += timey
		
	timeToGrn2 += thisTime #adds the current phase time

	global greenTimes
	greenTimes = (timeToGrn/1000, (timeToGrn2)/1000) #double div makes it int division throw away that extra stuff hand grenades not sniper bullets
	
	global dirty
	dirty = False #clear the data update lock

def LightLocation(TrafficID):#gets the Location of the Traffic Light from TrafficID
	youAreHere = traci.junction.getPosition(TrafficID)
	LatLONG = traci.simulation.convertGeo(youAreHere[0],youAreHere[1])
	global Lat, Long
	Long, Lat = LatLONG
	
	
	
@app.route('/start')
def stratIt():
	taco = date.today().isoformat()
	return taco

@app.route('/stop')
def Stopit():
	return date.today().isoformat()


def EngineOn():
	options = get_options()
	# this script has been called from the command line. It will start sumo as a
	# server, then connect and run
	if (options.nogui):
		sumoBinary = checkBinary('sumo')
	else:
		sumoBinary = checkBinary('sumo-gui')
	# first, generate the route file for this simulation
	generate_routefile()

	# this is the normal way of using traci. sumo is started as a
	# subprocess and then the python script connects and runs
	traci.start([sumoBinary, "-c", "final.sumocfg",
							 "--full-output", "tripinfo.sbx"])
	run()
	

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
	random.seed(42)  # make tests reproducible
	N = 5000  # number of time steps
	# demand per second from different directions
	p1e = 1. / 10
	p1w = 1. / 11
	p2e = 1. / 20
	p2w = 1. / 11
	p3e = 1. / 20
	p4n = 1. / 11
	with open("final.rou.xml", "w") as routes:
		print("""<routes>
		<vType id="typeCager" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="20" guiShape="passenger"/>
		<vType id="typeBike" accel="0.5" decel="5" sigma="0.5" length="2" minGap="3" maxSpeed="20" guiShape="bicycle"/>
		
		<route id="cager1e" edges=":-61379_0 -61381#0 -61381#1 -432523794"/>
		<route id="cager1w" edges=":4343464730_0 432523794 --61381#1 --61381#0"/>
		<route id="cager2e" edges="-435041944#1 -435041944#0"/>
		<route id="cager2w" edges="435041944#0 435041944#1"/>
		<route id="cager3e" edges="-61290 -430638860#2 -430638860#1"/>
		<route id="cager4n" edges="-354871676 -434953517#0 -430638860#3 -430638860#2 -430638860#1"/>
		<route id="bike1" edges="430638860#0 430638860#1 430638860#2 430638860#3 434953517#0 434953517#1 434953517#2"/>""", file=routes)
		lastVeh = 0
		vehNr = 0
		for i in range(N):
			if random.uniform(0, 1) < p1e:
				print('	<vehicle id="1e_%i" type="typeCager" route="cager1e" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p1w:
				print('	<vehicle id="1w_%i" type="typeCager" route="cager1w" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p2e:
				print('	<vehicle id="2e_%i" type="typeCager" route="cager2e" depart="%i" color="1,0,0"/>' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p2w:
				print('	<vehicle id="2w_%i" type="typeCager" route="cager2w" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p3e:
				print('	<vehicle id="3e_%i" type="typeCager" route="cager3e" depart="%i" color="1,0,0"/>' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p4n:
				print('	<vehicle id="4n_%i" type="typeCager" route="cager4n" depart="%i" color="1,0,0"/>' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
		print("</routes>", file=routes)

def run():
	#net = sumolib.net.readNet('campusmap.net.xml')
#	oldUpcomingLightID = ''
	"""execute the TraCI control loop"""
	""" This stuff powers through the fist 2 steps"""
	step = 0
	traci.simulationStep()
	traci.simulationStep()
	step += 2
	traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
	traci.vehicle.setSpeed("bike",0)
	oldTLSID = ''
	while True:
		starttime=time.time()
		updatePosition()
		
		upcominglights = traci.vehicle.getNextTLS("bike")
		if len(upcominglights) > 0:
			tank = str(upcominglights[0][0])# tank holds the current traficlight ID, 
			#trafic light identification logic will have to be tied to this variable
			
			LightLocation(tank) # this pulls the trafic light location out and stores it in variables for usage
			greenz(tank) #has to be here beacuse flask crashes traci if it is after the simulation step
			#this must be processed in the simulation, can1t be done in the webserver it will break things
			#likely because it is not thread safe
			
			if tank != oldTLSID:
				clearCars(oldTLSID)
			elif upcominglights[0][2] < 5 and BikeSpeed != 0: #Check if cyclist id crossing intersection for warning beacon
				oldTLSID = tank
				warnCars(tank)
			
		traci.simulationStep()
		step += 1
		time.sleep(1.0 - ((time.time() - starttime) % 1.0))
	traci.close()
#	sys.stdout.flush()

def updatePosition():
	net = sumolib.net.readNet('final.net.xml')
	x, y = net.convertLonLat2XY(BikeLong, BikeLat)		
	edges = net.getNeighboringEdges(x, y, 0.6)
	# pick the closest edge (FIX THIS)
	if len(edges) > 0:
		distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])
		dist, closestEdge = distancesAndEdges[0]
		edge_id = closestEdge.getID()
	#update bike parameters
		traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
		traci.vehicle.setSpeed("bike",BikeSpeed)	#speed update
		
def warnCars(tlsID):
	allCars = traci.vehicle.getIDList()
	for car in allCars:
		if traci.vehicle.getSpeed(car)==0 and car != "bike": #only cars waiting at light that aren't the cyclist
			nextLight = traci.vehicle.getNextTLS(car)		#get the ID of the light in front of them
			if nextLight[0][0]==tlsID and nextLight[0][2] < 40: #make sure the car is stopped at an intersection and the ID matches the one the bike is crossing
				traci.vehicle.setColor(255,0,0,255) #set color to red
				traci.vehicle.setStop(car,traci.vehicle.getRoadID(car), traci.vehicle.getLanePosition(car), traci.vehicle.getLaneIndex(car), duration=20000, flags=0, startPos=-1001.0, until=-1)	#stop cars for 20 seconds

def clearCars(tlsID):
	allCars = traci.vehicle.getIDList()
	for car in allCars:
		if traci.vehicle.getSpeed(car)==0 and car != "bike": #only cars waiting at light that aren't the cyclist
			nextLight = traci.vehicle.getNextTLS(car)		#get the ID of the light in front of them
			if nextLight[0][0]==tlsID and nextLight[0][2] < 50: #make sure the car is stopped at an intersection and the ID matches the one the bike is crossing
				traci.vehicle.setColor(255,255,0,255) #default yellow color 255,255,0,255
				traci.vehicle.resume(car) #clear cars to go again
	

def get_options():
	optParser = optparse.OptionParser()
	optParser.add_option("--nogui", action="store_true",
						 default=False, help="run the commandline version of sumo")
	options, args = optParser.parse_args()
	return options
	

def gogo(): # StartsTraci Hosted on port 8080, with the machines IP address
	app.run(threaded=True, host = '0.0.0.0', port = 8080)
	
	
# this is the main entry point of this script
#if __name__ == "__main__":
	
if __name__ == '__main__':

	global TTL
	TTL = 30 # setting TTL to 30 as fixed channge this if needed
	e = threading.Thread(target= gogo)
#	d = threading.Thread(target=EngineOn) """ if we need to put traci into a thread"""
	e.daemon = True
	e.start()
#	d.start() """ if we need traci in a seperate thread"""
	EngineOn()
	e.join()# in theory this will stop the web server when traci stops, in pratice i think it is broken
