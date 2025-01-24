import streamlit as st
import geopy
from geopy.geocoders import GoogleV3, Nominatim
import pandas as pd
import requests
import folium
from folium.plugins import MarkerCluster
import math
import pycountry

# Your Google Maps API key
API_KEY = 'AIzaSyBFndo2dJfVM6v2-4cs4ZVmOQLSXuhdLRg'

# Your ArcGIS Geocoding API key
ARCGIS_API_KEY = 'AAPTxy8BH1VEsoebNVZXo8HurM2a9zHZgf3Ek17nTpJKAMr9E49cYAVEZcH0HOvxP3LdkwSWd757I8M_nKp-xgS39rHX1UuGiLWIHCxvRKZBHuaiHS11T9ANfivsw-WqmIjrVxz_oF03x83ZXVu68dAs5FrVIcnp0asK1Ps6dXX_kX1gh0ZX51yaJL8096TvxaDCBYoR-n6L5WcK_2EInDUd-BEtQixmMpWh7KjfC0xSlRU.AT1_PynuEsI5'

# Create a geolocator object
geolocator = Nominatim(user_agent="my_app")

# Function to get country code using country name
def get_country_code(country_name):
    country = pycountry.countries.get(name=country_name)
    if country:
        return country.alpha_2
    else:
        return "Country not found"

# Function to geocode a location
def geocode_location(location, country_name):
    try:
        # Generate all variations of the location
        location_variations = create_variations(location)
        geocode_result = None

        # Try geocoding each variation
        for variation in location_variations:
            query = f'{variation}, {country_name}'
            geocode_result = geolocator.geocode(query)
            if geocode_result:
                break
        
        # Return the results if found
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
        print(f"Error geocoding {location}: {e}")
        return {
            'Formatted Address': None,
            'Location Type': None,
            'Latitude': None,
            'Longitude': None
        }

# Function to create variations of the location name
def create_variations(location):
    variations = []
    variations.append(location)
    variations.append(location.replace('Center', 'Centre'))
    variations.append(location.replace('center', 'centre'))
    variations.append(location.replace('Ctr', 'Centre'))
    variations.append(location.replace('ctr', 'centre'))
    variations.append(location.replace('Centre', 'Center'))
    variations.append(location.replace('centre', 'center'))
    variations.append(location.replace('Ctr', 'Center'))
    variations.append(location.replace('ctr', 'center'))
    return variations

# Function to calculate distances between coordinates
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on a sphere (like the Earth)
    based on their longitudes and latitudes.
    """
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    R = 6371  # Radius of the Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return round(distance, 3)  # Round the distance to 3 decimal places

# Streamlit app
def main():
    st.title("Geocoding and Distance Calculation App")

    # Get the country name from the user
    country_name = st.text_input("Enter Country Name: ")

    # Get the country code
    country_code = get_country_code(country_name)

    # Display the country code
    st.write(f"The country code for {country_name} is {country_code}")

    # Create a text area for the user to input locations
    locations = st.text_area("Enter locations (one per line):")

    # Split the locations into a list
    locations = [location.strip() for location in locations.split("\n") if location.strip()]

    # Geocode the locations
    geocoded_data = [geocode_location(location, country_name) for location in locations]

    # Create a DataFrame to store the results
    df = pd.DataFrame(geocoded_data)

    # Display the geocoded data
    st.write(df)

    # Calculate distances between coordinates
    distances = []
    for index, row in df.iterrows():
        lat1, lon1 = row['Latitude'], row['Longitude']
        lat2, lon2 = row['ArcGIS_Latitude'], row['ArcGIS_Longitude']
        lat3, lon3 = row['OS_Map_Latitude'], row['OS_Map_Longitude']
        dist1 = haversine(lat1, lon1, lat2, lon2)
        dist2 = haversine(lat1, lon1, lat3, lon3)
        dist3 = haversine(lat2, lon2, lat3, lon3)
        distances.append([dist1, dist2, dist3])

    # Add the distances to the DataFrame
    df[['Diff_GMap_ArcGIS', 'Diff_GMap_OSMap', 'Diff_ArcGIS_OSMap']] = distances

    # Display the updated DataFrame
    st.write(df)

    # Create a Folium map object
    m = folium.Map()

    # Add markers to the map
    for index, row in df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            tooltip="Google Map Point!",
            popup=f"{row['location']}: Google Map Point<br>Coordinates: {row['Latitude']}, {row['Longitude']}",
            icon=folium.Icon(color="blue"),
        ).add_to(m)

        folium.Marker(
            location=[row['ArcGIS_Latitude'], row['ArcGIS_Longitude']],
            tooltip="ArcGIS Point!",
            popup=f"{row['location']}: ArcGIS Point<br>Coordinates: {row['ArcGIS_Latitude']}, {row['ArcGIS_Longitude']}",
            icon=folium.Icon(color="red"),
        ).add_to(m)

        folium.Marker(
            location=[row['OS_Map_Latitude'], row['OS_Map_Longitude']],
            tooltip="OS_Map Point!",
            popup=f"{row['location']}: Open Street Map Point<br>Coordinates: {row['OS_Map_Latitude']}, {row['OS_Map_Longitude']}",
            icon=folium.Icon(color="beige"),
        ).add_to(m)

    # Display the map
    st_map = st_folium(m, width=725)

if __name__ == "__main__":
    main()