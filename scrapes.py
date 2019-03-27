import re
from csv import writer
import csv
import json
import requests
from bs4 import BeautifulSoup

listOfLinks = []
weekDays = []
times = []

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
headers = ['Id','Name','Status','Menu','Days','Hours','Description','Failed']

with open('resturantInfo.csv', 'w') as csv_file:
    csv_writer = writer(csv_file)
    csv_writer.writerow(headers)
    # the main website scrape
    for item in listOfTiles:
        try:
            resturantTile = item.select('.card-block')
            resturantHash = item.find('a')['href']
            resturantLink = rootSite + resturantHash
            listOfLinks.append(resturantLink)

            #redefine for each link
            response = requests.get(resturantLink)
            soup = BeautifulSoup(response.text, 'html.parser')
            divMenuContainer = soup.find(class_='container').find(class_='row')
            divTopContainer = soup.find(class_='content-wrapper').find(class_='row')
            divStandardHours = divTopContainer.select('.location__details')[0]
            divDescription = divTopContainer.select('.location__details')[1]

            # Status
            # status = divStandardHours.select_one("span[class*=locationstatus]").get_text()
            status = "Closed"

            # Page Title & Menu
            pageTitle = divMenuContainer.find(class_='page-title').get_text()
            menuHash = divMenuContainer.find('a')['href']
            menuLink = rootSite + menuHash

            #Standard Hours Panel
            dayOfWeek = divStandardHours.select('.location__day')
            timeOfDay = divStandardHours.select('.location__times')

            #Description paragraph
            description = divDescription.find('p').get_text()
            description = str(description).replace("b'","")
            description = str(description).replace(u'\xa0',u'')

            #Output
            print(pageTitle) #confirm the resturant completed
            for item in dayOfWeek:
                weekDays.append(item.get_text())
            for item in timeOfDay:
                times.append(item.get_text())
            idCounter = idCounter + 1
            csv_writer.writerow([str(idCounter),pageTitle,status,menuLink,str(weekDays),str(times),description,""])
            weekDays.clear()
            times.clear()
        except:
            pass
            weekDays.clear()
            times.clear()
            
    # the market place page scrape
    for item in listOfTiles2:
        try:
            resturantTile = item.select('.card-block')
            resturantHash = item.find('a')['href']
            resturantLink = rootSite + resturantHash
            listOfLinks.append(resturantLink)

            #redefine for each link
            response = requests.get(resturantLink)
            soup = BeautifulSoup(response.text, 'html.parser')
            divMenuContainer = soup.find(class_='container').find(class_='row')
            divTopContainer = soup.find(class_='content-wrapper').find(class_='row')
            divStandardHours = divTopContainer.select('.location__details')[0]
            divDescription = divTopContainer.select('.location__details')[1]

            #Page Title & Menu
            pageTitle = divMenuContainer.find(class_='page-title').get_text()
            menuHash = divMenuContainer.find('a')['href']
            menuLink = rootSite + menuHash

            #Standard Hours Panel
            dayOfWeek = divStandardHours.select('.location__day')
            timeOfDay = divStandardHours.select('.location__times')

            #Description paragraph
            description = divDescription.find('p').get_text()
            description = str(description).replace("b'","")
            description = str(description).replace(u'\xa0',u'')

            #Output
            print(pageTitle)
            for item in dayOfWeek:
                weekDays.append(item.get_text())
            for item in timeOfDay:
                times.append(item.get_text())
            idCounter = idCounter + 1
            csv_writer.writerow([str(idCounter),pageTitle,status,menuLink,str(weekDays),str(times),description,""])
            weekDays.clear()
            times.clear()
        except:
            print("This site did not work: " + rootMarketplaceSite + resturantHash)
            csv_writer.writerow(["","","","","","","",resturantLink])
            weekDays.clear()
            times.clear()


# creates a json file for firebase from generated csv above
csvresturantInfo = open('resturantInfo.csv', 'r')
jsonresturantInfo = open('resturantInfo.json', 'w')
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
