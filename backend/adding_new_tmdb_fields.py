"""
Migration script to add TMDb caching fields to existing database
Run this to update your database without losing data
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "frameratr"),
        user=os.getenv("DB_USER", "fr_user"),
        password=os.getenv("DB_PASS", "fr_password"),
    )

def run_migration():
    """Add new TMDb fields to movie and tv_show tables"""
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            print("Starting migration...")
            
            # Add new columns to movie table
            print("Adding columns to movie table...")
            movie_columns = [
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS poster_path TEXT;",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS backdrop_path TEXT;",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS overview TEXT;",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS vote_average NUMERIC(3,1);",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS vote_count INT;",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS popularity NUMERIC(10,3);",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS runtime INT;",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS original_language VARCHAR(10);",
                "ALTER TABLE movie ADD COLUMN IF NOT EXISTS original_title VARCHAR(200);",
            ]
            
            for sql in movie_columns:
                cur.execute(sql)
            
            # Add new columns to tv_show table
            print("Adding columns to tv_show table...")
            tv_columns = [
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS poster_path TEXT;",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS backdrop_path TEXT;",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS overview TEXT;",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS vote_average NUMERIC(3,1);",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS vote_count INT;",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS popularity NUMERIC(10,3);",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS number_of_seasons INT;",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS number_of_episodes INT;",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS original_language VARCHAR(10);",
                "ALTER TABLE tv_show ADD COLUMN IF NOT EXISTS original_title VARCHAR(200);",
            ]
            
            for sql in tv_columns:
                cur.execute(sql)
            
            # Create indexes for better performance
            print("Creating indexes...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_movie_vote_average ON movie (vote_average DESC);",
                "CREATE INDEX IF NOT EXISTS idx_movie_popularity ON movie (popularity DESC);",
                "CREATE INDEX IF NOT EXISTS idx_tv_vote_average ON tv_show (vote_average DESC);",
                "CREATE INDEX IF NOT EXISTS idx_tv_popularity ON tv_show (popularity DESC);",
            ]
            
            for sql in indexes:
                cur.execute(sql)
            
            conn.commit()
            print("✓ Migration completed successfully!")
            print("\nNew fields added:")
            print("  - poster_path: TMDb poster image path")
            print("  - backdrop_path: TMDb backdrop image path")
            print("  - overview: Movie/show description")
            print("  - vote_average: TMDb rating (0-10)")
            print("  - vote_count: Number of TMDb votes")
            print("  - popularity: TMDb popularity score")
            print("  - runtime: Movie duration (minutes)")
            print("  - number_of_seasons/episodes: For TV shows")
            print("  - original_language/title: Original language and title")

if __name__ == "__main__":
    print("=" * 60)
    print("FrameRatr Database Migration")
    print("Adding TMDb caching fields")
    print("=" * 60)
    print()
    
    try:
        run_migration()
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("\nIf you see 'column already exists' errors, that's OK!")
        print("It means the columns were already added.")