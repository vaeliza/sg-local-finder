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

st.write(df)

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

    with st.container():

        st.subheader(row["name"])

        st.write(row["description"])

        st.write(f"Category: {row['category']}")

        st.write(f"🌐 Website: {row['website']}")

        st.write(f"⭐ Rating: {rating}")

        st.write(f"🗣 Reviews: {reviews}")

        st.write(f"🏆 Support Local Score: {score}")

        if "opening_hours" in result:

            st.write("Opening Hours:")

            for hour in result["opening_hours"]["weekday_text"]:
                st.write(hour)

        if "reviews" in result:

            st.write("Customer Reviews:")

            for review in result["reviews"][:2]:
                st.write(f"{review['author_name']}: {review['text']}")

        st.divider()
