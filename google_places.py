import requests
import streamlit as st

def get_place_details(place_id):
    """Fetch Google Place details for a given place_id"""
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"
    response = requests.get(url)
    return response.json()
