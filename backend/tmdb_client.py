#TMDb API integration
import os
import requests
import time
from typing import Optional, List, Dict, Any

class TMDbClient:
    """Client for interacting with The Movie Database (TMDb) API"""
    
    def __init__(self):
        self.token = os.getenv("TMDB_TOKEN")
        self.sleep_sec = float(os.getenv("TMDB_SLEEP_SEC", "0.25"))
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        """Make a request to TMDb API with rate limiting"""
        url = f"{self.base_url}{endpoint}"
        time.sleep(self.sleep_sec)  # Rate limiting
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    # ============ SEARCH ============
    
    def search_movies(self, query: str, page: int = 1) -> Dict[Any, Any]:
        """Search for movies by title"""
        return self._make_request("/search/movie", {
            "query": query,
            "page": page,
            "include_adult": False
        })
    
    def search_tv(self, query: str, page: int = 1) -> Dict[Any, Any]:
        """Search for TV shows by title"""
        return self._make_request("/search/tv", {
            "query": query,
            "page": page,
            "include_adult": False
        })
    
    def search_multi(self, query: str, page: int = 1) -> Dict[Any, Any]:
        """Search for movies and TV shows combined"""
        return self._make_request("/search/multi", {
            "query": query,
            "page": page,
            "include_adult": False
        })
    
    # ============ MOVIE DETAILS ============
    
    def get_movie_details(self, movie_id: int) -> Dict[Any, Any]:
        """Get detailed information about a movie"""
        return self._make_request(f"/movie/{movie_id}", {
            "append_to_response": "credits,videos,similar,recommendations"
        })
    
    def get_movie_credits(self, movie_id: int) -> Dict[Any, Any]:
        """Get cast and crew for a movie"""
        return self._make_request(f"/movie/{movie_id}/credits")
    
    def get_movie_videos(self, movie_id: int) -> Dict[Any, Any]:
        """Get trailers and videos for a movie"""
        return self._make_request(f"/movie/{movie_id}/videos")
    
    def get_movie_similar(self, movie_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get similar movies"""
        return self._make_request(f"/movie/{movie_id}/similar", {"page": page})
    
    def get_movie_recommendations(self, movie_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get recommended movies based on a movie"""
        return self._make_request(f"/movie/{movie_id}/recommendations", {"page": page})
    
    # ============ TV SHOW DETAILS ============
    
    def get_tv_details(self, tv_id: int) -> Dict[Any, Any]:
        """Get detailed information about a TV show"""
        return self._make_request(f"/tv/{tv_id}", {
            "append_to_response": "credits,videos,similar,recommendations"
        })
    
    def get_tv_credits(self, tv_id: int) -> Dict[Any, Any]:
        """Get cast and crew for a TV show"""
        return self._make_request(f"/tv/{tv_id}/credits")
    
    def get_tv_videos(self, tv_id: int) -> Dict[Any, Any]:
        """Get trailers and videos for a TV show"""
        return self._make_request(f"/tv/{tv_id}/videos")
    
    def get_tv_similar(self, tv_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get similar TV shows"""
        return self._make_request(f"/tv/{tv_id}/similar", {"page": page})
    
    def get_tv_recommendations(self, tv_id: int, page: int = 1) -> Dict[Any, Any]:
        """Get recommended TV shows based on a TV show"""
        return self._make_request(f"/tv/{tv_id}/recommendations", {"page": page})
    
    # ============ TRENDING ============
    
    def get_trending_movies(self, time_window: str = "day", page: int = 1) -> Dict[Any, Any]:
        """Get trending movies (time_window: 'day' or 'week')"""
        return self._make_request(f"/trending/movie/{time_window}", {"page": page})
    
    def get_trending_tv(self, time_window: str = "day", page: int = 1) -> Dict[Any, Any]:
        """Get trending TV shows (time_window: 'day' or 'week')"""
        return self._make_request(f"/trending/tv/{time_window}", {"page": page})
    
    def get_trending_all(self, time_window: str = "day", page: int = 1) -> Dict[Any, Any]:
        """Get trending movies and TV shows (time_window: 'day' or 'week')"""
        return self._make_request(f"/trending/all/{time_window}", {"page": page})
    
    # ============ POPULAR & TOP RATED ============
    
    def get_popular_movies(self, page: int = 1) -> Dict[Any, Any]:
        """Get popular movies"""
        return self._make_request("/movie/popular", {"page": page})
    
    def get_popular_tv(self, page: int = 1) -> Dict[Any, Any]:
        """Get popular TV shows"""
        return self._make_request("/tv/popular", {"page": page})
    
    def get_top_rated_movies(self, page: int = 1) -> Dict[Any, Any]:
        """Get top rated movies"""
        return self._make_request("/movie/top_rated", {"page": page})
    
    def get_top_rated_tv(self, page: int = 1) -> Dict[Any, Any]:
        """Get top rated TV shows"""
        return self._make_request("/tv/top_rated", {"page": page})
    
    def get_upcoming_movies(self, page: int = 1) -> Dict[Any, Any]:
        """Get upcoming movies"""
        return self._make_request("/movie/upcoming", {"page": page})
    
    def get_now_playing_movies(self, page: int = 1) -> Dict[Any, Any]:
        """Get movies now playing in theaters"""
        return self._make_request("/movie/now_playing", {"page": page})
    
    # ============ DISCOVER (with filters) ============
    
    def discover_movies(self, **filters) -> Dict[Any, Any]:
        """
        Discover movies with filters
        
        Available filters:
        - with_genres: comma-separated genre IDs
        - primary_release_year: year
        - sort_by: popularity.desc, vote_average.desc, etc.
        - page: page number
        """
        return self._make_request("/discover/movie", filters)
    
    def discover_tv(self, **filters) -> Dict[Any, Any]:
        """
        Discover TV shows with filters
        
        Available filters:
        - with_genres: comma-separated genre IDs
        - first_air_date_year: year
        - sort_by: popularity.desc, vote_average.desc, etc.
        - page: page number
        """
        return self._make_request("/discover/tv", filters)
    
    # ============ GENRES ============
    
    def get_movie_genres(self) -> Dict[Any, Any]:
        """Get list of movie genres"""
        return self._make_request("/genre/movie/list")
    
    def get_tv_genres(self) -> Dict[Any, Any]:
        """Get list of TV genres"""
        return self._make_request("/genre/tv/list")
    
    # ============ PERSON (Cast/Crew) ============
    
    def get_person_details(self, person_id: int) -> Dict[Any, Any]:
        """Get details about a person (actor, director, etc.)"""
        return self._make_request(f"/person/{person_id}")
    
    def search_person(self, query: str, page: int = 1) -> Dict[Any, Any]:
        """Search for people by name"""
        return self._make_request("/search/person", {
            "query": query,
            "page": page
        })


# Create a singleton instance
tmdb_client = TMDbClient()