import sqlite3
import urllib.request

db_path = r"c:\Users\priyanshi\OneDrive\Desktop\Movie-Recommendation\backend\movies.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, title, poster_path FROM movies")
movies = cursor.fetchall()
conn.close()

headers = {'User-Agent': 'Mozilla/5.0'}
invalid_posters = []

print("Checking first 30 movie posters on TMDb CDN...")
for mid, title, path in movies[:30]:
    if not path:
        print(f"Movie: {title} - poster_path is None")
        invalid_posters.append((mid, title, "None"))
        continue
    
    url = f"https://image.tmdb.org/t/p/w500{path}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as res:
            code = res.getcode()
            if code != 200:
                print(f"Movie: {title} - URL {url} returned status {code}")
                invalid_posters.append((mid, title, path))
    except Exception as e:
        print(f"Movie: {title} - Failed to load {url}: {e}")
        invalid_posters.append((mid, title, path))

print(f"\nDone. Found {len(invalid_posters)} invalid posters in first 30 movies.")
