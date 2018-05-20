from __future__ import absolute_import
from __future__ import print_function
#from datetime import date, timedelta, time, datetime
import os
import sys
import optparse
import sumolib
import traci
#import random
import time

global p 
global greenTimes
global net
global MinGreen
MinGreen = 5000
global maxSpeed
maxSpeed = 10
global minDist
minDist = 10
global waitCount
waitCount = 66



def greenz(TraficID): #get the next two green times from TraficID
    tinker = traci.trafficlights.getCompleteRedYellowGreenDefinition(TraficID)[0]

    timeToGrn = 2000   #need to arrive with some buffer time
    timeToGrn2 = 1  
    phaseNum = 0
    
    currentEdgeIndex = traci.vehicle.getRouteIndex('bike')
    edgeList = traci.vehicle.getRoute('bike')
    inEdge,outEdge = edgeList[currentEdgeIndex],edgeList[currentEdgeIndex+1]
    #parse link list
#     print(inEdge,outEdge)
    
    linkList = traci.trafficlights.getControlledLinks(TraficID)
#     print(linkList)


    for k in range(len(linkList)):
        if linkList[k][0][0].startswith(inEdge) and linkList[k][0][1].startswith(outEdge):
            phaseNum = k

            
    phaseList = [] # set up an empty list
    #phaseList.clear() #make sure its empty
    for p in tinker._phases: # extract the list of phases from the logic class
        phaseList.append((p._phaseDef,p._duration)) # each phase in a list ('Marker', duration)
        
    current = traci.trafficlights.getPhase(TraficID)
    i = current        
    #how long is the current phase - getNextSwitch returns the simulation time of the next switch
    #so we have to subtract from it the current simulation time to get the remaining phaes time
    thisTime = traci.trafficlights.getNextSwitch(TraficID) - traci.simulation.getCurrentTime() # how long the current phase
    
    timeToGrn += thisTime #Add remaining phase time
    i += 1
    if i >= len(phaseList):
            i = 0
    pattern,phaseLength = phaseList[i]
    if pattern[phaseNum] == 'G' or pattern[phaseNum] == 'g':   
        timeToGrn -= 2000  #Don't want to buffer if current light is green
        
    while not pattern[phaseNum] == 'G' and not pattern[phaseNum] == 'g':
        timeToGrn += phaseLength
        i += 1
        if i >= len(phaseList):
            i = 0
        pattern,phaseLength = phaseList[i]

        
    timeToGrn2 += timeToGrn  #Add time to first green to time to second green
    for pattern,phaseLength in phaseList:
        timeToGrn2 += phaseLength   #Add complete program duration (one complete cycle)
       
    global greenTimes
    greenTimes = (timeToGrn/1000, (timeToGrn2)/1000) #double div makes it int division throw away that extra stuff hand grenades not sniper bullets
    

def EngineOn():
    options = get_options()
    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if (options.nogui):
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    # first, generate the route file for this simulation
    #generate_routefile()
    timeNow = time.strftime("%Y%m%d-%H%M%S")
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumoBinary, "-c", "bric.sumocfg",
                             "--full-output", "fulloutput/tripinfo-"+str(waitCount)+"-"+timeNow+".xml", "--emission-output", "emissions/emissions-"+str(waitCount)+"-"+timeNow+".xml"]) #may need to add  "--ignore-route-errors"
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

def run():
    """execute the TraCI control loop"""
    """ This stuff powers through the fist 2 steps"""
    step = 0
    
    for i in range(0,waitCount):
        traci.simulationStep()
        step += 1
    
    
    traci.vehicle.add("bike", "bike1", typeID='typeBike')  #Adds bike to simulation
    traci.vehicle.setSpeed('bike',5)
    #traci.vehicle.slowDown('bike',3,2500) #start moving
    warnRepeat = 0
    savedLight = ''
    warningTriggered=False
    while True:
        upcominglights = traci.vehicle.getNextTLS("bike")
        if len(upcominglights) > 0:
            nextID = str(upcominglights[0][0])# tank holds the current traficlight ID, 
            nextDist = upcominglights[0][2] #distance to next light
            #trafic light identification logic will have to be tied to this variable
            
            greenz(nextID) #has to be here beacuse flask crashes traci if it is after the simulation step
            #this must be processed in the simulation, can1t be done in the webserver it will break things
            #likely because it is not thread safe
            newSpeed = getBestSpeed(nextDist)
            traci.vehicle.slowDown('bike',newSpeed,2500)
            
            #print(traci.trafficlights.getControlledLinks(nextID))
            #print(traci.trafficlights.getControlledLanes(nextID))
            
            #Car warning blob
            if upcominglights[0][2] < 40 and newSpeed > 0: #Check if cyclist is going for it to trigger warning beacon
                warnRepeat = 8
                savedLight = nextID
                warningTriggered = True
            
            if warnRepeat > 0: #keeps repeating warning to ensure message is sent in case of GPS "bouncing"
                warnCars(savedLight)
                warnRepeat -= 1
                
            if warnRepeat == 0 and warningTriggered == True: #Reset cars
                clearCars()
                warningTriggered = False
        
#             print('speed: ' + repr(newSpeed) +', distance: ' +  repr(nextDist) + ', green times: '+ repr(greenTimes))
#             if step == 120:
#                 print(traci.trafficlights.getControlledLinks(nextID))
        traci.simulationStep()
        step += 1
        #time.sleep(1.0 - ((time.time() - starttime) % 1.0)) #keeps each simulation step at 1 second to sync with real time
    traci.close()
#    sys.stdout.flush()

def getBestSpeed(dist):
    if dist > minDist:
        try:
            speed = dist/greenTimes[0]
        except ZeroDivisionError:
            speed = 300
        
        if speed > maxSpeed:
            try:
                speed = dist/greenTimes[1]
            except ZeroDivisionError:
                speed = 300
    else:
        #speed = traci.vehicle.getSpeedWithoutTraCI('bike')
        speed = 6
    return speed

        
def warnCars(tlsID):
    #get position of junction
    #loop and get all vehicles in a certain radius of intersection
    radius = 40
    x1,y1 = traci.junction.getPosition(tlsID)
    allCars = traci.vehicle.getIDList()
    #check if other vehicles in to avoid crashing the sim
    if len(allCars)>1:
        for car in allCars:
            x2,y2 = traci.vehicle.getPosition(car)
            dist = traci.simulation.getDistance2D(x1,y1,x2,y2, isGeo=False, isDriving=True)
            if dist < radius and car != "bike" and traci.vehicle.getSpeed(car)==0:
                traci.vehicle.setColor(car,(255,0,0,255)) #set color to red to show car is warned
                traci.vehicle.slowDown(car,0,1500) #can't stop car while moving, crashes SUMO
                print('car warned\n') #debugging
                
def clearCars():
    #clear all cars in simulation
    allCars = traci.vehicle.getIDList()
    #check for other vehicles to avoid crashing the sim
    if len(allCars)>1:
        for car in allCars:
            if car != "bike":
                traci.vehicle.setColor(car,(255,255,0,255)) #default yellow color 255,255,0,255
                traci.vehicle.slowDown(car,traci.vehicle.getSpeedWithoutTraCI(car),3000) #Resumes original speed of car
                print('car cleared\n')
    
def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=True, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options
    
  
# this is the main entry point of this script    
if __name__ == '__main__':

    EngineOn()
    #e.join()# in theory this will stop the web server when traci stops, in pratice i think it is broken