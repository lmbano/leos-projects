import streamlit as st
import pandas as pd
import numpy as np
import folium
from geopy.distance import geodesic

# Function to clean location names
def clean_location_name(name):
    name = name.strip().replace('[', '').replace(']', '').replace("'" ,"")
    return name

# Load MWI097.txt file
uploaded_file = st.file_uploader("Upload MWI097.txt file", type='txt')
if uploaded_file is not None:
    content = uploaded_file.read().decode('utf-8')
    content = content.replace('\n', ',')
    df = pd.DataFrame(content.split(','))

# Clean location names for dropdown
if 'df' in locals():
    cleaned_locations = df.squeeze().apply(clean_location_name)

# Load sub-saharan_health_facilities.xlsx file
uploaded_health_facilities_file = st.file_uploader("Upload sub-saharan_health_facilities.xlsx file", type='xlsx')
if uploaded_health_facilities_file is not None:
    health_facilities_df = pd.read_excel(uploaded_health_facilities_file)

# Sidebar - Select location for visualization
selected_location = st.sidebar.selectbox('Select a location for visualization', cleaned_locations if 'cleaned_locations' in locals() else [])

# Display selected location on the map
if 'df' in locals() and not df.empty and selected_location:
    st.write(f"Selected location: {selected_location}")
    
    # Your code to display the location on the map using Folium goes here

# Display DataFrames
if 'geocoded_google' in locals():
    st.subheader('Google Maps Geocoding Results')
    st.write(geocoded_google)

if 'geocoded_arcgis' in locals():
    st.subheader('ArcGIS Geocoding Results')
    st.write(geocoded_arcgis)

if 'geocoded_nominatim' in locals():
    st.subheader('Nominatim Geocoding Results')
    st.write(geocoded_nominatim)

if 'differences' in locals():
    st.subheader('Differences in Point Locations')
    st.write(differences)