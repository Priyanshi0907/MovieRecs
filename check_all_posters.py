import sqlite3
import urllib.request
import concurrent.futures

db_path = r"c:\Users\priyanshi\OneDrive\Desktop\Movie-Recommendation\backend\movies.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, title, poster_path FROM movies")
movies = cursor.fetchall()
conn.close()

headers = {'User-Agent': 'Mozilla/5.0'}
invalid_movies = []

def check_movie(m):
    mid, title, path = m
    if not path:
        return (mid, title, "None (Path is empty/null)")
    url = f"https://image.tmdb.org/t/p/w500{path}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as res:
            if res.getcode() != 200:
                return (mid, title, f"HTTP Status {res.getcode()}")
    except Exception as e:
        return (mid, title, str(e))
    return None

print(f"Checking all {len(movies)} movies in database...")
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = executor.map(check_movie, movies)
    for res in results:
        if res:
            print(f"Invalid: {res[1]} (ID: {res[0]}) - {res[2]}")
            invalid_movies.append(res)

print(f"\nTotal invalid poster paths found: {len(invalid_movies)}")
