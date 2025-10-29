import os
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, credentials
from tmdb_client import tmdb_client

load_dotenv()

def init_firebase():
    svc_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "firebase-service-account.json")
    if not firebase_admin._apps:
        cred = credentials.Certificate(svc_path)
        firebase_admin.initialize_app(cred)

init_firebase()

app = Flask(__name__)
CORS(app)

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "frameratr"),
        user=os.getenv("DB_USER", "fr_user"),
        password=os.getenv("DB_PASS", "fr_password")
    )

def require_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401)
    token = auth_header.split(" ", 1)[1]
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception:
        abort(401)

# ============================================
# HEALTH & BASIC ENDPOINTS
# ============================================

@app.route("/health")
def health():
    return {"ok": True}

@app.route('/')
def index():
    return "Welcome to FrameRatr API!"

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({
        'message': 'Hello, World!',
        'status': 'success'
    })

# ============================================
# USER ENDPOINTS
# ============================================

@app.route("/api/me", methods=["GET"])
def me():
    user = require_user()
    uid = user["uid"]
    email = user.get("email")
    display_name = user.get("name")

    sql = """
    INSERT INTO app_user (uid, email, display_name)
    VALUES (%s, %s, %s)
    ON CONFLICT (uid) DO UPDATE
      SET email = EXCLUDED.email,
          display_name = COALESCE(EXCLUDED.display_name, app_user.display_name)
    RETURNING uid, email, display_name, created_at;
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (uid, email, display_name))
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    return jsonify(row)

# ============================================
# DATABASE MOVIE ENDPOINTS (Local) - NOW WITH CACHED TMDB DATA
# ============================================

@app.route("/api/movies", methods=["GET"])
def list_movies():
    """List movies from local database with all TMDb cached data"""
    q = request.args.get("q")
    sql = """
        SELECT id, title, release_date, tmdb_id,
               poster_path, backdrop_path, overview,
               vote_average, vote_count, popularity,
               runtime, original_language, original_title
        FROM movie
    """
    params = []
    if q:
        sql += " WHERE title ILIKE %s"
        params.append(f"%{q}%")
    sql += " ORDER BY popularity DESC NULLS LAST, id DESC LIMIT 50"
    
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return jsonify(rows)

@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def movie_detail(movie_id: int):
    """Get movie details from local database with all cached TMDb data"""
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT m.id, m.title, m.release_date, m.tmdb_id,
                   m.poster_path, m.backdrop_path, m.overview,
                   m.vote_average AS tmdb_rating, m.vote_count AS tmdb_votes,
                   m.popularity, m.runtime, m.original_language, m.original_title,
                   COALESCE(a.rating_count, 0) AS user_rating_count,
                   ROUND(COALESCE(a.rating_avg, 0)::numeric, 1) AS user_rating_avg
            FROM movie m
            LEFT JOIN movie_rating_agg a ON a.movie_id = m.id
            WHERE m.id = %s
        """, (movie_id,))
        movie = cur.fetchone()
        if not movie:
            return jsonify({"error": "not found"}), 404

        cur.execute("""
            SELECT g.name
            FROM movie_genre mg
            JOIN genre g ON g.id = mg.genre_id
            WHERE mg.movie_id = %s
            ORDER BY g.name
        """, (movie_id,))
        genres = [row["name"] for row in cur.fetchall()]
    
    movie["genres"] = genres
    return jsonify(movie)

@app.route("/api/movies/<int:movie_id>/reviews", methods=["GET"])
def movie_reviews(movie_id: int):
    """Get reviews for a movie from local database"""
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT r.id, r.body, r.created_at, u.display_name, u.uid
            FROM movie_review r
            JOIN app_user u ON u.uid = r.uid
            WHERE r.movie_id = %s
            ORDER BY r.created_at DESC
            LIMIT 50
        """, (movie_id,))
        rows = cur.fetchall()
    return jsonify(rows)

# ============================================
# TMDB SEARCH ENDPOINTS
# ============================================

@app.route("/api/tmdb/search/movies", methods=["GET"])
def tmdb_search_movies():
    """Search movies on TMDb"""
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    try:
        results = tmdb_client.search_movies(query, page)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/search/tv", methods=["GET"])
def tmdb_search_tv():
    """Search TV shows on TMDb"""
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    try:
        results = tmdb_client.search_tv(query, page)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/search/multi", methods=["GET"])
def tmdb_search_multi():
    """Search movies and TV shows on TMDb"""
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    try:
        results = tmdb_client.search_multi(query, page)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# TMDB MOVIE DETAILS
# ============================================

@app.route("/api/tmdb/movie/<int:tmdb_id>", methods=["GET"])
def tmdb_movie_details(tmdb_id: int):
    """Get movie details from TMDb"""
    try:
        movie = tmdb_client.get_movie_details(tmdb_id)
        return jsonify(movie)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/movie/<int:tmdb_id>/credits", methods=["GET"])
def tmdb_movie_credits(tmdb_id: int):
    """Get movie cast and crew from TMDb"""
    try:
        credits = tmdb_client.get_movie_credits(tmdb_id)
        return jsonify(credits)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/movie/<int:tmdb_id>/videos", methods=["GET"])
def tmdb_movie_videos(tmdb_id: int):
    """Get movie trailers and videos from TMDb"""
    try:
        videos = tmdb_client.get_movie_videos(tmdb_id)
        return jsonify(videos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/movie/<int:tmdb_id>/similar", methods=["GET"])
def tmdb_movie_similar(tmdb_id: int):
    """Get similar movies from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        similar = tmdb_client.get_movie_similar(tmdb_id, page)
        return jsonify(similar)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/movie/<int:tmdb_id>/recommendations", methods=["GET"])
def tmdb_movie_recommendations(tmdb_id: int):
    """Get recommended movies from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        recommendations = tmdb_client.get_movie_recommendations(tmdb_id, page)
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# TMDB TV SHOW DETAILS
# ============================================

@app.route("/api/tmdb/tv/<int:tmdb_id>", methods=["GET"])
def tmdb_tv_details(tmdb_id: int):
    """Get TV show details from TMDb"""
    try:
        tv = tmdb_client.get_tv_details(tmdb_id)
        return jsonify(tv)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/tv/<int:tmdb_id>/credits", methods=["GET"])
def tmdb_tv_credits(tmdb_id: int):
    """Get TV show cast and crew from TMDb"""
    try:
        credits = tmdb_client.get_tv_credits(tmdb_id)
        return jsonify(credits)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/tv/<int:tmdb_id>/videos", methods=["GET"])
def tmdb_tv_videos(tmdb_id: int):
    """Get TV show trailers and videos from TMDb"""
    try:
        videos = tmdb_client.get_tv_videos(tmdb_id)
        return jsonify(videos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/tv/<int:tmdb_id>/similar", methods=["GET"])
def tmdb_tv_similar(tmdb_id: int):
    """Get similar TV shows from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        similar = tmdb_client.get_tv_similar(tmdb_id, page)
        return jsonify(similar)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/tv/<int:tmdb_id>/recommendations", methods=["GET"])
def tmdb_tv_recommendations(tmdb_id: int):
    """Get recommended TV shows from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        recommendations = tmdb_client.get_tv_recommendations(tmdb_id, page)
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# TMDB TRENDING & POPULAR
# ============================================

@app.route("/api/tmdb/trending/movies", methods=["GET"])
def tmdb_trending_movies():
    """Get trending movies from TMDb"""
    time_window = request.args.get("time_window", "day")
    page = request.args.get("page", 1, type=int)
    try:
        trending = tmdb_client.get_trending_movies(time_window, page)
        return jsonify(trending)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/trending/tv", methods=["GET"])
def tmdb_trending_tv():
    """Get trending TV shows from TMDb"""
    time_window = request.args.get("time_window", "day")
    page = request.args.get("page", 1, type=int)
    try:
        trending = tmdb_client.get_trending_tv(time_window, page)
        return jsonify(trending)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/trending/all", methods=["GET"])
def tmdb_trending_all():
    """Get trending movies and TV shows from TMDb"""
    time_window = request.args.get("time_window", "day")
    page = request.args.get("page", 1, type=int)
    try:
        trending = tmdb_client.get_trending_all(time_window, page)
        return jsonify(trending)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/popular/movies", methods=["GET"])
def tmdb_popular_movies():
    """Get popular movies from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        popular = tmdb_client.get_popular_movies(page)
        return jsonify(popular)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/popular/tv", methods=["GET"])
def tmdb_popular_tv():
    """Get popular TV shows from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        popular = tmdb_client.get_popular_tv(page)
        return jsonify(popular)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/top-rated/movies", methods=["GET"])
def tmdb_top_rated_movies():
    """Get top rated movies from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        top_rated = tmdb_client.get_top_rated_movies(page)
        return jsonify(top_rated)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/top-rated/tv", methods=["GET"])
def tmdb_top_rated_tv():
    """Get top rated TV shows from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        top_rated = tmdb_client.get_top_rated_tv(page)
        return jsonify(top_rated)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/upcoming/movies", methods=["GET"])
def tmdb_upcoming_movies():
    """Get upcoming movies from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        upcoming = tmdb_client.get_upcoming_movies(page)
        return jsonify(upcoming)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/now-playing/movies", methods=["GET"])
def tmdb_now_playing_movies():
    """Get now playing movies from TMDb"""
    page = request.args.get("page", 1, type=int)
    try:
        now_playing = tmdb_client.get_now_playing_movies(page)
        return jsonify(now_playing)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# TMDB DISCOVER & GENRES
# ============================================

@app.route("/api/tmdb/discover/movies", methods=["GET"])
def tmdb_discover_movies():
    """Discover movies with filters from TMDb"""
    filters = request.args.to_dict()
    try:
        results = tmdb_client.discover_movies(**filters)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/discover/tv", methods=["GET"])
def tmdb_discover_tv():
    """Discover TV shows with filters from TMDb"""
    filters = request.args.to_dict()
    try:
        results = tmdb_client.discover_tv(**filters)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/genres/movies", methods=["GET"])
def tmdb_movie_genres():
    """Get movie genres from TMDb"""
    try:
        genres = tmdb_client.get_movie_genres()
        return jsonify(genres)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/genres/tv", methods=["GET"])
def tmdb_tv_genres():
    """Get TV genres from TMDb"""
    try:
        genres = tmdb_client.get_tv_genres()
        return jsonify(genres)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# TMDB PERSON/CAST
# ============================================

@app.route("/api/tmdb/person/<int:person_id>", methods=["GET"])
def tmdb_person_details(person_id: int):
    """Get person details from TMDb"""
    try:
        person = tmdb_client.get_person_details(person_id)
        return jsonify(person)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tmdb/search/person", methods=["GET"])
def tmdb_search_person():
    """Search for people on TMDb"""
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    try:
        results = tmdb_client.search_person(query, page)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# USER RATINGS & REVIEWS
# ============================================

@app.route("/api/ratings", methods=["POST"])
def upsert_rating():
    """Add or update a user's rating for a movie"""
    user = require_user()
    body = request.get_json(force=True)
    movie_id = int(body["movie_id"])
    rating_val = float(body["rating_val"])

    with get_db_conn() as con, con.cursor() as cur:
        cur.execute("""
            INSERT INTO movie_rating (uid, movie_id, rating_val)
            VALUES (%s, %s, %s)
            ON CONFLICT (uid, movie_id) DO UPDATE
            SET rating_val = EXCLUDED.rating_val,
                rated_at = now();
        """, (user["uid"], movie_id, rating_val))
    return {"ok": True}

@app.route("/api/reviews", methods=["POST"])
def add_review():
    """Add a user review for a movie"""
    user = require_user()
    body = request.get_json(force=True)
    movie_id = int(body["movie_id"])
    review_body = body["body"]

    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO movie_review (movie_id, uid, body)
            VALUES (%s, %s, %s)
            ON CONFLICT (movie_id, uid) DO UPDATE
            SET body = EXCLUDED.body,
                created_at = now()
            RETURNING id, movie_id, uid, body, created_at;
        """, (movie_id, user["uid"], review_body))
        review = cur.fetchone()
    return jsonify(review)

# ============================================
# USER FAVORITES
# ============================================

@app.route("/api/favorites/movies", methods=["GET"])
def get_favorite_movies():
    """Get user's favorite movies with all cached TMDb data"""
    user = require_user()
    
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT m.id, m.title, m.release_date, m.tmdb_id,
                   m.poster_path, m.backdrop_path, m.overview,
                   m.vote_average, m.vote_count, m.popularity,
                   fm.created_at AS favorited_at
            FROM favorite_movie fm
            JOIN movie m ON m.id = fm.movie_id
            WHERE fm.uid = %s
            ORDER BY fm.created_at DESC;
        """, (user["uid"],))
        favorites = cur.fetchall()
    return jsonify(favorites)

@app.route("/api/favorites/movies/<int:movie_id>", methods=["POST"])
def add_favorite_movie(movie_id: int):
    """Add a movie to user's favorites"""
    user = require_user()
    
    with get_db_conn() as con, con.cursor() as cur:
        cur.execute("""
            INSERT INTO favorite_movie (uid, movie_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user["uid"], movie_id))
    return {"ok": True}

@app.route("/api/favorites/movies/<int:movie_id>", methods=["DELETE"])
def remove_favorite_movie(movie_id: int):
    """Remove a movie from user's favorites"""
    user = require_user()
    
    with get_db_conn() as con, con.cursor() as cur:
        cur.execute("""
            DELETE FROM favorite_movie
            WHERE uid = %s AND movie_id = %s;
        """, (user["uid"], movie_id))
    return {"ok": True}

# ============================================
# RECOMMENDATIONS (Based on Favorites)
# ============================================

@app.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Get movie recommendations based on user's favorites"""
    user = require_user()
    
    with get_db_conn() as con, con.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT m.tmdb_id
            FROM favorite_movie fm
            JOIN movie m ON m.id = fm.movie_id
            WHERE fm.uid = %s
            LIMIT 5;
        """, (user["uid"],))
        favorites = cur.fetchall()
    
    if not favorites:
        return jsonify({"message": "No favorites found. Add some movies to your favorites first!"})
    
    all_recommendations = []
    seen_ids = set()
    
    try:
        for fav in favorites:
            tmdb_id = fav["tmdb_id"]
            recs = tmdb_client.get_movie_recommendations(tmdb_id)
            
            for movie in recs.get("results", [])[:5]:
                if movie["id"] not in seen_ids:
                    seen_ids.add(movie["id"])
                    all_recommendations.append(movie)
        
        return jsonify({
            "based_on_favorites": len(favorites),
            "recommendations": all_recommendations[:20]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", "3000"))
    app.run(debug=True, host='0.0.0.0', port=port)