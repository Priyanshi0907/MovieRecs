import urllib.request
import json
from app.database import SessionLocal
from app.models import Movie, Rating, History, Watchlist

def reset_db():
    db = SessionLocal()
    # Clear out user interactions and legacy movies
    db.query(Rating).delete()
    db.query(History).delete()
    db.query(Watchlist).delete()
    
    # Delete manually seeded movies
    db.query(Movie).delete()
    db.commit()
    db.close()
    print("Legacy movies and interactions cleared.")

    # Call the new TMDB API sync endpoint
    url = "http://localhost:8000/api/admin/sync-tmdb"
    data = json.dumps({
        "api_key": "2d11825663306373fbd924fcfb975415",
        "count": 150 # Request a good batch of movies
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        print("TMDb API Sync Response:")
        print(response.read().decode())

if __name__ == "__main__":
    reset_db()
