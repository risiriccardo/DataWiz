import streamlit as st
import requests
import pandas as pd
import ast
from PIL import Image
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

# Place CSS to center the 'Proceed to Recommendations' button and add spacing below it
st.markdown("""
    <style>
    div.stButton > button {
        display: block;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 20px; /* Add space below the button */
    }
    </style>
    """, unsafe_allow_html=True)

# TMDB API key
TMDB_API_KEY = st.secrets["tmdb_api"]["api_key"]
# OMDb API key
OMDB_API_KEY = st.secrets["omdb_api"]["api_key"]

# Function to fetch trending movies
@st.cache_data(show_spinner=False)
def fetch_trending_movies(api_key):
    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}"
    response = requests.get(url).json()
    trending_movies = []
    if "results" in response:
        for movie in response["results"][:5]:  # Limit to top 5 movies
            trending_movies.append({
                "title": movie["title"],
                "poster_path": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}",
                "overview": movie["overview"],
                "rating": round(movie["vote_average"], 1),  # Round to 1 decimal place
                "release_date": movie.get("release_date", "N/A")[:4]  # Get year only
            })
    return trending_movies

# Fetch trending movies
trending_movies = fetch_trending_movies(TMDB_API_KEY)

# Initialize session state
if "carousel_index" not in st.session_state:
    st.session_state.carousel_index = 0

if "show_recommendations" not in st.session_state:
    st.session_state.show_recommendations = False

# Show trending movies if recommendations are not yet selected
if not st.session_state.show_recommendations:
    st.markdown("""
        <div style="text-align: center; color: red; font-size: 3rem; font-weight: bold;">
            Welcome to Movie Matchmaker!
        </div>
        <p style="text-align: center; font-size: 1.2rem; color: #f5f5f5; margin-top: 10px;">
            This platform is designed to give you quick, personalized movie recommendations 
            based on your unique tastes and preferences. Start by browsing trending movies or 
            proceed to the personalized recommendations below!
        </p>
    """, unsafe_allow_html=True)

    if trending_movies:
        # Use st_autorefresh to automatically refresh the page every 5 seconds (5000 ms)
        count = st_autorefresh(interval=5000, limit=None, key="carousel_counter")

        # Update the carousel index based on the autorefresh count
        st.session_state.carousel_index = count % len(trending_movies)
        current_movie = trending_movies[st.session_state.carousel_index]

        # Display Movie Card
        st.markdown(f"""
            <div style="display: flex; justify-content: center; align-items: center;">
                <div style="background: #1C1C1C; color: white; padding: 20px; border-radius: 15px; width: 300px; text-align: center;">
                    <img src="{current_movie['poster_path']}" alt="{current_movie['title']}" style="width: 100%; border-radius: 10px; margin-bottom: 15px;">
                    <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 10px;">
                        {current_movie['title']} ({current_movie['release_date']})
                    </div>
                    <div style="color: #f39c12; font-size: 1rem; margin-bottom: 15px;">
                        ⭐ {current_movie['rating']}
                    </div>
                    <p style="font-size: 0.9rem; color: #bbb;">
                        {current_movie['overview'][:300]}...
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Proceed to Recommendations button underneath the movie card
        if st.button("Proceed to Recommendations", key='proceed_button'):
            st.session_state.show_recommendations = True

    else:
        st.write("No trending movies available at the moment.")

else:
    # Recommendation page
    st.sidebar.header('Select Your Preferences')

    # Load the data (cached)
    @st.cache_data(show_spinner=False)
    def load_data():
        df = pd.read_csv('merged_df.zip', compression="zip")
        # Convert lists
        list_columns = ['available_languages', 'genres', 'cast', 'directors']
        for col in list_columns:
            df[col] = df[col].apply(ast.literal_eval)
        return df

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("The data file 'merged_df.zip' was not found. Please ensure it is in the correct directory.")
        st.stop()

    @st.cache_data(show_spinner=False)
    def get_movie_poster(imdb_id, api_key):
        url = f'http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}'
        response = requests.get(url)
        data = response.json()
        if 'Poster' in data and data['Poster'] != 'N/A':
            poster_url = data['Poster']
            poster_response = requests.get(poster_url)
            return Image.open(BytesIO(poster_response.content))
        else:
            return None

    # Sidebar filters
    available_languages = sorted(df['available_languages'].explode().unique().tolist())
    selected_languages = st.sidebar.multiselect('Available Languages:', available_languages)

    min_runtime = int(df['runtimeMinutes'].min())
    max_runtime = int(df['runtimeMinutes'].max())
    selected_runtime_range = st.sidebar.slider('Runtime (Minutes):', min_runtime, max_runtime, (min_runtime, max_runtime))

    min_year = int(df['startYear'].min())
    max_year = int(df['startYear'].max())
    selected_year_range = st.sidebar.slider('Release Year Range:', min_year, max_year, (min_year, max_year))

    available_genres = sorted(df['genres'].explode().unique().tolist())
    selected_genres = st.sidebar.multiselect('Genres:', available_genres)

    selected_cast_input = st.sidebar.text_input('Cast (comma-separated):')
    selected_cast = [x.strip() for x in selected_cast_input.split(',')] if selected_cast_input else []

    selected_directors_input = st.sidebar.text_input('Directors (comma-separated):')
    selected_directors = [x.strip() for x in selected_directors_input.split(',')] if selected_directors_input else []

    selected_isAdult = st.sidebar.checkbox('Include Adult Movies')

    # Filter data
    filtered_df = df.copy()
    if selected_languages:
        filtered_df = filtered_df[filtered_df['available_languages'].apply(lambda x: all(lang in x for lang in selected_languages))]
    if not selected_isAdult:
        filtered_df = filtered_df[filtered_df['isAdult'] == 0]
    filtered_df = filtered_df[(filtered_df['startYear'] >= selected_year_range[0]) & (filtered_df['startYear'] <= selected_year_range[1])]
    filtered_df = filtered_df[(filtered_df['runtimeMinutes'] >= selected_runtime_range[0]) & (filtered_df['runtimeMinutes'] <= selected_runtime_range[1])]
    if selected_genres:
        filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: all(genre in x for genre in selected_genres))]
    if selected_cast:
        filtered_df = filtered_df[filtered_df['cast'].apply(lambda x: all(cast_member in x for cast_member in selected_cast))]
    if selected_directors:
        filtered_df = filtered_df[filtered_df['directors'].apply(lambda x: all(director in x for director in selected_directors))]

    filtered_df = filtered_df.sort_values(by='weighted_rating', ascending=False).reset_index(drop=True)

    if 'recommendation_index' not in st.session_state:
        st.session_state.recommendation_index = 0

    if len(filtered_df) == 0:
        st.write('No movies found with the selected filters.')
    else:
        current_index = st.session_state.recommendation_index
        if current_index < len(filtered_df):
            movie = filtered_df.iloc[current_index]
            st.write('**Recommended Movie:**')
            imdb_id = movie['tconst']
            poster = get_movie_poster(imdb_id, OMDB_API_KEY)

            # Adjust columns to [1, 2] for a 1:2 ratio (left column is 1/3 of the right one)
            col1, col2 = st.columns([1, 2])

            with col1:
                if poster:
                    st.image(poster, use_container_width=True)  
                else:
                    st.write("No poster available.")

            with col2:
                st.write(f"**Title:** {movie['title']}")
                st.write(f"**Rating:** {round(movie['weighted_rating'], 1)}")
                st.write(f"**Year:** {movie['startYear']}")
                st.write(f"**Genres:** {', '.join(movie['genres'])}")
                st.write(f"**Runtime:** {movie['runtimeMinutes']} minutes")
                st.write(f"**Cast:** {', '.join(sorted(movie['cast']))}")
                st.write(f"**Directors:** {', '.join(sorted(movie['directors']))}")
                st.write(f"**Languages:** {', '.join(sorted(movie['available_languages']))}")
                st.write(f"**Adult Content:** {'Yes' if movie['isAdult'] == 1 else 'No'}")
                # Add some spacing before the 'Next' button
                st.markdown("<br>", unsafe_allow_html=True)

                if st.button('Next', key='next_button'):
                    st.session_state.recommendation_index += 1
        else:
            st.write('No more recommendations.')
            # Optionally, you can reset the index or provide an option to restart
            if st.button('Restart Recommendations', key='restart_button'):
                st.session_state.recommendation_index = 0
