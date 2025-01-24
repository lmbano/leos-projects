'''
pip install streamlit geopy pandas folium openpyxl

pip install streamlit-folium

pip install fuzzywuzzy

pip install streamlit pandas folium streamlit-folium geopy fuzzywuzzy requests openpyxl

'''

# Streamlit app with features from the provided code

# Streamlit app with file upload functionality

import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import GoogleV3, Nominatim
from fuzzywuzzy import process
import requests
import math

# File upload prompts
uploaded_txt_file = st.file_uploader("Upload the MWI097.txt file", type=["txt"])
uploaded_xlsx_file = st.file_uploader("Upload the sub-saharan_health_facilities.xlsx file", type=["xlsx"])

if uploaded_txt_file is not None and uploaded_xlsx_file is not None:
    # Read the text file
    data = uploaded_txt_file.read().decode('utf-8').splitlines()

    # Clean the data
    data = [line.strip().replace("'", "").replace(",", "").replace("[", "").replace("]", "") for line in data]

    # Create the DataFrame
    df_locations = pd.DataFrame(data, columns=['location'])

    # Streamlit user inputs
    country = st.text_input("Enter Country Name: ")
    country_code = st.text_input("Enter the Country Code (e.g., ZW): ")

    # Importing sub-sahara_health_facilities
    df_sshf = pd.read_excel(uploaded_xlsx_file)
    df_sshf = df_sshf.rename(columns={'Facility_n': 'location'})

    # Filtering country health facilities
    df_filtered_country = df_sshf[df_sshf['Country'] == country]

    # Geocoding setup
    API_KEY ='AIzaSyBFndo2dJfVM6v2-4cs4ZVmOQLSXuhdLRg'
    geolocator = GoogleV3(api_key=API_KEY)

    def create_variations(location):
        variations = [
            location,
            location.replace('Center', 'Centre'),
            location.replace('center', 'centre'),
            location.replace('Ctr', 'Centre'),
            location.replace('ctr', 'centre'),
            location.replace('Centre', 'Center'),
            location.replace('centre', 'center'),
            location.replace('Ctr', 'Center'),
            location.replace('ctr', 'center')
        ]
        return variations

    def geocode_location(location, country):
        try:
            location_variations = create_variations(location)
            geocode_result = None

            for variation in location_variations:
                query = f'{variation}, {country}'
                geocode_result = geolocator.geocode(query)
                if geocode_result:
                    break
            
            if geocode_result:
                return {
                    'Formatted Address': geocode_result.address,
                    'Location Type': geocode_result.raw.get('geometry', {}).get('location_type', ''),
                    'Latitude': geocode_result.latitude,
                    'Longitude': geocode_result.longitude
                }
            else:
                return {
                    'Formatted Address': None,
                    'Location Type': None,
                    'Latitude': None,
                    'Longitude': None
                }
        except Exception as e:
            st.error(f"Error geocoding {location}: {e}")
            return {
                'Formatted Address': None,
                'Location Type': None,
                'Latitude': None,
                'Longitude': None
            }

    locations = df_locations['location']
    results = [geocode_location(loc, country) for loc in locations]
    df_geocoded = pd.DataFrame(results)

    # Concatenate with original DataFrame
    df = pd.concat([df_locations, df_geocoded], axis=1)

    # ArcGIS Geocoding
    ARCGIS_API_KEY = 'AAPTxy8BH1VEsoebNVZXo8HurM2a9zHZgf3Ek17nTpJKAMr9E49cYAVEZcH0HOvxP3LdkwSWd757I8M_nKp-xgS39rHX1UuGiLWIHCxvRKZBHuaiHS11T9ANfivsw-WqmIjrVxz_oF03x83ZXVu68dAs5FrVIcnp0asK1Ps6dXX_kX1gh0ZX51yaJL8096TvxaDCBYoR-n6L5WcK_2EInDUd-BEtQixmMpWh7KjfC0xSlRU.AT1_PynuEsI5'


    def arcgis_geocode(location, country_code):
        try:
            params = {
                'address': location,
                'countryCode': country_code,
                'maxLocations': 1,
                'fuzziness': 0.5,
                'outFields': 'address',
                'f': 'json'
            }
            headers = {'Referer': 'http://localhost:8501'}
            response = requests.get(f'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates', params=params, headers=headers)
            data = response.json()
            if data['candidates']:
                candidate = data['candidates'][0]
                return {
                    'ArcGIS_Address': candidate['address'],
                    'ArcGIS_Latitude': candidate['location']['y'],
                    'ArcGIS_Longitude': candidate['location']['x']
                }
            else:
                return {
                    'ArcGIS_Address': None,
                    'ArcGIS_Latitude': None,
                    'ArcGIS_Longitude': None
                }
        except Exception as e:
            st.error(f"Error geocoding {location}: {e}")
            return {
                'ArcGIS_Address': None,
                'ArcGIS_Latitude': None,
                'ArcGIS_Longitude': None
            }

    arcgis_data = [arcgis_geocode(location, country_code) for location in df['location']]
    df_arcgis = pd.DataFrame(arcgis_data)
    df = pd.concat([df, df_arcgis], axis=1)

    # Nominatim geocoding
    nominatim_geolocator = Nominatim(user_agent="my_app")

    def nominatim_geocode(location):
        try:
            location_variations = create_variations(location)
            location_result = None
            
            for variation in location_variations:
                query = f"{variation}, {country}"
                location = nominatim_geolocator.geocode(query, timeout=10)
                if location:
                    location_result = location
                    break

            if location_result:
                return (location_result.latitude, location_result.longitude)
            else:
                return (None, None)
        except GeocoderTimedOut:
            return (None, None)

    df_nominatim = df[['location']].copy()
    df_nominatim[['OS_Map_Latitude', 'OS_Map_Longitude']] = df_nominatim['location'].apply(nominatim_geocode).apply(pd.Series)
    df = pd.merge(df, df_nominatim, on='location', how='inner')

    # Dealing with NaN and None Values
    df = df.fillna(0)

    # Calculate distances using Haversine formula
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lat1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        return round(distance, 3)

    distances = []
    for index, row in df.iterrows():
        lat1, lon1, lat2, lon2 = row['Latitude'], row['Longitude'], row['ArcGIS_Latitude'], row['ArcGIS_Longitude']
        lat3, lon3 = row['OS_Map_Latitude'], row['OS_Map_Longitude']
        dist1 = haversine(lat1, lon1, lat2, lon2)
        dist2 = haversine(lat1, lon1, lat3, lon3)
        dist3 = haversine(lat2, lon2, lat3, lon3)
        distances.append([dist1, dist2, dist3])

    df[['Diff_GMap_ArcGIS', 'Diff_GMap_OSMap', 'Diff_ArcGIS_OSMap']] = distances

    # Map visualization
    st.title("Geocoding and Distance Calculation")

    location_name = st.text_input("Enter location name to visualize on map:")
    if location_name:
        location_data = df[df['location'] == location_name]

        if not location_data.empty:
            m = folium.Map(location=[location_data['Latitude'].iloc[0], location_data['Longitude'].iloc[0]], zoom_start=15)

            folium.Marker(
                location=[location_data['Latitude'].iloc[0], location_data['Longitude'].iloc[0]],
                tooltip="Click me!",
                popup="Google Maps Point",
                icon=folium.Icon(color="blue")
            ).add_to(m)

            folium.Marker(
                location=[location_data['ArcGIS_Latitude'].iloc[0], location_data['ArcGIS_Longitude'].iloc[0]],
                tooltip="Click me!",
                popup="ArcGIS Point",
                icon=folium.Icon(color="red")
            ).add_to(m)

            folium.Marker(
                location=[location_data['OS_Map_Latitude'].iloc[0], location_data['OS_Map_Longitude'].iloc[0]],
                tooltip="Click me!",
                popup="OpenStreetMap Point",
                icon=folium.Icon(color="beige")
            ).add_to(m)

            st_folium(m, width=700, height=500)

            st.write(f"The distance between Google Maps and ArcGIS points is: {location_data['Diff_GMap_ArcGIS'].iloc[0]} km")
            st.write(f"The distance between Google Maps and OpenStreetMap points is: {location_data['Diff_GMap_OSMap'].iloc[0]} km")
            st.write(f"The distance between ArcGIS and OpenStreetMap points is: {location_data['Diff_ArcGIS_OSMap'].iloc[0]} km")
        else:
            st.error("Location not found in the dataset.")
else:
    st.warning("Please upload both the required files to proceed.")
