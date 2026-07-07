import os
import sqlite3

db_path = r"c:\Users\priyanshi\OneDrive\Desktop\Movie-Recommendation\backend\movies.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get total number of movies
cursor.execute("SELECT COUNT(*) FROM movies")
total = cursor.fetchone()[0]
print(f"Total movies: {total}")

# Get count of movies with null poster_path or empty
cursor.execute("SELECT COUNT(*) FROM movies WHERE poster_path IS NULL OR poster_path = ''")
null_posters = cursor.fetchone()[0]
print(f"Movies with null/empty poster_path: {null_posters}")

# Get count of romance movies
cursor.execute("SELECT COUNT(*) FROM movies WHERE genres LIKE '%Romance%'")
romance_count = cursor.fetchone()[0]
print(f"Movies with Romance genre: {romance_count}")

# Print a few romance movies
cursor.execute("SELECT title, genres, poster_path, release_date FROM movies WHERE genres LIKE '%Romance%' LIMIT 10")
print("\nSome Romance movies in DB:")
for row in cursor.fetchall():
    print(row)

# Print a few movies with null posters
cursor.execute("SELECT title, genres, poster_path FROM movies WHERE poster_path IS NULL OR poster_path = '' LIMIT 10")
print("\nSome movies with null/empty poster_path in DB:")
for row in cursor.fetchall():
    print(row)

conn.close()
