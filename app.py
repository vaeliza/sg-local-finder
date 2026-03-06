import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from geopy.distance import geodesic

from supabase_client import get_supabase_client
from google_places import get_place_details

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="🇸🇬 SG Local Finder", layout="wide")
st.title("🇸🇬 SG Local Finder")
st.write("Discover Singapore's independent businesses.")

# -----------------------
# USER INPUTS
# -----------------------
search_location = st.text_input("Enter a location to search nearby (e.g., Orchard, Singapore):")
search_radius_km = st.slider("Search radius (km)", min_value=1, max_value=10, value=5)

search_text = st.text_input("Search businesses by name")
category_filter = st.selectbox(
    "Filter by category",
    ["All", "Food", "Fashion", "Education", "Health"]
)

# -----------------------
# GEOCODE USER LOCATION
# -----------------------
user_lat, user_lng = None, None
if search_location:
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": search_location,
        "key": st.secrets["GOOGLE_API_KEY"]
    }
    resp = requests.get(geocode_url, params=params).json()
    if resp.get("results"):
        user_lat = resp["results"][0]["geometry"]["location"]["lat"]
        user_lng = resp["results"][0]["geometry"]["location"]["lng"]

# -----------------------
# CONNECT TO SUPABASE
# -----------------------
supabase = get_supabase_client()
data = supabase.table("businesses").select("*").execute()
df = pd.DataFrame(data.data)

# -----------------------
# SEARCH + CATEGORY FILTER
# -----------------------
if search_text:
    df = df[df["name"].str.contains(search_text, case=False)]
if category_filter != "All":
    df = df[df["category"] == category_filter]

# -----------------------
# SUPPORT LOCAL SCORE FUNCTION
# -----------------------
def calculate_support_score(rating, review_count, has_website):
    score = 0
    if rating:
        score += rating * 15
    if review_count:
        score += min(review_count / 10, 30)
    if has_website:
        score += 10
    return round(score)

# -----------------------
# BUILD BUSINESS LIST
# -----------------------
business_list = []
for _, row in df.iterrows():
    details = get_place_details(row["place_id"])
    result = details.get("result", {})

    rating = result.get("rating", 0)
    review_count = result.get("user_ratings_total", 0)
    has_website = bool(row.get("website"))

    score = calculate_support_score(rating, review_count, has_website)
    lat = result.get("geometry", {}).get("location", {}).get("lat")
    lng = result.get("geometry", {}).get("location", {}).get("lng")

    business_list.append({
        "row": row,
        "rating": rating,
        "reviews": review_count,
        "score": score,
        "details": result,
        "lat": lat,
        "lng": lng
    })

# -----------------------
# FILTER BY LOCATION
# -----------------------
filtered_businesses = []
for item in business_list:
    b_lat = item.get("lat")
    b_lng = item.get("lng")
    if user_lat and user_lng and b_lat and b_lng:
        distance_km = geodesic((user_lat, user_lng), (b_lat, b_lng)).km
        if distance_km <= search_radius_km:
            filtered_businesses.append(item)
    else:
        filtered_businesses.append(item)

# -----------------------
# SORT BY SUPPORT LOCAL SCORE
# -----------------------
filtered_businesses = sorted(filtered_businesses, key=lambda x: x["score"], reverse=True)

# -----------------------
# DISPLAY BUSINESS CARDS
# -----------------------
for item in filtered_businesses:
    row = item["row"]
    rating = item.get("rating", 0)
    reviews = item.get("reviews", 0)
    score = item.get("score", 0)
    result = item.get("details", {})

    # 1️⃣ Photo URL
    photo_url = "https://via.placeholder.com/300x200?text=No+Image"
    photos = result.get("photos")
    if photos and len(photos) > 0:
        photo_ref = photos[0].get("photo_reference")
        if photo_ref:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={st.secrets['GOOGLE_API_KEY']}"

    # 2️⃣ Top 2 reviews
    top_reviews = ""
    if "reviews" in result and len(result["reviews"]) > 0:
        for review in result["reviews"][:2]:
            author = review.get("author_name", "Anonymous")
            text = review.get("text", "")
            top_reviews += f"<b>{author}:</b> {text}<br>"

    # 3️⃣ Google Maps link
    maps_url = f"https://www.google.com/maps/search/?api=1&query={quote(row['name'])}&query_place_id={row['place_id']}"

    # 4️⃣ Bootstrap-style responsive card
    card_html = f"""
    <style>
        @media(max-width:768px) {{
            .card-container {{
                flex-direction: column !important;
            }}
            .card-image {{
                width:100% !important;
                height:auto !important;
            }}
        }}
    </style>
    <div class="card-container" style="display:flex; flex-direction:row; border:1px solid #ddd; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); margin-bottom:20px; overflow:hidden;">
        <div class="card-image" style="flex:1 0 200px;">
            <img src="{photo_url}" style="width:100%; height:100%; object-fit:cover;">
        </div>
        <div class="card-info" style="flex:2; padding:15px;">
            <h3 style="margin:0;">{row.get('name','Unnamed Business')}</h3>
            <p>{row.get('description','No description available')}</p>
            <p><b>Category:</b> {row.get('category','N/A')}</p>
            {"<p>🌐 <a href='"+row.get('website')+"' target='_blank'>Website</a></p>" if row.get('website') else ""}
            <p>⭐ Rating: {rating} | 🗣 Reviews: {reviews} | 🏆 Support Local Score: {score}</p>
            {("<p><b>Top Reviews:</b><br>"+top_reviews+"</p>") if top_reviews else ""}
            <p>📍 <a href="{maps_url}" target="_blank">View on Google Maps</a></p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
