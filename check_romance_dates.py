import sqlite3

db_path = r"c:\Users\priyanshi\OneDrive\Desktop\Movie-Recommendation\backend\movies.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, title, genres, release_date FROM movies WHERE genres LIKE '%Romance%'")
romance_movies = cursor.fetchall()
conn.close()

print(f"Total Romance movies in DB: {len(romance_movies)}")
print("Romance movies by era:")
eras = {"90s & older": 0, "2000s": 0, "2010s": 0, "2020s": 0}
for m in romance_movies:
    date = m[3]
    year = int(date.split("-")[0]) if date else 0
    if year < 2000:
        eras["90s & older"] += 1
    elif year < 2010:
        eras["2000s"] += 1
    elif year < 2020:
        eras["2010s"] += 1
    else:
        eras["2020s"] += 1

for era, count in eras.items():
    print(f"  {era}: {count}")

print("\nList of all Romance movies:")
for m in romance_movies:
    print(f"  - {m[1]} ({m[3]})")
