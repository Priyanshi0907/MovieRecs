import sqlite3

db_path = r"c:\Users\priyanshi\OneDrive\Desktop\Movie-Recommendation\backend\movies.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get 20 movies
cursor.execute("SELECT id, title, genres, poster_path, vote_average FROM movies LIMIT 30")
for row in cursor.fetchall():
    print(row)

conn.close()
