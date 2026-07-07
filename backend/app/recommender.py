import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from .models import Movie, Rating, User, Watchlist

try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    genai = None
    GEMINI_API_KEY = ""

EMBEDDING_MODEL = "models/gemini-embedding-001"

# Global Cache for Recommender Data
_tfidf_matrix = None
_cosine_sim = None
_movie_id_map = {} # Maps movie_id to index in tfidf matrix
_index_movie_map = {} # Maps index in tfidf matrix to movie_id
_svd_model = None

# Semantic embedding cache (parallel structure to the TF-IDF one above).
# Reuses the SAME _movie_id_map / _index_movie_map indices so a row index
# means the same movie in both matrices.
_embedding_matrix = None      # numpy array, shape (n_movies, embedding_dim)
_embedding_cosine_sim = None  # precomputed cosine similarity, same shape as _cosine_sim

# Placeholder values written by tmdb.py's lightweight ingestion path when real
# data wasn't fetched. These must never be treated as real content signal.
_PLACEHOLDER_VALUES = {"unknown director", "unknown", "", "none", "n/a"}


def _clean_placeholder_field(value: str) -> str:
    """Returns '' for missing/placeholder field values, otherwise the value unchanged."""
    if not value or value.strip().lower() in _PLACEHOLDER_VALUES:
        return ""
    return value


def build_movie_embedding_text(m: Movie) -> str:
    """
    Builds the natural-language description of a movie that gets embedded.
    Unlike the TF-IDF 'soup' (which is just concatenated tokens), this reads
    as an actual sentence, which matters for embedding quality since the
    model is trained on natural language, not keyword bags.
    """
    genres = ", ".join(m.genres) if isinstance(m.genres, list) else ""
    cast_list = [c for c in (m.cast or []) if c][:4]
    director = _clean_placeholder_field(m.director)

    parts = [f"{m.title}."]
    if genres:
        parts.append(f"Genres: {genres}.")
    if m.overview:
        parts.append(m.overview.strip())
    if director:
        parts.append(f"Directed by {director}.")
    if cast_list:
        parts.append(f"Starring {', '.join(cast_list)}.")
    return " ".join(parts)


def embed_text(text: str, task_type: str = "retrieval_document"):
    """
    Calls Gemini's embedding model. task_type should be "retrieval_document"
    when embedding a movie (goes into the searchable index) and
    "retrieval_query" when embedding a user's chatbot query (what we search
    WITH) - Gemini's embedding model is trained asymmetrically for these two
    roles, so using the right one matters for match quality.
    Returns None (never raises) if Gemini isn't configured or the call fails,
    so every caller can gracefully fall back to TF-IDF.
    """
    if not GEMINI_API_KEY or not genai or not text:
        return None
    try:
        result = genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type=task_type)
        return result.get("embedding")
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def compute_missing_embeddings(db: Session, limit: int = 100, max_api_calls: int = 100) -> dict:
    """
    Computes and caches embeddings ONLY for movies that don't already have one
    (Movie.embedding IS NULL). This is the expensive, network-bound operation -
    NEVER call this from inside train_recommender() or any request/startup
    path that needs to stay fast; run it as a background task instead (see
    main.py), same lesson learned from the poster backfill blocking-startup
    incident. Bounded by `limit`/`max_api_calls` so repeated calls
    incrementally work through a large catalog instead of one huge call.
    """
    if not GEMINI_API_KEY:
        return {"embedded": 0, "skipped_no_key": True}

    candidates = db.query(Movie).filter(Movie.embedding.is_(None)).limit(limit).all()
    embedded = 0
    api_calls = 0

    for movie in candidates:
        if api_calls >= max_api_calls:
            break
        text = build_movie_embedding_text(movie)
        vector = embed_text(text, task_type="retrieval_document")
        api_calls += 1
        if vector:
            movie.embedding = vector
            db.commit()
            embedded += 1
        else:
            db.rollback()

    print(f"Embedding backfill: {embedded}/{len(candidates)} movies embedded this pass ({api_calls} API calls).")
    return {"embedded": embedded, "checked": len(candidates), "api_calls": api_calls}

class CustomSVD:
    def __init__(self, n_factors=15, lr=0.005, reg=0.02, n_epochs=25):
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.n_epochs = n_epochs
        
        self.mu = 3.5
        self.b_u = {}
        self.b_i = {}
        self.P = {}
        self.Q = {}
        
    def fit(self, ratings_df):
        if ratings_df.empty:
            return
            
        self.mu = float(ratings_df['rating'].mean())
        
        users = ratings_df['user_id'].unique()
        items = ratings_df['movie_id'].unique()
        
        # Initialize biases to 0
        self.b_u = {u: 0.0 for u in users}
        self.b_i = {i: 0.0 for i in items}
        
        # Initialize user/item matrices randomly
        np.random.seed(42)
        self.P = {u: np.random.normal(0, 0.1, self.n_factors) for u in users}
        self.Q = {i: np.random.normal(0, 0.1, self.n_factors) for i in items}
        
        # Stochastic Gradient Descent (SGD)
        for epoch in range(self.n_epochs):
            for _, row in ratings_df.iterrows():
                u = int(row['user_id'])
                i = int(row['movie_id'])
                r = float(row['rating'])
                
                # Predict
                pred = self.mu + self.b_u.get(u, 0.0) + self.b_i.get(i, 0.0) + np.dot(self.P.get(u, np.zeros(self.n_factors)), self.Q.get(i, np.zeros(self.n_factors)))
                err = r - pred
                
                # Update biases
                self.b_u[u] += self.lr * (err - self.reg * self.b_u[u])
                self.b_i[i] += self.lr * (err - self.reg * self.b_i[i])
                
                # Update matrices P and Q
                p_temp = self.P[u].copy()
                self.P[u] += self.lr * (err * self.Q[i] - self.reg * self.P[u])
                self.Q[i] += self.lr * (err * p_temp - self.reg * self.Q[i])
                
    def predict(self, user_id, movie_id):
        b_u_val = self.b_u.get(user_id, 0.0)
        b_i_val = self.b_i.get(movie_id, 0.0)
        
        p_u = self.P.get(user_id, None)
        q_i = self.Q.get(movie_id, None)
        
        if p_u is not None and q_i is not None:
            interaction = np.dot(p_u, q_i)
        else:
            interaction = 0.0
            
        pred = self.mu + b_u_val + b_i_val + interaction
        return max(1.0, min(5.0, float(pred)))


def train_recommender(db: Session):
    """
    Trains/builds the TF-IDF similarity matrix and fits the SVD model on user ratings.
    Should be called at server startup and whenever major data changes.

    Also LOADS (never computes) any cached semantic embeddings into an aligned
    similarity matrix. Computing embeddings requires a network call per movie,
    so it must never happen here - this function needs to stay fast since it's
    called synchronously after nearly every user action (rating, questionnaire
    update, etc). Embeddings are computed separately and incrementally by
    compute_missing_embeddings(), run as a background task.
    """
    global _tfidf_matrix, _cosine_sim, _movie_id_map, _index_movie_map, _svd_model
    global _embedding_matrix, _embedding_cosine_sim
    
    # 1. Train Content-Based TF-IDF Matrix
    movies = db.query(Movie).all()
    if not movies:
        return
        
    df_movies = pd.DataFrame([{
        'id': m.id,
        'title': m.title,
        'genres': " ".join(m.genres) if isinstance(m.genres, list) else "",
        'overview': m.overview or "",
        'cast': " ".join(m.cast) if isinstance(m.cast, list) else "",
        # Placeholder values like "Unknown Director" must NOT enter the text
        # corpus as real tokens. A huge share of the catalog comes from the
        # lightweight TMDb sync path, which never fetches credits and stores
        # exactly this placeholder string. If left in, every under-detailed
        # movie shares that literal phrase and becomes falsely "similar" to
        # every other under-detailed movie - regardless of actual genre,
        # plot, or cast overlap. This is the root cause behind reference
        # movies returning wildly unrelated, often equally-sparse results.
        'director': _clean_placeholder_field(m.director),
        'embedding': m.embedding
    } for m in movies])
    
    # Create combined soup of features. Genres are repeated to weight them
    # more heavily than free-text overview/cast/director - genre overlap is
    # the most reliable structured similarity signal, especially for movies
    # with thin metadata where overview wording alone is a weak, noisy signal.
    df_movies['soup'] = (
        (df_movies['genres'] + " ") * 3
        + df_movies['overview'] + " "
        + df_movies['cast'] + " "
        + df_movies['director']
    )
    
    tfidf = TfidfVectorizer(stop_words='english', min_df=1)
    _tfidf_matrix = tfidf.fit_transform(df_movies['soup'])
    _cosine_sim = cosine_similarity(_tfidf_matrix, _tfidf_matrix)
    
    _movie_id_map = {row['id']: idx for idx, row in df_movies.iterrows()}
    _index_movie_map = {idx: row['id'] for idx, row in df_movies.iterrows()}

    # Load cached embeddings (read-only, zero API calls). Movies without a
    # cached embedding yet get a zero vector, which cosine_similarity handles
    # safely (zero similarity to everything) rather than crashing - those
    # rows simply won't surface via embedding-based similarity until
    # compute_missing_embeddings() backfills them.
    embeddings_present = df_movies['embedding'].apply(lambda e: isinstance(e, list) and len(e) > 0)
    if embeddings_present.any():
        embedding_dim = len(next(e for e in df_movies['embedding'] if isinstance(e, list) and len(e) > 0))
        embedding_rows = []
        for e in df_movies['embedding']:
            if isinstance(e, list) and len(e) == embedding_dim:
                embedding_rows.append(e)
            else:
                embedding_rows.append([0.0] * embedding_dim)
        _embedding_matrix = np.array(embedding_rows)
        _embedding_cosine_sim = cosine_similarity(_embedding_matrix, _embedding_matrix)
    else:
        _embedding_matrix = None
        _embedding_cosine_sim = None
    
    # 2. Train Collaborative SVD
    ratings = db.query(Rating).all()
    if ratings:
        df_ratings = pd.DataFrame([{
            'user_id': r.user_id,
            'movie_id': r.movie_id,
            'rating': r.rating
        } for r in ratings])
        
        _svd_model = CustomSVD()
        _svd_model.fit(df_ratings)
    else:
        _svd_model = None

    embedded_count = int(embeddings_present.sum())
    print(f"Recommender model trained successfully! ({embedded_count}/{len(movies)} movies have cached embeddings)")


def get_similar_movies(movie_id: int, db: Session, limit: int = 10):
    """
    Retrieves similar movies based on content similarity. Prefers semantic
    embedding similarity when BOTH the source movie and enough of the catalog
    have cached embeddings, since it captures actual meaning (theme, tone,
    plot) rather than literal word/genre overlap - falls back to TF-IDF
    automatically otherwise (no Gemini key configured, or embeddings not yet
    backfilled for this movie).
    """
    global _cosine_sim, _movie_id_map, _index_movie_map, _embedding_cosine_sim
    
    # If not trained, train first
    if _cosine_sim is None or movie_id not in _movie_id_map:
        train_recommender(db)
        
    if movie_id not in _movie_id_map:
        return []
        
    idx = _movie_id_map[movie_id]

    # Use embedding similarity if this specific movie actually has a non-zero
    # embedding row (checking the source row avoids the degenerate case where
    # a zero-vector "no embedding yet" row would otherwise rank everything
    # equally low instead of falling back to TF-IDF).
    use_embeddings = (
        _embedding_cosine_sim is not None
        and _embedding_matrix is not None
        and np.any(_embedding_matrix[idx])
    )
    sim_matrix = _embedding_cosine_sim if use_embeddings else _cosine_sim

    sim_scores = list(enumerate(sim_matrix[idx]))
    # Sort by similarity, skip the first one (itself)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:limit+1]
    
    similar_ids = [_index_movie_map[i[0]] for i in sim_scores]
    similar_movies = db.query(Movie).filter(Movie.id.in_(similar_ids)).all()
    
    # Return in order of similarity
    movie_dict = {m.id: m for m in similar_movies}
    return [movie_dict[mid] for mid in similar_ids if mid in movie_dict]


def semantic_search_movies(query: str, db: Session, limit: int = 10):
    """
    Embeds a raw natural-language query (e.g. a chatbot message) and finds the
    closest movies in the catalog by embedding cosine similarity. This is the
    primary accuracy upgrade for free-text requests like "romcoms that would
    make you cry" - it searches by actual MEANING instead of requiring the
    query to contain specific hand-coded genre/trait keywords.

    Returns [] if Gemini isn't configured, embeddings haven't been trained/
    loaded yet, or the API call fails - callers should treat an empty result
    as "fall back to keyword/genre-based scoring", not as "no good matches".
    """
    global _embedding_matrix, _index_movie_map

    if _embedding_matrix is None or not GEMINI_API_KEY:
        return []

    query_vector = embed_text(query, task_type="retrieval_query")
    if not query_vector:
        return []

    query_vector = np.array(query_vector).reshape(1, -1)
    if query_vector.shape[1] != _embedding_matrix.shape[1]:
        return []  # dimension mismatch safety guard (e.g. stale cache after a model change)

    sims = cosine_similarity(query_vector, _embedding_matrix)[0]
    # Only consider rows that actually have a real (non-zero) cached embedding
    valid_mask = np.any(_embedding_matrix, axis=1)
    scored = [(idx, sims[idx]) for idx in range(len(sims)) if valid_mask[idx]]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_ids = [_index_movie_map[idx] for idx, _ in scored[:limit]]

    movies = db.query(Movie).filter(Movie.id.in_(top_ids)).all()
    movie_dict = {m.id: m for m in movies}
    return [movie_dict[mid] for mid in top_ids if mid in movie_dict]


def get_cold_start_recommendations(user: User, db: Session, limit: int = 20):
    """
    Calculate matching score based on user questionnaire preferences (Cold Start).
    """
    all_movies = db.query(Movie).all()
    
    pref_genres = set(user.preferred_genres or [])
    pref_actors = set(user.preferred_actors or [])
    pref_directors = set(user.preferred_directors or [])
    pref_langs = set(user.preferred_languages or [])
    pref_runtime = user.preferred_runtime
    pref_mood = user.preferred_mood

    # Define mood-to-genre maps
    mood_genre_map = {
        "Happy": ["Comedy", "Romance", "Music"],
        "Sad": ["Drama", "Romance"],
        "Mind-bending": ["Sci-Fi", "Thriller", "Mystery"],
        "Feel-good": ["Comedy", "Drama", "Romance"],
        "Dark": ["Crime", "Thriller", "Mystery", "Horror"],
        "Family": ["Fantasy", "Adventure", "Animation", "Comedy"]
    }
    mood_genres = set(mood_genre_map.get(pref_mood, []))

    scored_movies = []
    for m in all_movies:
        score = 0.0
        
        # Genre matches
        m_genres = set(m.genres or [])
        genre_matches = len(pref_genres.intersection(m_genres))
        score += genre_matches * 1.5
        
        # Mood matches (indirect genre match)
        mood_genre_matches = len(mood_genres.intersection(m_genres))
        score += mood_genre_matches * 1.0

        # Actor matches
        m_cast = set(m.cast or [])
        actor_matches = len(pref_actors.intersection(m_cast))
        score += actor_matches * 2.0

        # Director match
        if m.director in pref_directors:
            score += 3.0

        # Language match
        m_langs = set(m.languages or [])
        lang_matches = len(pref_langs.intersection(m_langs))
        score += lang_matches * 1.0

        # Runtime match
        # Under 90 mins, 90-120 mins, Over 2 hours
        if pref_runtime == "Under 90 mins" and m.runtime and m.runtime < 90:
            score += 1.0
        elif pref_runtime == "90-120 mins" and m.runtime and 90 <= m.runtime <= 120:
            score += 1.0
        elif pref_runtime == "Over 2 hours" and m.runtime and m.runtime > 120:
            score += 1.0

        # Add small popularity factor
        score += (m.popularity or 0) * 0.005
        # Add rating factor
        score += (m.vote_average or 0) * 0.1

        scored_movies.append((m, score))

    scored_movies.sort(key=lambda x: x[1], reverse=True)
    return [sm[0] for sm in scored_movies[:limit]]


def get_hybrid_recommendations(user_id: int, db: Session, limit: int = 20):
    """
    Computes portfolio-grade hybrid recommendations.
    Uses a Two-Stage Recommender System (Retrieval + Personalized Ranking).
    - Stage 1: Retrieve candidate movies from TMDB recommendations for user's liked movies, 
      falling back to TMDB popular and genre matches. Candidates are ingested on-the-fly.
    - Stage 2: Rank candidates using Collaborative SVD, Content TF-IDF, User Preference overlap,
      and global TMDb popularity.
    """
    global _svd_model, _cosine_sim, _movie_id_map
    import os
    import urllib.request
    import json
    from .tmdb import (
        fetch_tmdb_recommendations,
        fetch_tmdb_similar,
        save_lightweight_tmdb_movies,
        search_tmdb_movies
    )

    api_key = os.getenv("TMDB_API_KEY", "")

    # 1. Fetch user data
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    # 2. Get user ratings
    user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    rated_movie_ids = {r.movie_id for r in user_ratings}
    liked_ratings = [r for r in user_ratings if r.rating >= 3.5]
    
    # Also get watchlist want-to-watch movies to include in preferences
    watchlist_items = db.query(Watchlist).filter(Watchlist.user_id == user_id, Watchlist.status == "Want to Watch").all()
    watchlist_movie_ids = {w.movie_id for w in watchlist_items}

    # --- STAGE 1: CANDIDATE RETRIEVAL ---
    raw_candidates = []
    
    # A. Retrieve from TMDB Recommendations for user's top liked movies
    if liked_ratings:
        # Sort liked ratings by score descending, pick up to top 3
        liked_ratings.sort(key=lambda x: x.rating, reverse=True)
        top_liked = liked_ratings[:3]
        
        for lr in top_liked:
            movie = db.query(Movie).filter(Movie.id == lr.movie_id).first()
            if not movie:
                continue
                
            # If movie doesn't have tmdb_id, try to fetch it first
            if not movie.tmdb_id:
                try:
                    search_res = search_tmdb_movies(api_key, movie.title)
                    if search_res:
                        movie.tmdb_id = search_res[0]['tmdb_id']
                        db.commit()
                except Exception:
                    pass
            
            if movie.tmdb_id:
                recs = fetch_tmdb_recommendations(movie.tmdb_id, api_key)
                sims = fetch_tmdb_similar(movie.tmdb_id, api_key)
                raw_candidates.extend(recs)
                raw_candidates.extend(sims)

    # B. Retrieve TMDb Popular/Trending if candidates are few or user has no ratings
    if len(raw_candidates) < 40:
        try:
            for page in [1, 2]:
                url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&page={page}&language=en-US"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as res:
                    data = json.loads(res.read().decode('utf-8'))
                    raw_candidates.extend(data.get('results', []))
        except Exception as e:
            print(f"Error fetching popular candidates: {e}")

    # C. Dedup candidates by TMDb ID & title
    seen_ids = set()
    deduped_candidates = []
    for c in raw_candidates:
        cid = c.get('id')
        ctitle = c.get('title')
        if cid and cid not in seen_ids:
            seen_ids.add(cid)
            deduped_candidates.append(c)

    # D. Ingest these retrieved candidates into local DB on-the-fly
    candidate_movies = save_lightweight_tmdb_movies(db, deduped_candidates, api_key)
    
    # E. Filter out movies the user has already rated
    candidate_movies = [m for m in candidate_movies if m.id not in rated_movie_ids]
    
    # Fallback to local database if candidate list is empty
    if not candidate_movies:
        candidate_movies = db.query(Movie).filter(Movie.id.notin_(rated_movie_ids)).limit(50).all()

    # Ensure models are trained
    if _cosine_sim is None:
        train_recommender(db)

    # --- STAGE 2: PERSONAL RANKING ---
    liked_movie_ids = {r.movie_id for r in liked_ratings}
    
    # Compute Content Score (TF-IDF Cosine Similarity) against user liked movies
    content_scores = {}
    for m in candidate_movies:
        if m.id not in _movie_id_map:
            content_scores[m.id] = 0.0
            continue
            
        m_idx = _movie_id_map[m.id]
        
        sims = []
        for liked_id in liked_movie_ids:
            if liked_id in _movie_id_map:
                liked_idx = _movie_id_map[liked_id]
                sims.append(_cosine_sim[m_idx][liked_idx])
                
        content_scores[m.id] = np.mean(sims) if sims else 0.0

    # Max-min scale the content scores to [0, 1]
    c_vals = list(content_scores.values())
    if c_vals and max(c_vals) > min(c_vals):
        max_c, min_c = max(c_vals), min(c_vals)
        content_scores = {mid: (val - min_c) / (max_c - min_c) for mid, val in content_scores.items()}
    else:
        content_scores = {mid: 0.5 for mid in content_scores}

    # Score candidates using multiple factors
    scored_movies = []
    
    pref_genres = set(user.preferred_genres or [])
    pref_actors = set(user.preferred_actors or [])
    pref_directors = set(user.preferred_directors or [])
    pref_langs = set(user.preferred_languages or [])
    
    mood_genres = {
        "Happy": ["Comedy", "Romance", "Music"],
        "Sad": ["Drama", "Romance"],
        "Mind-bending": ["Sci-Fi", "Thriller", "Mystery"],
        "Feel-good": ["Comedy", "Drama", "Romance"],
        "Dark": ["Crime", "Thriller", "Mystery", "Horror"],
        "Family": ["Fantasy", "Adventure", "Animation", "Comedy"]
    }
    mood_genre_set = set(mood_genres.get(user.preferred_mood, []))

    for m in candidate_movies:
        # 1. SVD Score (Collaborative Filtering prediction)
        if _svd_model is not None:
            collab_rating = _svd_model.predict(user_id, m.id)
            collab_score = (collab_rating - 1.0) / 4.0  # Scale [1,5] to [0,1]
        else:
            collab_score = 0.5
            
        # 2. Content Score (TF-IDF Similarity)
        content_score = content_scores.get(m.id, 0.5)

        # 3. Preference Overlap Score
        m_genres = set(m.genres or [])
        genre_overlap = len(pref_genres.intersection(m_genres))
        genre_score = 1.0 if genre_overlap > 0 else 0.0
        
        mood_overlap = len(mood_genre_set.intersection(m_genres))
        mood_score = 1.0 if mood_overlap > 0 else 0.0
        
        m_cast = set(m.cast or [])
        actor_overlap = len(pref_actors.intersection(m_cast))
        actor_score = min(1.0, actor_overlap / max(1, len(pref_actors)))
        
        director_score = 1.0 if m.director in pref_directors else 0.0
        
        m_langs = set(m.languages or [])
        lang_overlap = len(pref_langs.intersection(m_langs))
        lang_score = 1.0 if lang_overlap > 0 else 0.0
        
        # Weighted preference score (total max 1.0)
        pref_score = 0.5 * genre_score + 0.2 * mood_score + 0.1 * actor_score + 0.1 * director_score + 0.1 * lang_score
        
        # 4. Global Score (TMDB popularity & ratings)
        pop_score = min(1.0, (m.popularity or 50.0) / 500.0)
        rating_score = (m.vote_average or 7.0) / 10.0
        global_score = 0.4 * pop_score + 0.6 * rating_score

        # 5. Hybrid Scoring: 0.35 Collab + 0.35 Content + 0.20 Preference + 0.10 Global
        hybrid_score = 0.35 * collab_score + 0.35 * content_score + 0.20 * pref_score + 0.10 * global_score
        
        # Boost movies in watchlist
        if m.id in watchlist_movie_ids:
            hybrid_score += 0.05
            
        scored_movies.append((m, hybrid_score))

    # Sort candidates by Hybrid Score and return top ones
    scored_movies.sort(key=lambda x: x[1], reverse=True)
    return [sm[0] for sm in scored_movies[:limit]]


def explain_recommendation(user_id: int, movie: Movie, db: Session) -> str:
    """
    Returns an explanatory string for why this movie is recommended to this user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "Recommended for you."

    # 1. Check if collaborative factors are strong
    user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    
    # Find overlapping preferences
    m_genres = set(movie.genres or [])
    u_genres = set(user.preferred_genres or [])
    genre_overlap = u_genres.intersection(m_genres)
    
    # Check if user rated similar movies high
    highest_rated = db.query(Rating).filter(Rating.user_id == user_id, Rating.rating >= 4.0).order_by(Rating.rating.desc()).first()
    
    if highest_rated:
        ref_movie = db.query(Movie).filter(Movie.id == highest_rated.movie_id).first()
        if ref_movie and len(set(ref_movie.genres).intersection(m_genres)) > 0:
            return f"Recommended because you rated {ref_movie.title} {int(highest_rated.rating)}⭐ and enjoy {ref_movie.genres[0]} films."

    if movie.director in (user.preferred_directors or []):
        return f"Recommended because you enjoy films directed by {movie.director}."
        
    actor_overlap = set(user.preferred_actors or []).intersection(set(movie.cast or []))
    if actor_overlap:
        return f"Recommended because you enjoy movies starring {list(actor_overlap)[0]}."

    if genre_overlap:
        return f"Recommended because you're a fan of {list(genre_overlap)[0]} movies."

    if user.preferred_mood:
        return f"Recommended because it matches your preferred '{user.preferred_mood}' mood."

    return f"Recommended because people with similar taste liked {movie.title}."