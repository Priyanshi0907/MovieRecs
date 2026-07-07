import os
import threading
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .database import engine, get_db, Base, SessionLocal, run_lightweight_migrations
from .models import User, Movie, Rating, Watchlist, History, Review
from .auth import get_current_user, verify_password, get_password_hash, create_access_token
from .recommender import train_recommender, get_similar_movies, get_hybrid_recommendations, explain_recommendation, compute_missing_embeddings
from .ai import generate_ai_summary, generate_ai_review_analysis, handle_chatbot_query
from .seed import seed_database
from .tmdb import (
    sync_movies_from_tmdb,
    search_tmdb_movies,
    fetch_tmdb_movie_by_id,
    lazy_load_movie_details,
    backfill_missing_posters,
    repair_broken_posters,
)

# Add any new columns to existing tables (e.g. Movie.embedding) BEFORE
# create_all, since create_all only creates missing tables, not missing
# columns on tables that already exist.
run_lightweight_migrations()

# Initialize DB Tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini-Netflix AI Recommendation API")

# Setup CORS middleware. Deployment-ready: reads allowed origins from an env
# var (comma-separated) so production can lock this down to the real frontend
# domain instead of "*". Defaults to "*" for local development convenience.
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "*")
_cors_origins = ["*"] if _cors_origins_env.strip() == "*" else [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Simple liveness/readiness endpoint for deployment platforms (Render, Railway, etc.)."""
    return {"status": "ok"}


# Startup event to train models and seed if empty
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        movie_count = db.query(Movie).count()
        if movie_count == 0:
            print("Database empty. Seeding database...")
            seed_database()
        # Initial training of content-based matrices and SVD
        train_recommender(db)
    except Exception as e:
        print(f"Error on startup: {e}")
    finally:
        db.close()

    # Repair any movies left with missing posters, and backfill any movies
    # missing a cached semantic embedding - both as genuinely non-blocking
    # background threads, NOT inside this function's synchronous body. This
    # event must return quickly or the whole app stays stuck "starting up"
    # and every request hangs until it's done (this exact mistake was made
    # and fixed earlier - do not reintroduce it).
    api_key = os.getenv("TMDB_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        def _run_startup_backfill():
            bg_db = SessionLocal()
            try:
                result = backfill_missing_posters(bg_db, api_key)
                print(f"Startup poster backfill: fixed {result['fixed_count']}, "
                      f"unresolved {result['unresolved_count']}")
            except Exception as e:
                print(f"Startup poster backfill failed: {e}")
            finally:
                bg_db.close()

        threading.Thread(target=_run_startup_backfill, daemon=True).start()

    if gemini_key:
        def _run_startup_embedding_backfill():
            bg_db = SessionLocal()
            try:
                result = compute_missing_embeddings(bg_db, limit=200)
                print(f"Startup embedding backfill: {result}")
                # Reload the recommender so newly-embedded movies are usable
                # immediately instead of waiting for the next natural retrain.
                train_recommender(bg_db)
            except Exception as e:
                print(f"Startup embedding backfill failed: {e}")
            finally:
                bg_db.close()

        threading.Thread(target=_run_startup_embedding_backfill, daemon=True).start()


# Pydantic Schemas
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class QuestionnaireUpdate(BaseModel):
    genres: List[str]
    languages: List[str]
    actors: List[str]
    directors: List[str]
    runtime: str
    mood: str
    age: Optional[int] = None
    region: Optional[str] = None

class RatingSubmit(BaseModel):
    rating: float # 1 to 5

class ReviewSubmit(BaseModel):
    content: str

class ActionSubmit(BaseModel):
    action: str # "liked", "disliked", "watched", "viewed"

class ChatQuery(BaseModel):
    query: str

class MovieCreate(BaseModel):
    title: str
    genres: List[str]
    overview: str
    cast: List[str]
    director: str
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    runtime: int
    vote_average: float
    popularity: float
    release_date: str
    budget: Optional[int] = 0
    revenue: Optional[int] = 0
    youtube_trailer_id: Optional[str] = None
    streaming_platforms: List[str] = []
    languages: List[str] = []
    awards: List[str] = []
    country: Optional[str] = None

class TmdbSyncRequest(BaseModel):
    api_key: Optional[str] = None
    count: Optional[int] = 100

class TmdbIngestRequest(BaseModel):
    api_key: Optional[str] = None
    tmdb_id: int

class MovieFilterRequest(BaseModel):
    genres: Optional[List[str]] = []
    mood: Optional[str] = None
    language: Optional[str] = None
    runtime: Optional[str] = None
    min_rating: Optional[float] = 0.0
    era: Optional[str] = None
    sort_by: Optional[str] = "Recommended"


# --- AUTHENTICATION ENDPOINTS ---

@app.post("/api/auth/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "genres": user.preferred_genres,
            "mood": user.preferred_mood
        }
    }

@app.post("/api/auth/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
        
    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "genres": user.preferred_genres,
            "mood": user.preferred_mood
        }
    }

@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "genres": user.preferred_genres,
        "languages": user.preferred_languages,
        "actors": user.preferred_actors,
        "directors": user.preferred_directors,
        "runtime": user.preferred_runtime,
        "mood": user.preferred_mood,
        "age": user.age,
        "region": user.region,
        "is_guest": user.email == "guest@netflix.com"
    }


# --- USER PROFILE & QUESTIONNAIRE ---

@app.post("/api/user/questionnaire")
def submit_questionnaire(
    q: QuestionnaireUpdate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user.preferred_genres = q.genres
    user.preferred_languages = q.languages
    user.preferred_actors = q.actors
    user.preferred_directors = q.directors
    user.preferred_runtime = q.runtime
    user.preferred_mood = q.mood
    if q.age is not None:
        user.age = q.age
    if q.region is not None:
        user.region = q.region
        
    db.commit()
    
    # Retrain recommender model asynchronously because user features updated
    background_tasks.add_task(train_recommender, db)
    
    return {"message": "Preferences updated successfully", "user": {"name": user.name, "mood": user.preferred_mood}}


# --- MOVIES & RECOMMENDATION ENGINE ---


@app.post("/api/movies/ingest")
def ingest_movie_tmdb(req: TmdbIngestRequest, background_tasks: BackgroundTasks):
    """
    Ingests a single movie from TMDb into the local database.
    """
    api_key = req.api_key or os.getenv("TMDB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="TMDb API key is required")
    db = SessionLocal()
    try:
        movie = fetch_tmdb_movie_by_id(db, req.tmdb_id, api_key)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found on TMDb")
        movie_id = movie.id
    finally:
        db.close()
        
    def _retrain_recommender():
        retrain_db = SessionLocal()
        try:
            train_recommender(retrain_db)
        finally:
            retrain_db.close()
            
    background_tasks.add_task(_retrain_recommender)
    return {"message": "Movie ingested successfully", "movie_id": movie_id}

@app.get("/api/movies/sections")
def get_movie_sections(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns lists of movies structured in typical Netflix home screen rows.
    """
    # 1. Recommended row (Hybrid or Cold-start based on rating count)
    recommended_raw = get_hybrid_recommendations(user.id, db, limit=12)
    recommended = []
    for m in recommended_raw:
        m_dict = {
            "id": m.id,
            "title": m.title,
            "genres": m.genres,
            "overview": m.overview,
            "cast": m.cast,
            "director": m.director,
            "poster_path": m.poster_path,
            "backdrop_path": m.backdrop_path,
            "runtime": m.runtime,
            "vote_average": m.vote_average,
            "popularity": m.popularity,
            "release_date": m.release_date,
            "youtube_trailer_id": m.youtube_trailer_id,
            "streaming_platforms": m.streaming_platforms,
            "languages": m.languages,
            "awards": m.awards,
            "country": m.country,
            "explanation": explain_recommendation(user.id, m, db)
        }
        recommended.append(m_dict)
    
    # 2. Trending row (by popularity descending)
    trending = db.query(Movie).order_by(Movie.popularity.desc()).limit(12).all()
    
    # 3. Critically Acclaimed (by rating descending)
    critically_acclaimed = db.query(Movie).order_by(Movie.vote_average.desc()).limit(12).all()
    
    # 4. Because you watched (find user's highest rated movie, list similar movies)
    because_watched_title = ""
    because_watched_movies = []
    
    highest_rated = db.query(Rating).filter(Rating.user_id == user.id, Rating.rating >= 4.0).order_by(Rating.rating.desc()).first()
    if highest_rated:
        ref_movie = db.query(Movie).filter(Movie.id == highest_rated.movie_id).first()
        if ref_movie:
            because_watched_title = f"Because you watched {ref_movie.title}"
            because_watched_movies = get_similar_movies(ref_movie.id, db, limit=12)
            
    # Default fallback if they haven't liked any movie yet
    if not because_watched_movies:
        # Pick a famous seeded movie like Interstellar
        famous_movie = db.query(Movie).filter(Movie.title == "Interstellar").first()
        if famous_movie:
            because_watched_title = f"Because you liked {famous_movie.title}"
            because_watched_movies = get_similar_movies(famous_movie.id, db, limit=12)
            
    # 5. Sci-Fi/Action or customized genre row
    fav_genre = user.preferred_genres[0] if user.preferred_genres else "Action"
    genre_movies = db.query(Movie).filter(Movie.genres.like(f'%"{fav_genre}"%')).limit(12).all()
    # Alternate simple search if JSON storage uses flat serialization
    if not genre_movies:
        genre_movies = db.query(Movie).filter(Movie.genres.like(f'%{fav_genre}%')).limit(12).all()

    # 6. Mood-based recommendations
    mood_genres = {
        "Happy": "Comedy",
        "Sad": "Drama",
        "Mind-bending": "Sci-Fi",
        "Feel-good": "Romance",
        "Dark": "Thriller",
        "Family": "Fantasy"
    }
    mood_mapped_genre = mood_genres.get(user.preferred_mood, "Drama")
    mood_movies = db.query(Movie).filter(Movie.genres.like(f'%{mood_mapped_genre}%')).order_by(Movie.popularity.desc()).limit(12).all()

    # 7. Hidden Gems (High rating, lower popularity / lesser known)
    hidden_gems = db.query(Movie).filter(Movie.vote_average >= 7.5, Movie.popularity < 120.0).order_by(Movie.vote_average.desc()).limit(12).all()

    # 8. Continue Watching / History (Only movies marked as "Watching" in Watchlist)
    continue_watching = []
    watching_items = db.query(Watchlist).filter(Watchlist.user_id == user.id, Watchlist.status == "Watching").all()
    if watching_items:
        m_ids = [item.movie_id for item in watching_items]
        movies_in_watch = db.query(Movie).filter(Movie.id.in_(m_ids)).all()
        movies_lookup = {m.id: m for m in movies_in_watch}
        
        seen_titles = set()
        for item in watching_items:
            if item.movie_id in movies_lookup:
                m = movies_lookup[item.movie_id]
                title_lower = m.title.lower().strip()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    continue_watching.append(m)
                    if len(continue_watching) >= 6:
                        break

    return {
        "hero_movie": trending[0] if trending else None,
        "sections": [
            {"title": "Continue Watching", "movies": continue_watching} if continue_watching else None,
            {"title": "Recommended For You", "movies": recommended, "type": "hybrid"},
            {"title": f"Mood Boosters ({user.preferred_mood})", "movies": mood_movies},
            {"title": because_watched_title, "movies": because_watched_movies} if because_watched_title else None,
            {"title": "Trending Today", "movies": trending},
            {"title": f"Best in {fav_genre}", "movies": genre_movies},
            {"title": "Critically Acclaimed", "movies": critically_acclaimed},
            {"title": "Hidden Gems", "movies": hidden_gems}
        ]
    }

MOOD_KEYWORDS = {
    "Happy": ["comedy", "funny", "laugh", "humor", "hilarious", "cheerful", "lighthearted", "sweet", "fun", "joke", "romantic comedy", "rom-com", "musical", "joy", "happy", "amusing", "silly", "upbeat", "whimsical", "warm", "delight", "pleasant", "good-natured"],
    "Sad": ["drama", "sad", "tragic", "tragedy", "emotional", "cry", "tear", "grief", "loss", "death", "die", "heartbreak", "heartbreaking", "melancholy", "pain", "sorrow", "depressing", "gloomy", "mourn", "mourning", "misfortune", "struggle", "devastating", "touching", "somber"],
    "Mind-bending": ["mind-bending", "twist", "psychological", "reality", "dream", "dimension", "space-time", "illusion", "mystery", "conspiracy", "puzzle", "existential", "surreal", "paradox", "quantum", "subconscious", "memory", "hallucination", "maze", "labyrinth", "inception"],
    "Feel-good": ["heartwarming", "feel-good", "inspiring", "inspiration", "inspirational", "uplifting", "charming", "sweet", "friendship", "triumph", "hope", "love", "smile", "cheer", "tender", "family", "comforting", "positive", "enthusiasm", "kindness"],
    "Dark": ["dark", "sinister", "murder", "killer", "crime", "thriller", "noir", "gritty", "shadowy", "conspiracy", "blood", "death", "revenge", "detective", "suspense", "morbid", "macabre", "gothic", "vampire", "evil", "demon", "serial", "haunted", "terrifying", "scary", "horror"],
    "Family": ["family", "child", "children", "kids", "magic", "adventure", "fantasy", "friendship", "animated", "animation", "school", "pet", "dog", "fairy", "youth", "boyhood", "girlhood", "parent", "toy", "wonder"]
}

def movie_matches_mood(movie: Movie, mood: str, selected_genres: List[str] = None) -> bool:
    if not mood or mood == "Any":
        return True
        
    mood_genres = {
        "Happy": ["Comedy", "Romance", "Music"],
        "Sad": ["Drama", "Romance"],
        "Mind-bending": ["Sci-Fi", "Thriller", "Mystery"],
        "Feel-good": ["Comedy", "Drama", "Romance"],
        "Dark": ["Crime", "Thriller", "Mystery", "Horror"],
        "Family": ["Fantasy", "Adventure", "Animation", "Comedy"]
    }
    
    mapped_genres = mood_genres.get(mood, [])
    if not mapped_genres:
        return True
        
    movie_genre_list = movie.genres if isinstance(movie.genres, list) else []
    
    # We check overlap of explicitly selected genres with mapped genres
    # If the user has selected a genre like Romance and also a mood like Happy,
    # the overlap is Romance. We want the movie to ALSO match other Happy aspects:
    # 1) Having Comedy or Music (other mapped genres)
    # 2) Or having some happy keywords in overview/title
    overlap = set(selected_genres or []).intersection(set(mapped_genres))
    
    if overlap:
        other_mapped_genres = [g for g in mapped_genres if g not in overlap]
        genre_match = any(g in movie_genre_list for g in other_mapped_genres)
    else:
        genre_match = any(g in movie_genre_list for g in mapped_genres)
        
    # Check keyword-based match
    keyword_match = False
    keywords = MOOD_KEYWORDS.get(mood, [])
    text_to_search = f"{movie.title} {movie.overview or ''} {' '.join(movie_genre_list)}".lower()
    for kw in keywords:
        if kw in text_to_search:
            keyword_match = True
            break
            
    return genre_match or keyword_match

@app.post("/api/movies/filter")
def filter_movies(
    req: MovieFilterRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    
    # 1. Filter by genres (All selected genres must match)
    if req.genres:
        for genre in req.genres:
            query = query.filter(Movie.genres.like(f'%"{genre}"%') | Movie.genres.like(f'%{genre}%'))
            
    # 2. Mood filter is processed in Python after loading the query results to enable cohesive intersection.
            
    # 3. Filter by language
    if req.language and req.language != "Any":
        lang_code_map = {
            "English": "en",
            "Japanese": "ja",
            "French": "fr",
            "Spanish": "es",
            "Korean": "ko"
        }
        lang_code = lang_code_map.get(req.language, "en")
        query = query.filter(Movie.languages.like(f'%"{lang_code}"%') | Movie.languages.like(f'%{lang_code}%'))
        
    # 4. Filter by runtime
    if req.runtime and req.runtime != "Any":
        if req.runtime == "Under 90 mins":
            query = query.filter(Movie.runtime < 90)
        elif req.runtime == "90-120 mins":
            query = query.filter(Movie.runtime >= 90, Movie.runtime <= 120)
        elif req.runtime == "Over 2 hours":
            query = query.filter(Movie.runtime > 120)
            
    # 5. Filter by rating
    if req.min_rating and req.min_rating > 0:
        query = query.filter(Movie.vote_average >= req.min_rating)
        
    # 6. Filter by release era
    if req.era and req.era != "Any":
        if req.era == "2020s":
            query = query.filter(Movie.release_date >= "2020-01-01")
        elif req.era == "2010s":
            query = query.filter(Movie.release_date >= "2010-01-01", Movie.release_date <= "2019-12-31")
        elif req.era == "2000s":
            query = query.filter(Movie.release_date >= "2000-01-01", Movie.release_date <= "2009-12-31")
        elif req.era == "90s & older":
            query = query.filter(Movie.release_date <= "1999-12-31")
            
    movies = query.all()
    
    # 2. Python-based mood filter (Cohesive Intersection)
    if req.mood and req.mood != "Any":
        movies = [m for m in movies if movie_matches_mood(m, req.mood, req.genres)]
    
    # 7. Apply sorting
    if req.sort_by == "Recommended":
        import numpy as np
        from .recommender import _svd_model, _cosine_sim, _movie_id_map
        user_ratings = db.query(Rating).filter(Rating.user_id == user.id).all()
        liked_ratings = [r for r in user_ratings if r.rating >= 3.5]
        liked_movie_ids = {r.movie_id for r in liked_ratings}
        
        content_scores = {}
        for m in movies:
            if m.id not in _movie_id_map:
                content_scores[m.id] = 0.0
                continue
            m_idx = _movie_id_map[m.id]
            sims = [
                _cosine_sim[m_idx][_movie_id_map[liked_id]] 
                for liked_id in liked_movie_ids 
                if liked_id in _movie_id_map
            ]
            content_scores[m.id] = np.mean(sims) if sims else 0.0
            
        c_vals = list(content_scores.values())
        if c_vals and max(c_vals) > min(c_vals):
            max_c, min_c = max(c_vals), min(c_vals)
            content_scores = {mid: (val - min_c) / (max_c - min_c) for mid, val in content_scores.items()}
        else:
            content_scores = {mid: 0.5 for mid in content_scores}
            
        scored_movies = []
        for m in movies:
            collab_score = (_svd_model.predict(user.id, m.id) - 1.0) / 4.0 if _svd_model else 0.5
            content_score = content_scores.get(m.id, 0.5)
            pref_score = 0.5 if set(user.preferred_genres or []).intersection(set(m.genres or [])) else 0.0
            global_score = 0.4 * min(1.0, (m.popularity or 50.0) / 500.0) + 0.6 * ((m.vote_average or 7.0) / 10.0)
            score = 0.35 * collab_score + 0.35 * content_score + 0.20 * pref_score + 0.10 * global_score
            scored_movies.append((m, score))
            
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        movies = [sm[0] for sm in scored_movies]
    elif req.sort_by == "Rating":
        movies.sort(key=lambda x: x.vote_average or 0.0, reverse=True)
    elif req.sort_by == "Popularity":
        movies.sort(key=lambda x: x.popularity or 0.0, reverse=True)
    elif req.sort_by == "Release Date":
        movies.sort(key=lambda x: x.release_date or "", reverse=True)
        
    serialized = []
    for m in movies:
        explanation = "Matches your taste criteria."
        if req.sort_by == "Recommended":
            from .recommender import explain_recommendation
            explanation = explain_recommendation(user.id, m, db)
            
        serialized.append({
            "id": m.id,
            "title": m.title,
            "genres": m.genres,
            "overview": m.overview,
            "cast": m.cast,
            "director": m.director,
            "poster_path": m.poster_path,
            "backdrop_path": m.backdrop_path,
            "runtime": m.runtime,
            "vote_average": m.vote_average,
            "popularity": m.popularity,
            "release_date": m.release_date,
            "youtube_trailer_id": m.youtube_trailer_id,
            "explanation": explanation
        })
        
    return serialized

@app.get("/api/movies/search")
def search_movies(q: str, api_key: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Handles autocomplete searches and filters by title, actor, director, genre, etc.
    Also queries TMDb if an api_key is provided to support lazy loading sync.
    """
    if not q or len(q) < 2:
        return []
        
    query_pattern = f"%{q}%"
    
    # Query database
    local_results = db.query(Movie).filter(
        (Movie.title.like(query_pattern)) | 
        (Movie.director.like(query_pattern)) |
        (Movie.genres.like(query_pattern)) |
        (Movie.cast.like(query_pattern))
    ).limit(10).all()
    
    results = []
    # We serialize local results manually to include the is_local flag
    for m in local_results:
        results.append({
            "id": m.id,
            "title": m.title,
            "poster_path": m.poster_path,
            "director": m.director,
            "genres": m.genres,
            "vote_average": m.vote_average,
            "release_date": m.release_date,
            "is_local": True
        })
        
    resolved_api_key = api_key or os.getenv("TMDB_API_KEY")
    if resolved_api_key:
        try:
            tmdb_results = search_tmdb_movies(resolved_api_key, q)
            # Avoid duplicate movies if they are already in the database
            local_titles = {m["title"].lower() for m in results}
            for r in tmdb_results:
                if r["title"].lower() not in local_titles:
                    results.append({
                        "tmdb_id": r["tmdb_id"],
                        "title": r["title"],
                        "poster_path": r["poster_path"],
                        "release_date": r["release_date"],
                        "is_local": False
                    })
        except Exception as e:
            print(f"Error querying TMDb during search: {e}")
            
    return results[:15]

@app.get("/api/movies/{movie_id}")
def get_movie_detail(movie_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # Lazy load details (cast, director, trailer, runtime, etc.) from TMDB on-demand
    api_key = os.getenv("TMDB_API_KEY")
    if api_key and movie.tmdb_id:
        movie = lazy_load_movie_details(db, movie, api_key)
        
    # Generate AI Hook summary
    ai_hook = generate_ai_summary(movie.title, movie.overview)
    
    # Generate AI Review Highlights
    ai_reviews = generate_ai_review_analysis(movie.title, movie.genres, movie.director)
    
    # Explain why recommended
    explanation = explain_recommendation(user.id, movie, db)
    
    # Check current status in user watchlist/ratings
    watchlist_item = db.query(Watchlist).filter_by(user_id=user.id, movie_id=movie_id).first()
    user_rating = db.query(Rating).filter_by(user_id=user.id, movie_id=movie_id).first()
    
    liked_record = db.query(History).filter(
        History.user_id == user.id,
        History.movie_id == movie_id,
        History.action.in_(["liked", "disliked"])
    ).order_by(History.timestamp.desc()).first()
    
    user_liked = liked_record.action == "liked" if liked_record else False
    user_disliked = liked_record.action == "disliked" if liked_record else False
    
    # Fetch reviews
    reviews_list = db.query(Review).filter(Review.movie_id == movie_id).order_by(Review.timestamp.desc()).all()
    user_ids = {r.user_id for r in reviews_list}
    user_lookup = {u.id: u.name for u in db.query(User).filter(User.id.in_(user_ids)).all()}
    
    serialized_reviews = [{
        "id": r.id,
        "user_name": user_lookup.get(r.user_id, "Anonymous"),
        "content": r.content,
        "timestamp": r.timestamp
    } for r in reviews_list]
    
    # Recommendation: Similar Movies
    similar = get_similar_movies(movie.id, db, limit=10)
    
    return {
        "movie": movie,
        "ai_summary": ai_hook,
        "ai_reviews": ai_reviews,
        "explanation": explanation,
        "watchlist_status": watchlist_item.status if watchlist_item else None,
        "user_rating": user_rating.rating if user_rating else None,
        "user_liked": user_liked,
        "user_disliked": user_disliked,
        "similar_movies": similar,
        "reviews": serialized_reviews
    }


# --- USER ACTIONS & RECORD UPDATES ---

@app.post("/api/movies/{movie_id}/action")
def register_movie_action(
    movie_id: int,
    act: ActionSubmit,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # 1. Store action history
    h = History(user_id=user.id, movie_id=movie_id, action=act.action)
    db.add(h)
    db.commit()
    
    # 2. Retrain model in background if liked/disliked
    if act.action in ["liked", "disliked"]:
        background_tasks.add_task(train_recommender, db)
        
    return {"message": f"Action '{act.action}' recorded successfully"}

@app.post("/api/movies/{movie_id}/rate")
def rate_movie(
    movie_id: int,
    r_in: RatingSubmit,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # Register/Update rating
    rating = db.query(Rating).filter_by(user_id=user.id, movie_id=movie_id).first()
    if rating:
        rating.rating = r_in.rating
    else:
        rating = Rating(user_id=user.id, movie_id=movie_id, rating=r_in.rating)
        db.add(rating)
        
    # Also record history
    db.add(History(user_id=user.id, movie_id=movie_id, action="watched" if r_in.rating >= 3.0 else "viewed"))
    db.commit()
    
    # Retrain collaborative model
    background_tasks.add_task(train_recommender, db)
    
    return {"message": "Rating recorded successfully", "rating": r_in.rating}

@app.post("/api/movies/{movie_id}/watchlist")
def toggle_watchlist(
    movie_id: int,
    status_in: ActionSubmit, # Used to send "status" like "Want to Watch", "Watching", "Completed", "Dropped"
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    item = db.query(Watchlist).filter_by(user_id=user.id, movie_id=movie_id).first()
    if item:
        if status_in.action == "remove":
            db.delete(item)
            msg = "Removed from Watchlist"
        else:
            item.status = status_in.action
            msg = f"Watchlist status updated to: {status_in.action}"
    else:
        if status_in.action != "remove":
            db.add(Watchlist(user_id=user.id, movie_id=movie_id, status=status_in.action))
            msg = f"Added to Watchlist as: {status_in.action}"
        else:
            msg = "Nothing to remove"
            
    db.commit()
    return {"message": msg}

@app.get("/api/watchlist")
def get_user_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Watchlist).filter(Watchlist.user_id == user.id).all()
    if not items:
        return []
        
    m_ids = [item.movie_id for item in items]
    status_map = {item.movie_id: item.status for item in items}
    
    movies = db.query(Movie).filter(Movie.id.in_(m_ids)).all()
    return [{
        "movie": m,
        "status": status_map[m.id]
    } for m in movies]

@app.get("/api/history")
def get_user_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(History).filter(History.user_id == user.id).order_by(History.timestamp.desc()).limit(30).all()
    if not records:
        return []
        
    m_ids = list({h.movie_id for h in records})
    movies_lookup = {m.id: m for m in db.query(Movie).filter(Movie.id.in_(m_ids)).all()}
    
    return [{
        "movie_title": movies_lookup[h.movie_id].title if h.movie_id in movies_lookup else "Unknown",
        "movie_id": h.movie_id,
        "action": h.action,
        "timestamp": h.timestamp
    } for h in records]

@app.post("/api/movies/{movie_id}/reviews")
def post_movie_review(
    movie_id: int,
    rev_in: ReviewSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not rev_in.content.strip():
        raise HTTPException(status_code=400, detail="Review content cannot be empty")
        
    review = Review(user_id=user.id, movie_id=movie_id, content=rev_in.content)
    db.add(review)
    db.commit()
    db.refresh(review)
    
    return {
        "id": review.id,
        "user_name": user.name,
        "content": review.content,
        "timestamp": review.timestamp
    }


# --- AI CHATBOT ---

@app.post("/api/chatbot")
def chatbot(chat_in: ChatQuery, db: Session = Depends(get_db)):
    if not chat_in.query:
        raise HTTPException(status_code=400, detail="Empty query")
    return handle_chatbot_query(chat_in.query, db)


# --- ANALYTICS DASHBOARD ---

@app.get("/api/analytics")
def get_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Generates statistics for the user analytics page (favorite genres, releases per year,
    genre distributions, timeline watch counts).
    """
    ratings = db.query(Rating).filter(Rating.user_id == user.id).all()

    # Fallback to the Guest account's stats if the current user hasn't rated
    # enough yet, so the dashboard isn't empty on a fresh account. This is now
    # looked up by email rather than a hardcoded user_id == 2, and the response
    # tells the frontend it happened (used_fallback_data) instead of silently
    # showing someone else's data with no indication.
    used_fallback_data = False
    activity_user_id = user.id

    if len(ratings) < 5:
        guest = db.query(User).filter(User.email == "guest@netflix.com").first()
        if guest and guest.id != user.id:
            fallback_ratings = db.query(Rating).filter(Rating.user_id == guest.id).all()
            if fallback_ratings:
                ratings = fallback_ratings
                activity_user_id = guest.id
                used_fallback_data = True

    if not ratings:
        return {"error": "Insufficient watch data to build analytics dashboard."}

    m_ids = [r.movie_id for r in ratings]
    r_map = {r.movie_id: r.rating for r in ratings}

    movies = db.query(Movie).filter(Movie.id.in_(m_ids)).all()

    # 1. Favorite Genres count & average ratings
    genre_data = {}
    year_data = {}

    for m in movies:
        rating_val = r_map.get(m.id, 3.5)
        # Genres
        for g in m.genres:
            if g not in genre_data:
                genre_data[g] = {"count": 0, "rating_sum": 0.0}
            genre_data[g]["count"] += 1
            genre_data[g]["rating_sum"] += rating_val

        # Years
        if m.release_date:
            year = m.release_date.split("-")[0]
            if year not in year_data:
                year_data[year] = 0
            year_data[year] += 1

    # Format Favorite Genres (Pie Chart)
    pie_genres = [{"name": g, "value": data["count"]} for g, data in genre_data.items()]
    pie_genres = sorted(pie_genres, key=lambda x: x["value"], reverse=True)[:6]

    # Format Genre distribution (Radar Chart)
    radar_genres = [{
        "subject": g,
        "A": data["count"],
        "fullMark": max([d["count"] for d in genre_data.values()])
    } for g, data in genre_data.items()]

    # Format Movies per Year (Bar Graph)
    bar_years = [{"year": yr, "count": count} for yr, count in sorted(year_data.items())]

    # Format Activity Timeline (Watch counts over months) - derived from REAL
    # History rows for this user (or the fallback user), grouped by calendar
    # month. This replaces the previous hardcoded placeholder numbers. Note:
    # if all of this user's History rows were created in one seeding pass,
    # they'll share nearly the same timestamp and the chart will show a single
    # spike rather than a spread - that's an honest reflection of the
    # underlying data, not a bug. As real activity accumulates over time
    # (ratings, watches) across different days/months, this will naturally
    # spread out.
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_counts = {m: 0 for m in month_order}

    history_records = db.query(History).filter(History.user_id == activity_user_id).all()
    for h in history_records:
        if h.timestamp:
            month_label = h.timestamp.strftime("%b")
            if month_label in month_counts:
                month_counts[month_label] += 1

    activity_months = [{"name": m, "watches": month_counts[m]} for m in month_order]

    avg_rating = sum(r_map.values()) / len(r_map) if r_map else 0.0
    return {
        "favorite_genres": pie_genres,
        "radar_distribution": radar_genres[:8],
        "movies_per_year": bar_years[-10:], # Keep recent 10 years
        "watching_activity": activity_months,
        "total_watched": len(movies),
        "average_rating": round(avg_rating, 1),
        "used_fallback_data": used_fallback_data,
    }

@app.post("/api/admin/sync-tmdb")
def sync_tmdb(req: TmdbSyncRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    api_key = req.api_key or os.getenv("TMDB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="TMDb API key is required")
    try:
        synced_count = sync_movies_from_tmdb(db, api_key, count=req.count)
        train_recommender(db)

        def _run_backfill():
            bg_db = SessionLocal()
            try:
                result = backfill_missing_posters(bg_db, api_key)
                print(f"Post-sync poster backfill: fixed {result['fixed_count']}, "
                      f"unresolved {result['unresolved_count']}")
            finally:
                bg_db.close()

        # Runs after this response is sent - doesn't block the client waiting
        # on what could be dozens of sequential TMDb network calls.
        background_tasks.add_task(_run_backfill)

        return {
            "message": "TMDb sync finished successfully. Poster backfill is running in the background.",
            "count": synced_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TMDb sync failed: {str(e)}")


@app.post("/api/admin/backfill-posters")
def backfill_posters(db: Session = Depends(get_db)):
    """
    One-time repair endpoint: finds movies with a missing poster_path (the ones
    currently rendering with generic stock-photo fallbacks in the UI) and tries
    to resolve real TMDb artwork for them. Returns which titles were fixed and
    which remain unresolved (likely fictional/test entries worth deleting manually).
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="TMDb API key is required")
    try:
        result = backfill_missing_posters(db, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Poster backfill failed: {str(e)}")


@app.post("/api/admin/repair-broken-posters")
def repair_posters(limit: int = 50, db: Session = Depends(get_db)):
    """
    Different from /backfill-posters above: that one only catches poster_path
    IS NULL. This one validates that EXISTING poster paths actually resolve to
    a real image and repairs any that 404 - catching hand-typed/guessed poster
    hashes (e.g. from early hardcoded seed data) that look set but are wrong.
    Checks up to `limit` movies per call since it does a network check per
    movie; call it multiple times (increasing an offset, or just re-running)
    to work through a large catalog.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="TMDb API key is required")
    try:
        result = repair_broken_posters(db, api_key, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Poster repair failed: {str(e)}")


@app.post("/api/admin/backfill-embeddings")
def backfill_embeddings(limit: int = 100, background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    """
    Computes and caches semantic embeddings for any movies that don't have one
    yet (Movie.embedding IS NULL) - this is what powers accurate chatbot
    search and content-based recommendations. Run this after a big TMDb sync
    (which adds many un-embedded movies at once), or anytime to incrementally
    work through a large catalog. Bounded by `limit` per call since it makes
    one Gemini API call per movie.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is required to compute embeddings")
    try:
        result = compute_missing_embeddings(db, limit=limit)
        train_recommender(db)  # reload so newly-embedded movies are usable immediately
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding backfill failed: {str(e)}")