import sqlite3

db_path = r"c:\Users\priyanshi\OneDrive\Desktop\Movie-Recommendation\backend\movies.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT awards, COUNT(*) FROM movies GROUP BY awards")
for row in cursor.fetchall():
    print(row)

conn.close()
