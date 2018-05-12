from __future__ import absolute_import
from __future__ import print_function
from datetime import date, timedelta, time, datetime
import os
import sys
import optparse
import time
#import multiprocessing
import threading
import sumolib
import traci
import pyproj
#import rtree
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
    phaseList.clear() #make sure its empty
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
                   
        
#        if pattern.startswith('G'): #must go first because if the phase is green then go on through
#            break
#            
#        if i == current:
#            timeToGrn += thisTime
#        else:
#            timeToGrn += timey
        Phase += 1
        i = (i + 1)%len(phaseList)
                    
    #timeToGrn2 = timeToGrn #timeToGrn2 is not really needed but this stops the extra math at greentimes
    
#    for pattern,timey in phaseList:
#        if(pattern.startswith('G') != 1): #excludeds the total curent phase time
#            timeToGrn2 += timey
        
#    timeToGrn2 += thisTime #adds the current phase time
    
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
    traci.start([sumoBinary, "-c", "campusmap.sumocfg",
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
    with open("campusmap.rou.xml", "w") as routes:
        print("""<routes>
        <vType id="typeBike" accel="0.5" decel="5" sigma="0.5" length="2" minGap="3" maxSpeed="15" guiShape="bicycle"/>
        <route id="bike1" edges="430638860#0 430638860#1 430638860#2 430638860#3 434953517#0 434953517#1 434953517#2"/>""", file=routes)
        
        print("</routes>", file=routes)

def run():
    global net
    net = sumolib.net.readNet('campusmap.net.xml')
#    oldUpcomingLightID = ''
    """execute the TraCI control loop"""
    """ This stuff powers through the fist 2 steps"""
    step = 0
    traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
    traci.vehicle.setSpeed("bike",0)
    
    traci.simulationStep()
    traci.simulationStep()
    step += 2
    lastCycle=datetime.utcnow()
    cycleDelta = timedelta(seconds = 0)
    
    while True:
        
        
        
        
        updatePosition()
        tanks = traci.vehicle.getNextTLS("bike") # tank holds the current traficlight ID, 
        #trafic light identification logic will have to be tied to this variable
        if len(tanks) > 0:
            #sorted(tanks, key=lambda tanks: tanks[2]) # sorts based on parameter 2
            tank = tanks[0][0]
        
        LightLocation(tank) # this pulls the trafic light location out and stores it in variables for usage
        greenz(tank) #has to be here beacuse flask crashes traci if it is after the simulation step
        #this must be processed in the simulation, can1t be done in the webserver it will break things
        #likely because it is not thread safe
        
        traci.simulationStep()
        step += 1

        while(lastCycle + cycleDelta > datetime.utcnow()): #do while it hasn't taken 1 second
            pass #do nothing
        
    traci.close()
#    sys.stdout.flush()

def updatePosition():
    global net
    x, y = traci.simulation.convertGeo(BikeLong, BikeLat, fromGeo=True)
    #sumolib.net.convertLonLat2XY(BikeLong, BikeLat)        
    edges = net.getNeighboringEdges(x, y, 0.6)
    # pick the closest edge (FIX THIS)

    #traci.domain.Domain.getIDList
    #put default case for edge_id to somethnig
    if edges == []: #for case of no known bike lat
        edges = net.getEdges()
        edge_id = edges[2].getID()
    else: # this sectoin needs to be fixed the sorting is terible, 
        distancesAndEdges = sorted([(dist, edge) for edge, dist in edges])#rewrtie this line
        #distancesAndEdges = sorted(edges, key=lambda edges: edges[1]) # this is the basis
        dist, closestEdge = distancesAndEdges[0]
        edge_id = closestEdge.getID()
        traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
    #update bike parameters
    
    if(BikeLat == 0 or BikeLong == 0):    
        traci.vehicle.moveToXY("bike",edge_id,0,190,36,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
    else:
        traci.vehicle.moveToXY("bike",edge_id,0,x,y,angle=BikeBear,keepRoute=1) #(vehID, edge, lane index, x, y, angle, keepRoute 0-2)
    traci.vehicle.setSpeed("bike",BikeSpeed)    #speed update

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
#    d = threading.Thread(target=EngineOn) """ if we need to put traci into a thread"""
    e.daemon = True
    e.start()
#    d.start() """ if we need traci in a seperate thread"""
    EngineOn()
    e.join()# in theory this will stop the web server when traci stops, in pratice i think it is broken
