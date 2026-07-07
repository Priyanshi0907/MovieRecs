import urllib.request
import json

api_key = "2d11825663306373fbd924fcfb975415"
url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&page=1&language=en-US"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Success! Popular movies count:", len(data.get('results', [])))
        if data.get('results'):
            print("First movie:", data['results'][0]['title'])
except Exception as e:
    print("Error:", e)
