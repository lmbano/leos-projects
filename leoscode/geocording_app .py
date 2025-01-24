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
st.title("Geocoding and Distance Calculation App")
st.write("Upload the required files and enter the necessary details to proceed.")

uploaded_txt_file = st.file_uploader("Upload the MWI097.txt file", type=["txt"])
uploaded_xlsx_file = st.file_uploader("Upload the sub-saharan_health_facilities.xlsx file", type=["xlsx"])

if uploaded_txt_file is not None:
    st.write("**Uploaded MWI097.txt File Content:**")
    data = uploaded_txt_file.read().decode('utf-8').splitlines()
    data = [line.strip().replace("'", "").replace(",", "").replace("[", "").replace("]", "") for line in data]
    df_locations = pd.DataFrame(data, columns=['location'])
    st.dataframe(df_locations)

if uploaded_xlsx_file is not None:
    st.write("**Uploaded sub-saharan_health_facilities.xlsx File Content:**")
    df_sshf = pd.read_excel(uploaded_xlsx_file)
    st.dataframe(df_sshf)

if uploaded_txt_file is not None and uploaded_xlsx_file is not None:
    # User inputs
    country = st.text_input("Enter Country Name: ")
    country_code = st.text_input("Enter the Country Code (e.g., ZW): ")

    if country and country_code:
        df_sshf = df_sshf.rename(columns={'Facility_n': 'location'})

        st.write("**Filtered Health Facilities Data for Selected Country:**")
        df_filtered_country = df_sshf[df_sshf['Country'] == country]
        #df = pd.concat([df_locations, df_filtered_country], axis=1)
        st.dataframe(df_filtered_country)

        # Geocoding setup
        API_KEY = 'AIzaSyBFndo2dJfVM6v2-4cs4ZVmOQLSXuhdLRg'
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

        # Sidebar for API selection
        st.sidebar.title("Choose Geocoding APIs")
        use_hdx = st.sidebar.checkbox("HDX", value=True)
        use_google_maps = st.sidebar.checkbox("Google Maps", value=True)
        use_arcgis = st.sidebar.checkbox("ArcGIS", value=True)
        use_nominatim = st.sidebar.checkbox("OpenStreetMap (Nominatim)", value=True)

        # Geocode using selected APIs
        if use_hdx:
            st.write("**Geocodes from HDX :**")
            df = pd.merge(df_locations, df_filtered_country, on='location', how='inner')
            st.dataframe(df)
           
        if use_google_maps:
            st.write("**Geocoding with Google Maps:**")
            locations = df_locations['location']
            results = [geocode_location(loc, country) for loc in locations]
            df_geocoded = pd.DataFrame(results)
            df = pd.concat([df, df_geocoded], axis=1)
            st.dataframe(df)

        # ArcGIS Geocoding
        if use_arcgis:
            ARCGIS_API_KEY = API_KEY = 'AAPTxy8BH1VEsoebNVZXo8HurM2a9zHZgf3Ek17nTpJKAMr9E49cYAVEZcH0HOvxP3LdkwSWd757I8M_nKp-xgS39rHX1UuGiLWIHCxvRKZBHuaiHS11T9ANfivsw-WqmIjrVxz_oF03x83ZXVu68dAs5FrVIcnp0asK1Ps6dXX_kX1gh0ZX51yaJL8096TvxaDCBYoR-n6L5WcK_2EInDUd-BEtQixmMpWh7KjfC0xSlRU.AT1_PynuEsI5'


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

            st.write("**Geocoding with ArcGIS:**")
            arcgis_data = [arcgis_geocode(location, country_code) for location in df['location']]
            df_arcgis = pd.DataFrame(arcgis_data)
            df = pd.concat([df, df_arcgis], axis=1)
            st.dataframe(df)

        # Nominatim geocoding
        if use_nominatim:
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

            st.write("**Geocoding with OpenStreetMap (Nominatim):**")
            df_nominatim = df[['location']].copy()
            df_nominatim[['OS_Map_Latitude', 'OS_Map_Longitude']] = df_nominatim['location'].apply(nominatim_geocode).apply(pd.Series)
            df = pd.merge(df, df_nominatim, on='location', how='inner')
            st.dataframe(df)

        # Dealing with NaN and None Values
        df = df.fillna(0)

        # Calculate distances using Haversine formula
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            return round(distance, 3)
        
        distances = []
        for index, row in df.iterrows():
            lat1, lon1, lat2, lon2 = row['Latitude'], row['Longitude'], row['ArcGIS_Latitude'], row['ArcGIS_Longitude']
            lat3, lon3 = row['OS_Map_Latitude'], row['OS_Map_Longitude']
            lat4, lon4 = row['lat'], row['long']
            dist1 = haversine(lat1, lon1, lat2, lon2)
            dist2 = haversine(lat1, lon1, lat3, lon3)
            dist3 = haversine(lat2, lon2, lat3, lon3)
            dist4 = haversine(lat1, lon1, lat4, lon4)
            dist5 = haversine(lat3, lon3, lat4, lon4)
            dist6 = haversine(lat2, lon2, lat4, lon4)
            distances.append([dist1, dist2, dist3, dist4, dist5, dist6])
        df[['Diff_GMap_ArcGIS', 'Diff_GMap_OSMap', 'Diff_ArcGIS_OSMap', 'HDX_diffGMap', 'HDX_diff_OSMap', 'HDX_diff_ArcGIS']] = distances
        st.write("**Point Differences:**")
        st.dataframe(df[['location', 'Diff_GMap_ArcGIS', 'Diff_GMap_OSMap', 'Diff_ArcGIS_OSMap', 'HDX_diffGMap', 'HDX_diff_OSMap', 'HDX_diff_ArcGIS']])

        # Map visualization
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

                st_folium(m, width=800, height=600)
            else:
                st.warning(f"No data found for location: {location_name}")
else:
    st.warning("Please upload both files to proceed.")