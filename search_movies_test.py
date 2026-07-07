import urllib.request
import urllib.parse
import json

api_key = "2d11825663306373fbd924fcfb975415"
headers = {'User-Agent': 'Mozilla/5.0'}

def search_movie(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(title)}&language=en-US&page=1"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        data = json.loads(res.read().decode('utf-8'))
        results = data.get('results', [])
        print(f"--- Search results for '{title}' ---")
        for r in results[:3]:
            print(f"Title: {r.get('title')}, ID: {r.get('id')}, Poster: {r.get('poster_path')}, Release: {r.get('release_date')}")

search_movie("La La Land")
search_movie("About Time")
search_movie("Your Name.")
search_movie("Your Lie in April")
