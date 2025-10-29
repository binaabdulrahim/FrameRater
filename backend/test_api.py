# Test script to verify everything works

#!/usr/bin/env python3
"""
Test script for FrameRatr API endpoints
Run this to verify all TMDb integrations are working
"""
import requests
import json

BASE_URL = "http://localhost:3000"

def print_test(name, success, message=""):
    status = "✓" if success else "✗"
    print(f"{status} {name}")
    if message:
        print(f"  {message}")

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200 and response.json().get("ok") == True
        print_test("Health Check", success)
        return success
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_search_movies():
    """Test movie search"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/search/movies", params={"q": "batman"})
        data = response.json()
        success = response.status_code == 200 and len(data.get("results", [])) > 0
        print_test("Search Movies", success, f"Found {len(data.get('results', []))} results")
        return success
    except Exception as e:
        print_test("Search Movies", False, str(e))
        return False

def test_search_tv():
    """Test TV show search"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/search/tv", params={"q": "breaking bad"})
        data = response.json()
        success = response.status_code == 200 and len(data.get("results", [])) > 0
        print_test("Search TV Shows", success, f"Found {len(data.get('results', []))} results")
        return success
    except Exception as e:
        print_test("Search TV Shows", False, str(e))
        return False

def test_movie_details():
    """Test getting movie details"""
    try:
        # The Dark Knight
        response = requests.get(f"{BASE_URL}/api/tmdb/movie/155")
        data = response.json()
        success = response.status_code == 200 and data.get("title") == "The Dark Knight"
        print_test("Get Movie Details", success, data.get("title", ""))
        return success
    except Exception as e:
        print_test("Get Movie Details", False, str(e))
        return False

def test_movie_credits():
    """Test getting movie credits"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/movie/155/credits")
        data = response.json()
        cast = data.get("cast", [])
        success = response.status_code == 200 and len(cast) > 0
        print_test("Get Movie Credits", success, f"{len(cast)} cast members")
        return success
    except Exception as e:
        print_test("Get Movie Credits", False, str(e))
        return False

def test_trending_movies():
    """Test getting trending movies"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/trending/movies")
        data = response.json()
        results = data.get("results", [])
        success = response.status_code == 200 and len(results) > 0
        print_test("Get Trending Movies", success, f"{len(results)} trending movies")
        return success
    except Exception as e:
        print_test("Get Trending Movies", False, str(e))
        return False

def test_popular_movies():
    """Test getting popular movies"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/popular/movies")
        data = response.json()
        results = data.get("results", [])
        success = response.status_code == 200 and len(results) > 0
        print_test("Get Popular Movies", success, f"{len(results)} popular movies")
        return success
    except Exception as e:
        print_test("Get Popular Movies", False, str(e))
        return False

def test_upcoming_movies():
    """Test getting upcoming movies"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/upcoming/movies")
        data = response.json()
        results = data.get("results", [])
        success = response.status_code == 200 and len(results) > 0
        print_test("Get Upcoming Movies", success, f"{len(results)} upcoming movies")
        return success
    except Exception as e:
        print_test("Get Upcoming Movies", False, str(e))
        return False

def test_genres():
    """Test getting movie genres"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/genres/movies")
        data = response.json()
        genres = data.get("genres", [])
        success = response.status_code == 200 and len(genres) > 0
        print_test("Get Movie Genres", success, f"{len(genres)} genres")
        return success
    except Exception as e:
        print_test("Get Movie Genres", False, str(e))
        return False

def test_discover():
    """Test discover endpoint with filters"""
    try:
        # Discover Action movies from 2023
        response = requests.get(
            f"{BASE_URL}/api/tmdb/discover/movies",
            params={"with_genres": "28", "primary_release_year": "2023"}
        )
        data = response.json()
        results = data.get("results", [])
        success = response.status_code == 200 and len(results) > 0
        print_test("Discover Movies with Filters", success, f"{len(results)} action movies from 2023")
        return success
    except Exception as e:
        print_test("Discover Movies with Filters", False, str(e))
        return False

def test_recommendations():
    """Test movie recommendations"""
    try:
        # Get recommendations for The Dark Knight
        response = requests.get(f"{BASE_URL}/api/tmdb/movie/155/recommendations")
        data = response.json()
        results = data.get("results", [])
        success = response.status_code == 200 and len(results) > 0
        print_test("Get Movie Recommendations", success, f"{len(results)} recommendations")
        return success
    except Exception as e:
        print_test("Get Movie Recommendations", False, str(e))
        return False

def test_search_person():
    """Test person search"""
    try:
        response = requests.get(f"{BASE_URL}/api/tmdb/search/person", params={"q": "tom hanks"})
        data = response.json()
        results = data.get("results", [])
        success = response.status_code == 200 and len(results) > 0
        print_test("Search People", success, f"Found {len(results)} people")
        return success
    except Exception as e:
        print_test("Search People", False, str(e))
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("FrameRatr API Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Basic Endpoints", [
            test_health,
        ]),
        ("Search Endpoints", [
            test_search_movies,
            test_search_tv,
            test_search_person,
        ]),
        ("Movie Details", [
            test_movie_details,
            test_movie_credits,
        ]),
        ("Discovery & Trending", [
            test_trending_movies,
            test_popular_movies,
            test_upcoming_movies,
            test_discover,
        ]),
        ("Recommendations & Genres", [
            test_recommendations,
            test_genres,
        ]),
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for category, test_funcs in tests:
        print(f"\n{category}:")
        print("-" * 60)
        for test_func in test_funcs:
            total_tests += 1
            if test_func():
                passed_tests += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your backend is working perfectly!")
    else:
        print(f"⚠️  {total_tests - passed_tests} test(s) failed. Check the errors above.")

if __name__ == "__main__":
    run_all_tests()