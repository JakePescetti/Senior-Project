#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import subprocess
import random
import math

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
#import sumolib

def generate_routefile():
	random.seed(42)  # make tests reproducible
	N = 5200  # number of time steps
	# demand per second from different directions
	pNS1 = 1. / 10
	pSN1 = 1. / 10
	pNS2 = 1. / 11
	pSN2 = 1. / 11
	with open("twoint.rou.xml", "w") as routes:
		print("""<routes>
		<vType id="typeNS" accel="1" decel="4.5" sigma="0.5" length="5" minGap="3" maxSpeed="8" guiShape="passenger"/>
		<vType id="typeBike" accel="0.5" decel="5" sigma="0.5" length="2" minGap="3" maxSpeed="2" guiShape="bicycle"/>
		<route id="up1" edges="94o 4o 2i 92i" />
		<route id="down1" edges="92o 2o 4i 94i" />
		<route id="up2" edges="97o 7o 5i 95i" />
		<route id="down2" edges="95o 5o 7i 97i" />
		<route id="bike1" edges="91o 1o 3o 8i 98i"/>""", file=routes)
		
		lastVeh = 0
		vehNr = 0
		for i in range(N):
			if random.uniform(0, 1) < pSN1:
				print('	<vehicle id="up1_%i" type="typeNS" route="up1" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < pNS1:
				print('	<vehicle id="down1_%i" type="typeNS" route="down1" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < pSN2:
				print('	<vehicle id="up2_%i" type="typeNS" route="up2" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
			if random.uniform(0, 1) < pNS2:
				print('	<vehicle id="down2_%i" type="typeNS" route="down2" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
				lastVeh = i
		print("</routes>", file=routes)

def run():
	"""execute the TraCI control loop"""
	step = 0
	bikeInRange=False
	bikeInSim=False
	while traci.simulation.getMinExpectedNumber() > 0:
		if step == 100:
			traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
			bikeInSim=True
		if bikeInSim:
			bikeSpeed=traci.vehicle.getSpeed("bike") if traci.vehicle.getSpeed("bike")>0 else 0.00001
			bikeLoc=traci.vehicle.getPosition("bike")
			bikeDist=math.sqrt((bikeLoc[0]-504.0)*(bikeLoc[0]-504.0)+(bikeLoc[1]-1008.0)*(bikeLoc[1]-1008.0))
			print ("Bike dist: ",bikeDist)
			bikeTimetoInter=bikeDist / bikeSpeed if (bikeDist / bikeSpeed)>0 else 100000
			print ("Bike time to int: ",bikeTimetoInter)
			if (bikeTimetoInter <= 100):
				bikeInRange=True
		if bikeInRange==True:
			traci.edge.setMaxSpeed("4o",2)
			traci.edge.setMaxSpeed("2o",2)
		if step == 400:
			traci.vehicle.moveToXY("bike","3o",0,200,1000,angle=-1001.0,keepRoute=1)
		traci.simulationStep()
		step += 1
	traci.close()
	sys.stdout.flush()


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
	traci.start([sumoBinary, "-c", "twoint.sumocfg",
							 "--tripinfo-output", "tripinfo.xml"])
	run()