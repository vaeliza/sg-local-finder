
from supabase_client import get_supabase_client
from google_places import get_place_details

import geopy.distance

# User inputs a location (address)
search_location = st.text_input("Enter a location to search nearby (e.g., Orchard, Singapore):")
search_radius_km = st.slider("Search radius (km)", min_value=1, max_value=10, value=5)

import requests

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
from urllib.parse import quote

# Loop through all businesses
for item in business_list:
    row = item["row"]           # Row from Supabase
    rating = item.get("rating", 0)     # Average rating
    reviews = item.get("reviews", 0)   # Number of reviews
    score = item.get("score", 0)       # Support Local Score
    result = item.get("details", {})   # Google Places details

    # -----------------------
    # 1️⃣ Photo
    # -----------------------
    photo_url = "https://via.placeholder.com/150?text=No+Image"  # default
    if "photos" in result and len(result["photos"]) > 0:
        photo_ref = result["photos"][0].get("photo_reference")
        if photo_ref:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={st.secrets['GOOGLE_API_KEY']}"

    # -----------------------
    # 2️⃣ Top 2 reviews
    # -----------------------
    top_reviews = ""
    if "reviews" in result and len(result["reviews"]) > 0:
        for review in result["reviews"][:2]:
            author = review.get("author_name", "Anonymous")
            text = review.get("text", "")
            top_reviews += f"{author}: {text}\n\n"

    # -----------------------
    # 3️⃣ Google Maps link
    # -----------------------
    # Properly encode business name for URL
    maps_url = f"https://www.google.com/maps/search/?api=1&query={quote(row['name'])}&query_place_id={row['place_id']}"

    # -----------------------
    # 4️⃣ Layout: 2 columns (image | info)
    # -----------------------
    col1, col2 = st.columns([1, 3])

    with col1:
        st.image(photo_url, width=150)

    with col2:
        st.subheader(row.get("name", "Unnamed Business"))
        st.write(row.get("description", "No description available"))
        st.write(f"**Category:** {row.get('category', 'N/A')}")
        website = row.get("website", "")
        if website:
            st.markdown(f"🌐 [Website]({website})", unsafe_allow_html=True)
        st.write(f"⭐ Rating: {rating} | 🗣 Reviews: {reviews} | 🏆 Support Local Score: {score}")
        if top_reviews:
            st.write("**Top Reviews:**")
            st.write(top_reviews)
        st.markdown(f"📍 [View on Google Maps]({maps_url})", unsafe_allow_html=True)

    # Divider between cards
    st.markdown("---")

