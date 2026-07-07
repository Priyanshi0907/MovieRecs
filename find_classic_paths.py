import urllib.request
import urllib.parse
import json

api_key = "2d11825663306373fbd924fcfb975415"
headers = {'User-Agent': 'Mozilla/5.0'}

classics = [
    "Interstellar", "Inception", "The Dark Knight", "The Martian", "Arrival",
    "Pulp Fiction", "Django Unchained", "Fight Club", "Shutter Island",
    "The Wolf of Wall Street", "La La Land", "Whiplash", "About Time", "Parasite",
    "Spirited Away", "Your Name.", "Princess Mononoke", "The Matrix", "Gladiator",
    "Blade Runner 2049", "Knives Out", "Avengers: Endgame", "The Grand Budapest Hotel",
    "Spider-Man: Into the Spider-Verse", "Your Lie in April"
]

results = {}
for title in classics:
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(title)}&language=en-US&page=1"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode('utf-8'))
            matches = data.get('results', [])
            if matches:
                match = matches[0]
                results[title] = {
                    "tmdb_id": match['id'],
                    "poster_path": match.get('poster_path'),
                    "backdrop_path": match.get('backdrop_path')
                }
                print(f"Classic: {title} -> ID: {match['id']}, Poster: {match.get('poster_path')}")
            else:
                print(f"No match for classic: {title}")
    except Exception as e:
        print(f"Error for classic {title}: {e}")

print("\nResult JSON:")
print(json.dumps(results, indent=2))
