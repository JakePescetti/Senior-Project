import xml.etree.ElementTree as ET
import os
import xlwt

book = xlwt.Workbook(encoding="utf-8")
sheet1 = book.add_sheet("Sheet 1")
appEnergy=0.0
appTime=0
normalEnergy=0.0
normalTime=0
appEmissionsDir = "C:\Users\jake\eclipse-workspace\SeniorProjSimulationRuns\emissions"
normalEmissionsDir = "C:\Users\jake\eclipse-workspace\SeniorProjSimulationRuns\emissions-sim"

#format sheet

sheet1.write(0, 0, "Time using App (sec)")
sheet1.write(0, 1, "Energy using App (watts)")
sheet1.write(0, 2, "Time without App (secs)")
sheet1.write(0, 3, "Energy without App (watts)")

row=0

  
for filename in os.listdir(appEmissionsDir):
    row +=1
    tree = ET.parse(appEmissionsDir+"\\"+filename)
    for vehicle in tree.iter('vehicle'):
        appEnergy += float(vehicle.attrib['electricity'])
        appTime += 1
    sheet1.write(row,0,appTime)
    sheet1.write(row,1,appEnergy)
     
row=0
     
for filename in os.listdir(normalEmissionsDir):
    row +=1
    tree = ET.parse(normalEmissionsDir+"\\"+filename)
    for vehicle in tree.iter('vehicle'):
        normalEnergy += float(vehicle.attrib['electricity'])
        normalTime += 1
    sheet1.write(row,2,normalTime)
    sheet1.write(row,3,normalEnergy)

book.save("emissionsComparison.xls")