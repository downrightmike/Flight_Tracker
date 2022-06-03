#IMPORTING LIBRARY
import requests
import json
import pandas as pd
import time
import datetime
import keys
from pymongo import MongoClient


#Connect to database
atlas_client = MongoClient(keys.mongo_connection_string)
db = atlas_client.flight_test #collection of flight data

starttime = time.time() # for the loop
flight_df=pd.DataFrame() # init dataframe

#Logic to run and check for flights, allow run() until manually stopped
# problem, api doesn't allow history tracking, so if I don't catch it, I won't have that event

def run(flight_df): 
    # load planes to search for
    planes_df = pd.read_csv('planes.csv')
    planes_df['icao24'] = planes_df['icao24'].astype(str)
    for i in planes_df['icao24']:
        # get information for this specific plane using icao24 id
        url_data='https://opensky-network.org/api/states/all?icao24=' + i
        
        response=requests.get(url_data).json()

        #LOAD TO PANDAS DATAFRAME
        col_name=['icao24','callsign','origin_country','time_position','last_contact','long','lat','baro_altitude','on_ground','velocity',       
        'true_track','vertical_rate','sensors','geo_altitude','squawk','spi','position_source']
        flight_df=pd.DataFrame(response['states'])
        
        if(len(flight_df) == 0 ):
            #print("Df is empty") # if not inflight it will be empty
            continue # to the next entry in list
    
        flight_df=flight_df.loc[:,0:16]
        flight_df.columns=col_name
        flight_df=flight_df.fillna('No Data') #replace NAN with No Data
        flight_df.head()
        print('flight df count ' + str(len(flight_df.index)))
        
        if(len(flight_df.count()) > 0 ):
            db.flights.insert_many(flight_df.to_dict('records')) # puts entry with key:value into test_flight db table fligts   
            print('New record written ' + str(len(flight_df.index)))
            
        # End of run()
while True:
	run(flight_df)
    # other functions to do the rest
	time.sleep(60.0 - ((time.time() - starttime) % 60.0))