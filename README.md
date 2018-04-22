# Senior-Project
Connected cyclist

server: http://165.227.7.177/data

need to install the following with pip:
  -pyproj
  -Rtree

4/22/18: 
  -SUMO waits for a change in the gps.pkl file from the app. It then calculates and updates time.pkl with the time to next green and the one after that (in case the time is too short)
  -The change in gps.pkl can be triggered by running filemodscript.py concurrently with campustesting-threading.py
  -Still deciding best way to decide when to update time.pkl
  
  ISSUES:
    -timeWorker function is SLOW! Calling the function too often causes it to take even longer. Haven't made it crash yet though.
    -We need to find a better way of deciding when to calculate "time to green"
    -I tried for hours and cannot figure out how to interpret the output of traci.trafficlights.getCompleteRedYellowGreenDefinition()
      When printing it, it gives a structured output like XML but I can't extract what I need from it so I had to resort to parsing the         string, which takes a while.
