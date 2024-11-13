import streamlit as st
import pandas as pd
import ast
import requests
from PIL import Image
from io import BytesIO

# Custom CSS to remove space at the top of the main content and sidebar
st.markdown("""
    <style>
    /* Remove top padding in the main content */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 1rem;
    }
    /* Remove header space */
    header, .toolbar {
        display: none;
    }
    /* Remove top padding in the sidebar */
    section[data-testid="stSidebar"] .css-ng1t4o {
        padding-top: 0rem;
        padding-bottom: 1rem;
    }
    /* Remove top margin in the sidebar */
    section[data-testid="stSidebar"] .css-1d391kg {
        margin-top: 0rem;
        margin-bottom: 0rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Your OMDb API key
AK = "86760ae5"

# Load your dataframe
df = pd.read_csv('merged_df.zip', compression = "zip")

# Convert lists
list_columns = ['available_languages', 'genres', 'cast', 'directors']
for col in list_columns:
    df[col] = df[col].apply(ast.literal_eval)

# Function to get movie poster
@st.cache_data(show_spinner=False)
def get_movie_poster(imdb_id, api_key):
    # OMDb API endpoint
    url = f'http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}'

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
        print('Poster not found for this IMDb ID.')
        return None

st.sidebar.header('Select Your Preferences')

# Available Languages
available_languages = sorted(df['available_languages'].explode().unique().tolist())
selected_languages = st.sidebar.multiselect('Available Languages:', available_languages)

# Runtime range
min_runtime = int(df['runtimeMinutes'].min())
max_runtime = int(df['runtimeMinutes'].max())
selected_runtime_range = st.sidebar.slider('Runtime (Minutes):', min_runtime, \
                                    max_runtime, (min_runtime, max_runtime))

# Release date
min_year = int(df['startYear'].min())
max_year = int(df['startYear'].max())
selected_year_range = st.sidebar.slider('Release Year Range:', min_year, \
                                        max_year, (min_year, max_year))

# Genres
available_genres = sorted(df['genres'].explode().unique().tolist())
selected_genres = st.sidebar.multiselect('Genres:', available_genres)

# Cast
selected_cast_input = st.sidebar.text_input('Cast (comma-separated):')
selected_cast = [x.strip() for x in selected_cast_input.split(',')] if \
                                                    selected_cast_input else []

# Directors
selected_directors_input = st.sidebar.text_input('Directors (comma-separated):')
selected_directors = [x.strip() for x in selected_directors_input.split(',')]  \
                                            if selected_directors_input else []

# Adult content
selected_isAdult = st.sidebar.checkbox('Include Adult Movies')

# Filter data based on preferences
filtered_df = df.copy()

if selected_languages:
    filtered_df = \
    filtered_df[filtered_df['available_languages'].apply(lambda x: \
                all(lang in x for lang in selected_languages))]

if not selected_isAdult:
    filtered_df = filtered_df[filtered_df['isAdult'] == 0]

filtered_df = filtered_df[
    (filtered_df['startYear'] >= selected_year_range[0]) & 
    (filtered_df['startYear'] <= selected_year_range[1])
]

filtered_df = filtered_df[
    (filtered_df['runtimeMinutes'] >= selected_runtime_range[0]) & 
    (filtered_df['runtimeMinutes'] <= selected_runtime_range[1])
]

if selected_genres:
    filtered_df = \
    filtered_df[filtered_df['genres'].apply(lambda x: \
                all(genre in x for genre in selected_genres))]

if selected_cast:
    filtered_df = \
    filtered_df[filtered_df['cast'].apply(lambda x: \
                all(cast_member in x for cast_member in selected_cast))]

if selected_directors:
    filtered_df = \
    filtered_df[filtered_df['directors'].apply(lambda x: \
                all(director in x for director in selected_directors))]

# Sort based on rating
filtered_df = filtered_df.sort_values(by='weighted_rating', ascending=False)

# Initialize session state
if 'recommendation_index' not in st.session_state: # keep track of what we 
                                                   # recommended so far
    st.session_state.recommendation_index = 0

# Recommendation display
if len(filtered_df) == 0:
    st.write('No movies found with the selected filters.')
else:
    current_index = st.session_state.recommendation_index
    if current_index < len(filtered_df):
        movie = filtered_df.iloc[current_index]
        st.write('**Recommended Movie:**')

        # Fetch the movie poster
        imdb_id = movie['tconst']
        poster = get_movie_poster(imdb_id, AK)

        # Create two columns
        col1, col2 = st.columns([1, 3])  # Adjust the ratio as needed

        # Display poster and button in the first column
        with col1:
            if poster:
                st.image(poster, use_container_width=True)
            else:
                st.write("Poster not available :(")

            # Add some spacing if needed
            st.write('')  # Adds a blank line for spacing

            # Create sub-columns within col1 to center the button
            sub_col1, sub_col2, sub_col3 = st.columns([1, 2, 1])

            with sub_col2:
                # Center the button in the middle sub-column
                if st.button('Next'):
                    if st.session_state.recommendation_index + 1 < len(filtered_df):
                        st.session_state.recommendation_index += 1
                        st.rerun()
                    else:
                        st.write('No more results')

        # Display movie details in the second column
        with col2:
            st.write(f"**Title:** {movie['title']}")
            st.write(f"**Rating:** {movie['weighted_rating']}")
            st.write(f"**Runtime:** {movie['runtimeMinutes']} minutes")
            st.write(f"**Genres:** {', '.join(sorted(movie['genres']))}")
            st.write(f"**Cast:** {', '.join(sorted(movie['cast']))}")
            st.write(f"**Directors:** {', '.join(sorted(movie['directors']))}")
            st.write(f"**Year:** {movie['startYear']}")
            st.write(f"**Languages:** {', '.join(sorted(movie['available_languages']))}")
            st.write(f"**Adult Content:** {'Yes' if movie['isAdult'] == 1 else 'No'}")
    else:
        st.write('No more recommendations.')