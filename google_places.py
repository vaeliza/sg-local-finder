import requests
import streamlit as st

API_KEY = st.secrets["GOOGLE_API_KEY"]

def get_place_details(place_id):

    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
    "place_id": place_id,
    "key": API_KEY,
    "fields": "name,rating,user_ratings_total,opening_hours,photos,reviews,website"
}

    response = requests.get(url, params=params)

    return response.json()

details = get_place_details(row["place_id"])
result = details.get("result", {})
print(result.get("photos", "No photos found"))
