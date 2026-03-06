import streamlit as st
import pandas as pd

from supabase_client import get_supabase_client
from google_places import get_place_details

st.set_page_config(page_title="SG Local Finder", layout="wide")

st.title("🇸🇬 SG Local Finder")
st.write("Discover Singapore's independent businesses.")

# Connect to Supabase
supabase = get_supabase_client()

data = supabase.table("businesses").select("*").execute()

df = pd.DataFrame(data.data)


# -----------------------
# SEARCH + FILTER
# -----------------------

search = st.text_input("Search businesses")

category_filter = st.selectbox(
    "Filter by category",
    ["All","Food","Fashion","Education","Health"]
)

if search:
    df = df[df["name"].str.contains(search, case=False)]

if category_filter != "All":
    df = df[df["category"] == category_filter]

# -----------------------
# SUPPORT LOCAL SCORE
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
# BUSINESS LIST
# -----------------------

business_list = []

for _, row in df.iterrows():

    details = get_place_details(row["place_id"])

    result = details.get("result", {})

    rating = result.get("rating", 0)
    review_count = result.get("user_ratings_total", 0)

    has_website = row["website"] != ""

    score = calculate_support_score(rating, review_count, has_website)

    business_list.append({
        "row": row,
        "rating": rating,
        "reviews": review_count,
        "score": score,
        "details": result
    })

# Sort by Support Local Score
business_list = sorted(business_list, key=lambda x: x["score"], reverse=True)

# -----------------------
# DISPLAY BUSINESSES
# -----------------------

for item in business_list:
    row = item["row"]
    rating = item["rating"]
    reviews = item["reviews"]
    score = item["score"]
    result = item["details"]

    # Get photo URL from Google if available
    photo_url = ""
    if "photos" in result:
        photo_ref = result["photos"][0]["photo_reference"]
        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={st.secrets['GOOGLE_API_KEY']}"

    st.markdown(
    f"""
    <div style="
        display: flex; 
        flex-direction: row; 
        align-items: flex-start; 
        padding: 15px; 
        border: 1px solid #ddd; 
        border-radius: 10px; 
        margin-bottom: 15px; 
        background-color: #f9f9f9;">
        
        <img src="{photo_url}" width="150" height="150" style="border-radius:10px; margin-right:15px;">
        
        <div style="flex:1;">
            <h3>{row['name']}</h3>
            <p>{row['description']}</p>
            <p><b>Category:</b> {row['category']}</p>
            <p><b>Website:</b> <a href="{row['website']}" target="_blank">{row['website']}</a></p>
            <p>⭐ Rating: {rating} | 🗣 Reviews: {reviews} | 🏆 Support Local Score: {score}</p>
            {top_reviews}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

    
