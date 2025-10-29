"""
Helper script to save movies from TMDb API to local database
Now includes poster_path, overview, vote_average, and more!
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from tmdb_client import tmdb_client

load_dotenv()

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "frameratr"),
        user=os.getenv("DB_USER", "fr_user"),
        password=os.getenv("DB_PASS", "fr_password"),
    )

def save_movie_to_db(tmdb_id: int):
    """
    Fetch a movie from TMDb and save it to local database with all details
    Returns the local database movie_id
    """
    # Get movie details from TMDb
    movie_data = tmdb_client.get_movie_details(tmdb_id)
    
    title = movie_data.get("title")
    release_date = movie_data.get("release_date")
    genres = [g["name"] for g in movie_data.get("genres", [])]
    
    # NEW: Extract additional fields
    poster_path = movie_data.get("poster_path")
    backdrop_path = movie_data.get("backdrop_path")
    overview = movie_data.get("overview")
    vote_average = movie_data.get("vote_average")
    vote_count = movie_data.get("vote_count")
    popularity = movie_data.get("popularity")
    runtime = movie_data.get("runtime")
    original_language = movie_data.get("original_language")
    original_title = movie_data.get("original_title")
    
    print(f"Saving: {title} ({release_date})")
    print(f"  Rating: {vote_average}/10 ({vote_count} votes)")
    print(f"  Popularity: {popularity}")
    
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        # Insert or update movie with all fields
        cur.execute("""
            INSERT INTO movie (
                title, release_date, tmdb_id,
                poster_path, backdrop_path, overview,
                vote_average, vote_count, popularity,
                runtime, original_language, original_title
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tmdb_id) DO UPDATE
            SET title = EXCLUDED.title,
                release_date = EXCLUDED.release_date,
                poster_path = EXCLUDED.poster_path,
                backdrop_path = EXCLUDED.backdrop_path,
                overview = EXCLUDED.overview,
                vote_average = EXCLUDED.vote_average,
                vote_count = EXCLUDED.vote_count,
                popularity = EXCLUDED.popularity,
                runtime = EXCLUDED.runtime,
                original_language = EXCLUDED.original_language,
                original_title = EXCLUDED.original_title
            RETURNING id;
        """, (
            title, release_date, tmdb_id,
            poster_path, backdrop_path, overview,
            vote_average, vote_count, popularity,
            runtime, original_language, original_title
        ))
        movie_id = cur.fetchone()["id"]
        
        # Insert genres and link to movie
        for genre_name in genres:
            # Insert genre if not exists
            cur.execute("""
                INSERT INTO genre (name) VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id;
            """, (genre_name,))
            
            # Get genre_id
            if cur.rowcount == 0:
                cur.execute("SELECT id FROM genre WHERE name = %s", (genre_name,))
            genre_id = cur.fetchone()["id"]
            
            # Link movie to genre
            cur.execute("""
                INSERT INTO movie_genre (movie_id, genre_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """, (movie_id, genre_id))
        
        print(f"✓ Saved movie ID {movie_id}: {title}")
        return movie_id

def save_tv_to_db(tmdb_id: int):
    """
    Fetch a TV show from TMDb and save it to local database with all details
    Returns the local database tv_id
    """
    # Get TV show details from TMDb
    tv_data = tmdb_client.get_tv_details(tmdb_id)
    
    title = tv_data.get("name")
    release_date = tv_data.get("first_air_date")
    genres = [g["name"] for g in tv_data.get("genres", [])]
    
    # NEW: Extract additional fields
    poster_path = tv_data.get("poster_path")
    backdrop_path = tv_data.get("backdrop_path")
    overview = tv_data.get("overview")
    vote_average = tv_data.get("vote_average")
    vote_count = tv_data.get("vote_count")
    popularity = tv_data.get("popularity")
    number_of_seasons = tv_data.get("number_of_seasons")
    number_of_episodes = tv_data.get("number_of_episodes")
    original_language = tv_data.get("original_language")
    original_title = tv_data.get("original_name")
    
    print(f"Saving: {title} ({release_date})")
    print(f"  Rating: {vote_average}/10 ({vote_count} votes)")
    print(f"  Seasons: {number_of_seasons}, Episodes: {number_of_episodes}")
    
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        # Insert or update TV show with all fields
        cur.execute("""
            INSERT INTO tv_show (
                title, release_date, tmdb_id,
                poster_path, backdrop_path, overview,
                vote_average, vote_count, popularity,
                number_of_seasons, number_of_episodes,
                original_language, original_title
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tmdb_id) DO UPDATE
            SET title = EXCLUDED.title,
                release_date = EXCLUDED.release_date,
                poster_path = EXCLUDED.poster_path,
                backdrop_path = EXCLUDED.backdrop_path,
                overview = EXCLUDED.overview,
                vote_average = EXCLUDED.vote_average,
                vote_count = EXCLUDED.vote_count,
                popularity = EXCLUDED.popularity,
                number_of_seasons = EXCLUDED.number_of_seasons,
                number_of_episodes = EXCLUDED.number_of_episodes,
                original_language = EXCLUDED.original_language,
                original_title = EXCLUDED.original_title
            RETURNING id;
        """, (
            title, release_date, tmdb_id,
            poster_path, backdrop_path, overview,
            vote_average, vote_count, popularity,
            number_of_seasons, number_of_episodes,
            original_language, original_title
        ))
        tv_id = cur.fetchone()["id"]
        
        # Insert genres and link to TV show
        for genre_name in genres:
            cur.execute("""
                INSERT INTO genre (name) VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id;
            """, (genre_name,))
            
            if cur.rowcount == 0:
                cur.execute("SELECT id FROM genre WHERE name = %s", (genre_name,))
            genre_id = cur.fetchone()["id"]
            
            cur.execute("""
                INSERT INTO tv_genre (tv_id, genre_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """, (tv_id, genre_id))
        
        print(f"✓ Saved TV show ID {tv_id}: {title}")
        return tv_id

def seed_popular_movies(count=20):
    """Seed database with popular movies from TMDb"""
    print(f"Fetching {count} popular movies from TMDb...")
    popular = tmdb_client.get_popular_movies()
    
    saved_count = 0
    for movie in popular["results"][:count]:
        try:
            save_movie_to_db(movie["id"])
            saved_count += 1
        except Exception as e:
            print(f"✗ Error saving {movie.get('title')}: {e}")
    
    print(f"\n✓ Successfully saved {saved_count}/{count} movies")

def seed_trending_movies(count=20):
    """Seed database with trending movies from TMDb"""
    print(f"Fetching {count} trending movies from TMDb...")
    trending = tmdb_client.get_trending_movies()
    
    saved_count = 0
    for movie in trending["results"][:count]:
        try:
            save_movie_to_db(movie["id"])
            saved_count += 1
        except Exception as e:
            print(f"✗ Error saving {movie.get('title')}: {e}")
    
    print(f"\n✓ Successfully saved {saved_count}/{count} movies")

def seed_top_rated_movies(count=20):
    """Seed database with top-rated movies from TMDb"""
    print(f"Fetching {count} top-rated movies from TMDb...")
    top_rated = tmdb_client.get_top_rated_movies()
    
    saved_count = 0
    for movie in top_rated["results"][:count]:
        try:
            save_movie_to_db(movie["id"])
            saved_count += 1
        except Exception as e:
            print(f"✗ Error saving {movie.get('title')}: {e}")
    
    print(f"\n✓ Successfully saved {saved_count}/{count} movies")


if __name__ == "__main__":
    print("=" * 60)
    print("FrameRatr - Database Seeding Script")
    print("=" * 60)
    print()
    print("Options:")
    print("1. Seed 20 popular movies")
    print("2. Seed 20 trending movies")
    print("3. Seed 20 top-rated movies")
    print("4. Save specific movie by TMDb ID")
    print("5. Save specific TV show by TMDb ID")
    print()
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        seed_popular_movies(20)
    elif choice == "2":
        seed_trending_movies(20)
    elif choice == "3":
        seed_top_rated_movies(20)
    elif choice == "4":
        tmdb_id = input("Enter TMDb movie ID: ").strip()
        save_movie_to_db(int(tmdb_id))
    elif choice == "5":
        tmdb_id = input("Enter TMDb TV show ID: ").strip()
        save_tv_to_db(int(tmdb_id))
    else:
        print("Invalid choice!")