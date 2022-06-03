#IMPORTING LIBRARY
import requests
import json
import pandas as pd
import time
import keys
from pymongo import MongoClient
import folium # https://python-visualization.github.io/folium/modules.html#module-folium.features
from html2image import Html2Image
import tweepy

# Login into twitter
#auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret) auth.set_access_token(keys.access_token, keys.access_token_secret) api = tweepy.API(auth)  

# load planes to search for 
planes_df = pd.read_csv('planes.csv')
planes_df['icao24'] = planes_df['icao24'].astype(str)

# I want to find each plane's update and use the coordinates to draw a line between them with folium
for i in planes_df['icao24']:
    # init a new map for this plane
    usmap = folium.Map(location=[39.8283, -98.5795], 
                   zoom_start=4, detect_retina=True,
                   tiles='Stamen Toner')
    
    locations = [] # container for the coordinates to draw a line
    query2 = db.flights.find({},{'icao24':i, 'lat':1, 'long':1,'on_ground':1,'time_position':1, 'callsign':1}) # get relevant data from database
    query3 = db.flights.count_documents({'icao24':i}) # see how many records we have captured to know when to put a done marker down
    count = 0 # keep track of where we are
    
    for data in query2:
        # if the data matches i, add to list
        if data['icao24'] == i:
            # check if bad data
            if data['lat'] == 'No Data' or data['long'] =='No Data': 
                continue
            # check if within 48 hours
            if data['time_position'] < int(time.time()) and data['time_position'] > (int(time.time()) - 48 * 3600):
                # check if start or end of flight
                if data['on_ground'] == True and  count == 0: # Ideally, I'd catch both start and end, but not realistic with this API
                    folium.Marker(
                                location=[data['lat'], data['long']],
                                popup='On ground ' + data['callsign'] + str(datetime.datetime.fromtimestamp(data['time_position'])),
                                icon=folium.Icon(color='green',icon="plane",angle=0),
                                
                            ).add_to(usmap) 
                    locations.append([data['lat'],data['long']])
                elif( count == 0 ):
                    folium.Marker(
                                location=[data['lat'], data['long']],
                                popup= 'Start '+ data['callsign'] + data['icao24'] + str(datetime.datetime.fromtimestamp(data['time_position'])),
                                icon=folium.Icon(color='green',icon="plane",angle=90),
                            ).add_to(usmap)
                    locations.append([data['lat'],data['long']])
                # Check if end of flight
                elif(count == query3  or count == query3 -1 or (count == query3 -1 and data['on_ground'] == True)):  # Ideally, I'd catch both start and end, but not realistic with this API
                    folium.Marker(
                                location=[data['lat'], data['long']],
                                popup='End ' + data['callsign'] + str(datetime.datetime.fromtimestamp(data['time_position'])),
                                icon=folium.Icon(color='red',icon="plane",angle=270),
                            ).add_to(usmap)
                    locations.append([data['lat'],data['long']])
                    
                # I don't care about the else data, I just need the points for start and end of flight    
                #else:  
                    #locations.append([data['lat'],data['long']])
                count = count + 1
    if(len(locations) == 0 ): # Don't add to map if no coordinates found in database
        continue
    else:
        folium.features.ColorLine(locations,[0, 1, 2, 3],colormap=['b', 'g', 'y', 'r'],nb_steps=4,weight=10,opacity=1).add_to(usmap)    
    
    # Little side box put on map with callsign start start and duration ( I can't get the datetime )
    usmap.save('Mapof' + str(i)+'.html') # just going to use their registration number icao24
    usmap
    
    # Save an image of that map
    hti = Html2Image()
    if count != 0:
        with open('./Mapof' + str(i) + '.html') as f:
            hti.screenshot(f.read(), save_as='Mapof' + str(i) + '.png', size=(600 , 600))# works
    
    # build a tweet with the key data and image
    # Login into twitter
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    api = tweepy.API(auth)  
    

    count = 0 # reset the count for the next plane in the list
tweet = "Recent flight of " + data['callsign']
post_result = api.update_status(status=tweet)