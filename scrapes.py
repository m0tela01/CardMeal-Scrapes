import csv
import json
import re
import time

from csv import writer
from datetime import datetime
from pprint import pprint

import pyrebase
import requests
from bs4 import BeautifulSoup

listOfLinks = []
weekDays = []
times = []

# Sets up Date and time locally
javaScriptDays = {days: [] for days in range(7)}
status = ''
currentTime = datetime.utcnow().time().replace(second=0,microsecond=0)
currentWeekDay = datetime.today().weekday()
currentWeekDay = currentWeekDay + 1
if currentWeekDay == 7:
   currentWeekDay = 0

# returns true if the current time is in the start/end times
def checkIfClosed(startTime, endTime, currTime):
   if startTime <= endTime:
       return startTime <= currTime <= endTime
   else:
       return startTime <= currTime or currTime <= endTime

# parse the main website
rootSite = 'https://louisville.campusdish.com'
response = requests.get(rootSite)
soup = BeautifulSoup(response.text, 'html.parser')

# parse the market place page
rootMarketplaceSite = 'https://louisville.campusdish.com/LocationsAndMenus/TheMarketplace'
responseMarketPlace = requests.get(rootMarketplaceSite)
soup2 = BeautifulSoup(responseMarketPlace.text, 'html.parser')

# header contents of the main webpage
divMenuContainer = soup.find(class_='container').find(class_='row')
divTopContainer = soup.find(class_='content-wrapper').find(class_='row')
divLocationContainer = divTopContainer.find(class_='locationList')
listOfTiles = divLocationContainer.select('li')

# header contents of the market place page
divMainMarketPlace = soup2.find(class_='main')
divMenuContainer2 = divMainMarketPlace.find(class_='container').select('.row')[1]
listOfTiles2 = divMenuContainer2.select('li')

idCounter = 0
# headers for csv and json files
headers = ['Id','Name','Status','Menu','Icon','Days','Hours','Description','Failed']

with open('resturantInfo.csv', 'w') as csv_file:
    csv_writer = writer(csv_file)
    csv_writer.writerow(headers)
    # the main website scrape
    for item in listOfTiles:
        try:
            resturantTile = item.select('.card-block')
            resturantHash = item.find('a')['href']

            # get the resturant icon image hash
            cardHeader = item.select('.card-header')[0].attrs
            resturantIcon = str(cardHeader).strip("{'class': ['card-header'], 'style': \"background-image:url('")
            resturantIcon = resturantIcon[:-5]
            resturantIcon = rootSite + resturantIcon

            resturantLink = rootSite + resturantHash
            listOfLinks.append(resturantLink)

            #redefine for each link
            response = requests.get(resturantLink)
            soup = BeautifulSoup(response.text, 'html.parser')
            divMenuContainer = soup.find(class_='container').find(class_='row')
            divTopContainer = soup.find(class_='content-wrapper').find(class_='row')
            divStandardHours = divTopContainer.select('.location__details')[0]
            divDescription = divTopContainer.select('.location__details')[1]

            # Page title
            pageTitle = divMenuContainer.find(class_='page-title').get_text()

            # Status
            status = divStandardHours.select_one('script').get_text()

            # finds out if the location is open or closed
            status = status.strip("\r\n\t\t\t\t\tvar currentHoursOfOperations = JSON.parse(\'")
            status = status.partition(";")[0]
            if status.endswith("\')"):
                status = status[:-2]
            jsonDates = json.loads(status)

            for line in jsonDates:
                UtcStartTime = ''
                UtcEndTime = ''
                weekDay = ''
                for key,value in line.items():
                    if key == 'UtcStartTime':
                        UtcStartTime = re.sub(r'.*T', '', value)[:-1]
                    if key == 'UtcEndTime':
                        UtcEndTime = re.sub(r'.*T', '', value)[:-1]
                    if key == 'WeekDay':
                        weekDay = value
              
                startTime = datetime.strptime(UtcStartTime, '%H:%M:%S').time()
                endTime = datetime.strptime(UtcEndTime, '%H:%M:%S').time()

                isOpen = checkIfClosed(startTime, endTime, currentTime)
                javaScriptDays[int(weekDay)].append(str(isOpen))
              
                # might be useful later
                javaScriptDays[int(weekDay)].append("("+UtcStartTime+")")
                javaScriptDays[int(weekDay)].append("("+UtcEndTime+")")
            
            if len(javaScriptDays[int(currentWeekDay)]) is 0:
                status = 'Closed'
            else:
                testnCheck = javaScriptDays[int(currentWeekDay)][0]
                status = 'Open'
                
                # Special handling for The Ville Gril's odd hours format
                if resturantHash == '/LocationsAndMenus/TheVilleGrill':
                    dayOfWeek = javaScriptDays[int(currentWeekDay)]
                    isOperating = False
                    # loop throught the data for that day
                    for value in dayOfWeek:
                        # if its open currently at least one value is true
                        if value == 'True':
                            isOperating = True
                            break
                    if isOperating == False:
                        status = 'Closed'
                else:   
                    if javaScriptDays[int(currentWeekDay)][0] == 'False' or javaScriptDays[int(currentWeekDay)][0] == '':
                        status = 'Closed'
            # finds out if the location is open or closed 
          
            # Menu
            menuHash = divMenuContainer.find('a')['href']

            # Special handling for The Ville Grill's odd menu format
            if pageTitle == 'The Ville Grill':
                menuLink = resturantLink
            else:
                menuLink = rootSite + menuHash

            #Standard Hours Panel
            dayOfWeek = divStandardHours.select('.location__day')
            timeOfDay = divStandardHours.select('.location__times')

            #Description paragraph
            description = divDescription.find('p').get_text()
            description = str(description).replace("b'","")
            description = str(description).replace(u'\xa0',u'')

            # Output
            print(pageTitle)    # print the name if the restuarant works
            for item in dayOfWeek:
                weekDays.append(item.get_text())
            for item in timeOfDay:
                times.append(item.get_text())
            idCounter = idCounter + 1
            csv_writer.writerow([str(idCounter),pageTitle,status,menuLink,str(resturantIcon),str(weekDays),str(times),description,""])
            weekDays.clear()
            times.clear()
            javaScriptDays = {days: [] for days in range(7)}
        except:
            pass
            weekDays.clear()
            times.clear()
            javaScriptDays = {days: [] for days in range(7)}
            
    # the market place page scrape
    for item in listOfTiles2:
        try:
            resturantTile = item.select('.card-block')
            resturantHash = item.find('a')['href']

            # get the resturant icon image hash
            cardHeader = item.select('.card-header')[0].attrs
            resturantIcon = str(cardHeader).strip("{'class': ['card-header'], 'style': \"background-image:url('")
            resturantIcon = resturantIcon[:-5]
            resturantIcon = rootSite + resturantIcon

            resturantLink = rootSite + resturantHash
            listOfLinks.append(resturantLink)

            #redefine for each link
            response = requests.get(resturantLink)
            soup = BeautifulSoup(response.text, 'html.parser')
            divMenuContainer = soup.find(class_='container').find(class_='row')
            divTopContainer = soup.find(class_='content-wrapper').find(class_='row')
            divStandardHours = divTopContainer.select('.location__details')[0]
            divDescription = divTopContainer.select('.location__details')[1]

            # Page title
            pageTitle = divMenuContainer.find(class_='page-title').get_text()

            # Status
            status = divStandardHours.select_one('script').get_text()

            # finds out if the location is open or closed
            status = status.strip("\r\n\t\t\t\t\tvar currentHoursOfOperations = JSON.parse(\'")
            status = status.partition(";")[0]
            if status.endswith("\')"):
                status = status[:-2]
            jsonDates = json.loads(status)

            for line in jsonDates:
                UtcStartTime = ''
                UtcEndTime = ''
                weekDay = ''
                for key,value in line.items():
                    if key == 'UtcStartTime':
                        UtcStartTime = re.sub(r'.*T', '', value)[:-1]
                    if key == 'UtcEndTime':
                        UtcEndTime = re.sub(r'.*T', '', value)[:-1]
                    if key == 'WeekDay':
                        weekDay = value
              
                startTime = datetime.strptime(UtcStartTime, '%H:%M:%S').time()
                endTime = datetime.strptime(UtcEndTime, '%H:%M:%S').time()

                isOpen = checkIfClosed(startTime, endTime, currentTime)
                javaScriptDays[int(weekDay)].append(str(isOpen))
              
                # might be useful later
                javaScriptDays[int(weekDay)].append("("+UtcStartTime+")")
                javaScriptDays[int(weekDay)].append("("+UtcEndTime+")")

            if len(javaScriptDays[int(currentWeekDay)]) is 0:
                    status = 'Closed'
            else:
                testnCheck = javaScriptDays[int(currentWeekDay)][0]
                status = 'Open'
                # Special handling for The Ville Gril's odd hours format
                if resturantHash == '/LocationsAndMenus/TheVilleGrill':
                    dayOfWeek = javaScriptDays[int(currentWeekDay)]
                    isOperating = False
                    # loop throught the data for that day
                    for value in dayOfWeek:
                        # if its open currently at least one value is true
                        if value == 'True':
                            isOperating = True
                            break
                    if isOperating == False:
                        status = 'Closed'
                else:   
                    if javaScriptDays[int(currentWeekDay)][0] == 'False' or javaScriptDays[int(currentWeekDay)][0] == '':
                        status = 'Closed'
            # finds out if the location is open or closed 
          
            # Menu
            menuHash = divMenuContainer.find('a')['href']

            # Special handling for The Ville Grill's odd menu format
            if pageTitle == 'The Ville Grill':
                menuLink = resturantLink
            else:
                menuLink = rootSite + menuHash

            #Standard Hours Panel
            dayOfWeek = divStandardHours.select('.location__day')
            timeOfDay = divStandardHours.select('.location__times')

            #Description paragraph
            description = divDescription.find('p').get_text()
            description = str(description).replace("b'","")
            description = str(description).replace(u'\xa0',u'')

            # Output
            print(pageTitle)    # print the name if the restuarant works
            for item in dayOfWeek:
                weekDays.append(item.get_text())
            for item in timeOfDay:
                times.append(item.get_text())
            idCounter = idCounter + 1
            csv_writer.writerow([str(idCounter),pageTitle,status,menuLink,str(resturantIcon),str(weekDays),str(times),description,""])
            weekDays.clear()
            times.clear()
            javaScriptDays = {days: [] for days in range(7)}
        except:
            print("This site did not work: " + rootMarketplaceSite + resturantHash)
            #csv_writer.writerow(["","","","","","","",resturantLink])
            weekDays.clear()
            times.clear()
            javaScriptDays = {days: [] for days in range(7)}


# creates a json file for firebase from generated csv above
with open('resturantInfo.csv', 'r') as csvresturantInfo:
    with open('resturantInfo.json', 'w') as jsonresturantInfo:
        reader = csv.DictReader(csvresturantInfo, headers)
        head = True
        index = 0
        idCounter = idCounter - 6   # remove repeated resturantes

        jsonresturantInfo.write('[\n')
        for row in reader:
            if head:
                head = False
                continue
            else:
                if index < idCounter:
                    json.dump(row,jsonresturantInfo)
                    jsonresturantInfo.write(',\n')
                    index = index + 1
                elif index == idCounter:
                    json.dump(row,jsonresturantInfo)
                    jsonresturantInfo.write('\n')
                    index = index + 1
                else:
                    break
        jsonresturantInfo.write(']')

print('\nUpdateing Firebase')
# post scrapes to firebase
config = {
    'apiKey': 'AIzaSyCx9aSj07cOAtI-m7nBluMHXqEvTYyyXkc',
    'authDomain': 'dining-services.firebaseapp.com',
    'databaseURL': 'https://dining-services.firebaseio.com',
    'projectId': 'dining-services',
    'storageBucket': 'dining-services.appspot.com',
    'messagingSenderId': '9791725706'
}

firebase = pyrebase.initialize_app(config)

# Get a reference to the auth service
auth = firebase.auth()

# Log the user in
email = 'kuhl.de.1337@gmail.com'  # Replace Email
password = 'very_secure_password12345'  # Replace Password

user = auth.sign_in_with_email_and_password(email, password)

# Get a reference to the database service
db = firebase.database()

# open json file and get ready to import to firebase
with open ("resturantInfo.json",'r') as data_file:
    data=json.load(data_file)


db.child("").remove()
results = db.child('').set(data, user['idToken'])

print('\nDone!')
