from __future__ import absolute_import
from __future__ import print_function
from datetime import date, timedelta, time, datetime
import os
import sys
import optparse
import threading
import sumolib
import traci
import pyproj
import rtree
import time
import random
#!/usr/bin/env python


from threading import Thread
from flask import Flask
from flask import request
from flask import jsonify


app = Flask(__name__)
global p 
global greenTimes
global dirty #locks the data command
global Lat
global Long
global TTL # time to live - set to 30 in main
global net
global MinGreen
MinGreen = 5000
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
	#phaseList.clear() #make sure its empty
	for p in tinker._phases: # extract the list of phases from the logic class
		phaseList.append((p._phaseDef,p._duration)) # each phase in a list ('Marker', duration)
		
	current = traci.trafficlights.getPhase(TraficID)
	i = current		
	#how long is the current phase - getNextSwitch returns the simulation time of the next switch
	#so we have to subtract from it the current simulation time to get the remaining phaes time
	thisTime = traci.trafficlights.getNextSwitch(TraficID) - traci.simulation.getCurrentTime() # how long the current phase

	numberOfGreens = 0
	runingTime = 0
	Phase = i;
	global MinGreen
	
	while 1:
		pattern,timey = phaseList[i]
		if pattern.startswith('G'):
			ptemp, ttemp = phaseList[(i+1)%len(phaseList)] #next patter on the list used below for lookahaed
			if(Phase != i): #if we are in future phases
				if ((timey > MinGreen) or(ptemp.startswith('G') & (ttemp+ttemp> MinGreen))):
				#we only want the greeen when the green time remaining is more than MinGReen seconds
					runingTime += MinGreen # we have to place the time MinGreen seconds into the future or stuff will break
					if (numberOfGreens == 0):
						timeToGrn = runingTime 
						numberOfGreens += 1 #keep trak were not done yet
					else: # we have #2 so we can stop now
						timeToGrn2 = runingTime
						break #break when the second greeen time is reached
			if ((thisTime > MinGreen) or(ptemp.startswith('G') & (ttemp+thisTime> MinGreen))):
				#we only want the greeen when the green time remaining is more than MinGReen seconds
				runingTime += MinGreen # we have to place the time MinGreen seconds into the future or stuff will break
				if (numberOfGreens == 0):
					timeToGrn = runingTime 
					numberOfGreens += 1 #keep trak were not done yet
				else: # we have #2 so we can stop now
					timeToGrn2 = runingTime
					break #break when the second greeen time is reached
		elif (Phase == current): #if this is the current phase then add only the time remaining
			runingTime += thisTime
		else: #if this is not the current phase and not green we don't care add the time
			runingTime += timey
				   
		
#		if pattern.startswith('G'): #must go first because if the phase is green then go on through
#			break
#			
#		if i == current:
#			timeToGrn += thisTime
#		else:
#			timeToGrn += timey
		Phase += 1
		i = (i + 1)%len(phaseList)
					
	#timeToGrn2 = timeToGrn #timeToGrn2 is not really needed but this stops the extra math at greentimes
	
#	for pattern,timey in phaseList:
#		if(pattern.startswith('G') != 1): #excludeds the total curent phase time
#			timeToGrn2 += timey
		
#	timeToGrn2 += thisTime #adds the current phase time
	
	global TTL
	
	global greenTimes
	greenTimes = (timeToGrn/1000, (timeToGrn2)/1000) #double div makes it int division throw away that extra stuff hand grenades not sniper bullets
	
	if (greenTimes[1] < 30): #TTL is the lesser of 30 seconds or the time till green
		TTL = greenTimes
	else:
		TTL = 30
	
	
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
	traci.start([sumoBinary, "-c", "horses.sumocfg", "--ignore-route-errors",
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
	p1s = 1. / 10
	p1n = 1. / 11
	p3s = 1. / 20
	p4e = 1. / 11
	p4w = 1. / 20
	with open("horses.rou.xml", "w") as routes:
		print("""<routes>
		<vType id="typeCager" accel="0.8" decel="9" sigma="0.5" length="5" minGap="2.5" maxSpeed="20" guiShape="passenger"/>
		<vType id="typeBike" vClass="emergency" color="blue" accel="0.5" decel="5" sigma="0" length="2" minGap="0" maxSpeed="20" jmDriveAterRedTime="100" guiShape="bicycle"/>
		
		<route id="cager1s" edges="-433065964#1 --40295#1 --40295#0"/>
		<route id="cager1n" edges="-40295#0 -40295#1 -433065964#0 -433066001 -50439396#1 -40295#1"/>
		<route id="cager3s" edges="-13373927#3 -13373927#2 430638836#0"/>
		<route id="cager4e" edges="-40297#0 -40297#1"/>
		<route id="cager4w" edges="--40297#1 --40297#0"/>
		<route id="bike1" edges="50439396#0 50439396#1 50439396#2 -13373927#2 -13373927#1 -13373927#0 -13275797#2"/>""", file=routes)
		#<route id="bike1" edges="-50439396#0 -50439396#1 -50439396#2 -13373927#3 -13373927#1 -13373927#0 -13275797#2"/>""", file=routes)
		lastVeh = 0
		vehNr = 0
		for i in range(N):
			if random.uniform(0, 1) < p1s:
				print('	<vehicle id="1s_%i" type="typeCager" route="cager1s" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p1n:
				print('	<vehicle id="1n_%i" type="typeCager" route="cager1n" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p3s:
				print('	<vehicle id="3s_%i" type="typeCager" route="cager3s" depart="%i"/>' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p4e:
				print('	<vehicle id="4e_%i" type="typeCager" route="cager4e" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < p4w:
				print('	<vehicle id="4w_%i" type="typeCager" route="cager4w" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
		print("</routes>", file=routes)

def run():
	"""execute the TraCI control loop"""
	""" This stuff powers through the fist 2 steps"""
	step = 0
	traci.simulationStep()
	traci.simulationStep()
	step += 2
	traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
	traci.vehicle.setSpeed("bike",0)
	oldTLSID = ''
	warnCounter=0
	warnRepeat = 0
	savedLight = ''
	carsWarned = False
	warningTriggered=False
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
			if upcominglights[0][2] < 30 and BikeSpeed > 0: #Check if cyclist is going for it to trigger warning beacon
				warnRepeat = 8
				savedLight = tank
				warningTriggered = True
			
			if warnRepeat > 0:
				warnCars(savedLight)
				warnRepeat -= 1
				
			if warnRepeat == 0 and warningTriggered == True: #Reset cars
				clearCars()
				warningTriggered = False
			
			# if carsWarned == True and tank != oldTLSID and step-warnCounter > 5:
				# clearCars(oldTLSID)
				# carsWarned = False
			# elif upcominglights[0][2] < 12 and BikeSpeed > 0: #Check if cyclist is crossing intersection for warning beacon
				# oldTLSID = tank
				# warnCars(tank)
				# warnCounter = step
				# carsWarned = True
			
		traci.simulationStep()
		step += 1
		time.sleep(1.0 - ((time.time() - starttime) % 1.0))
	traci.close()
#	sys.stdout.flush()

def updatePosition():
	net = sumolib.net.readNet('horses.net.xml')
	x, y = net.convertLonLat2XY(BikeLong, BikeLat)		
	edges = net.getNeighboringEdges(x, y, 0.6)
	if len(edges) > 0:
		distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])
		dist, closestEdge = distancesAndEdges[0]
		edge_id = closestEdge.getID()
	#update bike parameters
		traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
		traci.vehicle.setSpeed("bike",BikeSpeed)	#speed update
	
	# global net	
	# x, y = traci.simulation.convertGeo(BikeLong, BikeLat, fromGeo=True)
	# #sumolib.net.convertLonLat2XY(BikeLong, BikeLat)		
	# edges = net.getNeighboringEdges(x, y, 0.6)
	# # pick the closest edge (FIX THIS)

	# #traci.domain.Domain.getIDList
	# #put default case for edge_id to somethnig
	# if edges == []: #for case of no known bike lat
		# edges = net.getEdges()
		# edge_id = edges[2].getID()
	# else: # this sectoin needs to be fixed the sorting is terible, 
		# distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])#rewrtie this line
		# #distancesAndEdges = sorted(edges, key=lambda edges: edges[1]) # this is the basis
		# dist, closestEdge = distancesAndEdges[0]
		# edge_id = closestEdge.getID()
		# #traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
	# #update bike parameters
	
	# if(BikeLat == 0 or BikeLong == 0):	
		# traci.vehicle.moveToXY("bike",edge_id,0,189.73,495.91,angle=BikeBear,keepRoute=2) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
	# else:
		# traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
	# traci.vehicle.setSpeed("bike",BikeSpeed)	#speed update
		
def warnCars(tlsID):
	#get position of junction
	#loop and get all vehicles in a certain radius of intersection
	#check direction of vehicles?
	radius = 30
	x1,y1 = traci.junction.getPosition(tlsID)
	allCars = traci.vehicle.getIDList()
	for car in allCars:
		x2,y2 = traci.vehicle.getPosition(car)
		dist = traci.simulation.getDistance2D(x1,y1,x2,y2, isGeo=False, isDriving=False)
		#print(dist)
		if dist < radius and car != "bike" and traci.vehicle.getSpeed(car)==0:
			traci.vehicle.setColor(car,(255,0,0,255)) #set color to red
			#traci.vehicle.setStop(car,traci.vehicle.getRoadID(car), traci.vehicle.getLanePosition(car), traci.vehicle.getLaneIndex(car), duration=20000, flags=0, startPos=-1001.0, until=-1)	#stop cars for 20 seconds
			traci.vehicle.slowDown(car,0,1500)
			print('car warned\n') #debugging
				
def clearCars():
	allCars = traci.vehicle.getIDList()
	for car in allCars:
		if car != "bike":
			traci.vehicle.setColor(car,(255,255,0,255)) #default yellow color 255,255,0,255
			traci.vehicle.slowDown(car,traci.vehicle.getSpeedWithoutTraCI(car),3000)
			print('car cleared\n')
		# if traci.vehicle.isStopped(car):
			# traci.vehicle.resume(car) #clear cars to go again
			#print('car cleared\n')
	
def get_options():
	optParser = optparse.OptionParser()
	optParser.add_option("--nogui", action="store_true",
						 default=False, help="run the commandline version of sumo")
	options, args = optParser.parse_args()
	return options
	

def gogo(): # StartsTraci Hosted on port 8080, with the machines IP address
	app.run(threaded=True, host = '0.0.0.0', port = 8080)
	
	
# this is the main entry point of this script	
if __name__ == '__main__':

	global TTL
	#net = sumolib.net.readNet('horses.net.xml')
	TTL = 30 # setting TTL to 30 as fixed channge this if needed
	e = threading.Thread(target= gogo)
#	d = threading.Thread(target=EngineOn) """ if we need to put traci into a thread"""
	e.daemon = True
	e.start()
#	d.start() """ if we need traci in a seperate thread"""
	EngineOn()
	e.join()# in theory this will stop the web server when traci stops, in pratice i think it is broken
