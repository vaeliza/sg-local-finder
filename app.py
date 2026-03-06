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

# Loop through all businesses
# Loop through all businesses
for item in business_list:
    row = item["row"]           # Row from Supabase
    rating = item["rating"]     # Average rating
    reviews = item["reviews"]   # Number of reviews
    score = item["score"]       # Support Local Score
    result = item["details"]    # Google Places details

    # Get business photo or fallback
    photo_url = ""
    if "photos" in result:
        photo_ref = result["photos"][0]["photo_reference"]
        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={st.secrets['GOOGLE_API_KEY']}"
    else:
        photo_url = "https://via.placeholder.com/150?text=No+Image"

    # Top 2 reviews
    top_reviews = ""
    if "reviews" in result:
        for review in result["reviews"][:2]:
            author = review.get("author_name", "Anonymous")
            text = review.get("text", "")
            top_reviews += f"{author}: {text}\n\n"

    # Construct Google Maps clickable link
    maps_url = f"https://www.google.com/maps/search/?api=1&query={row['name']}&query_place_id={row['place_id']}"

    # Layout: 2 columns (image | info)
    col1, col2 = st.columns([1, 3])

    with col1:
        st.image(photo_url, width=150)

    with col2:
        st.subheader(row["name"])
        st.write(row["description"])
        st.write(f"**Category:** {row['category']}")
        if row["website"]:
            st.write(f"🌐 [Website]({row['website']})")
        st.write(f"⭐ Rating: {rating} | 🗣 Reviews: {reviews} | 🏆 Support Local Score: {score}")
        if top_reviews:
            st.write("**Top Reviews:**")
            st.write(top_reviews)
        # Google Maps clickable link
        st.write(f"📍 [View on Google Maps]({maps_url})")

    # Divider between cards
    st.markdown("---")


