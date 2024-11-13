import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO

# Assume you have loaded your data into df
df = pd.read_csv('/Users/ziyuefu/Desktop/CU_Fall24/Data viz/merged_df.csv')

# Data preprocessing: ensure 'genres' and 'directors' fields are in string format and handle NaN or null values
def safe_eval(value):
    """Safely handle eval() to avoid errors caused by illegal characters."""
    try:
        if isinstance(value, str):
            return ' '.join(eval(value)) if value else ''
        return ''
    except Exception as e:
        return ''  # Return an empty string if an error occurs

# Handle NaN and null values by filling them with appropriate default values
df['genres'] = df['genres'].fillna('').apply(safe_eval)
df['directors'] = df['directors'].fillna('').apply(safe_eval)

# Fill missing values in the rating column (if necessary)
df['weighted_rating'] = df['weighted_rating'].fillna(df['weighted_rating'].mean())

# OMDb API to get movie poster
API_KEY = "86760ae5"

def get_movie_poster(tconst, api_key):
    """
    Fetches the movie poster image for a given IMDb tconst using the OMDb API.
    """
    # OMDb API endpoint
    url = f'http://www.omdbapi.com/?i={tconst}&apikey={api_key}'

    # Send a GET request to the OMDb API
    response = requests.get(url)
    data = response.json()

    # Check if the response contains a poster URL
    if 'Poster' in data and data['Poster'] != 'N/A':
        poster_url = data['Poster']
        # Fetch the poster image
        poster_response = requests.get(poster_url)
        poster_image = Image.open(BytesIO(poster_response.content))
        return poster_image
    else:
        return None

# Streamlit application configuration
st.set_page_config(page_title="Movie Matchmaker", page_icon="🎬")

# Custom CSS styling
st.markdown("""
    <style>
        /* Set button background color to red, and font color to white */
        .stButton>button {
            background-color: #F44336;  /* Red */
            color: white !important;
            border: none;
            border-radius: 5px;
        }

        /* Center the button and images */
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            text-align: center;
            padding: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Display the title
st.title("Welcome to Movie Matchmaker!")

# Left-side filter panel
st.sidebar.header("Filter Movies")

# Genres filter
genres = df['genres'].str.split(' ').explode().unique()
selected_genres = st.sidebar.multiselect("Select Genres", genres)

# Rating filter
min_rating = df['weighted_rating'].min()
max_rating = df['weighted_rating'].max()
selected_rating = st.sidebar.slider("Select Rating", min_rating, max_rating, (min_rating, max_rating))

# Director filter
directors = df['directors'].str.split(' ').explode().unique()
selected_directors = st.sidebar.multiselect("Select Director", directors)

# isAdult filter
# Map 1 to 'Adult', and 0 to 'Not Adult'
adult_status = {1: 'Adult', 0: 'Not Adult'}
selected_adult = st.sidebar.selectbox("Select Adult Status", ['Any', 'Adult', 'Not Adult'])

# Apply filters to the dataframe
filtered_df = df.copy()

# Filter according to the selected filter options
if selected_genres:
    filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: any(genre in x for genre in selected_genres))]

if selected_rating:
    filtered_df = filtered_df[(filtered_df['weighted_rating'] >= selected_rating[0]) & 
                               (filtered_df['weighted_rating'] <= selected_rating[1])]

if selected_directors:
    filtered_df = filtered_df[filtered_df['directors'].apply(lambda x: any(director in x for director in selected_directors))]

if selected_adult != 'Any':
    # Filter the isAdult column, mapping 1 to 'Adult' and 0 to 'Not Adult'
    is_adult_filter = 1 if selected_adult == 'Adult' else 0
    filtered_df = filtered_df[filtered_df['isAdult'] == is_adult_filter]

# Initialize the session state for the movie if not already set
if 'current_movie' not in st.session_state or 'poster' not in st.session_state:
    # Get a random movie from the filtered data
    st.session_state.current_movie = filtered_df.sample(1).iloc[0]
    # Get the movie poster from OMDb API
    tconst = st.session_state.current_movie['tconst']
    st.session_state.poster = get_movie_poster(tconst, API_KEY)

# Display movie recommendations
st.header("Recommended Movies")

# Get current movie
current_movie = st.session_state.current_movie

# Get IMDb tconst
tconst = current_movie['tconst']

# Get movie poster
poster = st.session_state.poster

# Display poster and movie details
with st.container():
    # Display the movie poster, centered
    st.markdown('<div class="center">', unsafe_allow_html=True)
    if poster:
        st.image(poster, caption=f"Poster of {current_movie['title']}", use_container_width=True)
    else:
        st.write("No poster available.")
    
    # Display movie details
    st.markdown(f"**Title:** {current_movie['title']}")
    st.markdown(f"**Genres:** {current_movie['genres']}")
    st.markdown(f"**Rating:** {current_movie['weighted_rating']}")
    st.markdown(f"**Director:** {current_movie['directors']}")
    st.markdown(f"**Release Year:** {current_movie['startYear']}")
    st.markdown(f"**Language:** {current_movie['available_languages']}")
    
    # Use the movie's tconst to ensure the button key is unique
    button_key = f"btn_{tconst}"
    if st.button("Don't like this one", key=button_key):
        # Randomly select a new movie
        st.session_state.current_movie = filtered_df.sample(1).iloc[0]
        tconst = st.session_state.current_movie['tconst']
        # Get the new movie poster
        st.session_state.poster = get_movie_poster(tconst, API_KEY)
        # Re-render the current page
        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# If no movies match the filters, display a message
if filtered_df.empty:
    st.write("No movies match your filters.")
