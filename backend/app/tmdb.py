import urllib.request
import urllib.parse
import json
import time
from sqlalchemy.orm import Session
from .models import Movie

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# All standard TMDb movie genre IDs -> names (kept in sync with save_lightweight_tmdb_movies)
GENRE_IDS = [28, 12, 16, 35, 80, 99, 18, 10751, 14, 36, 27, 10402, 9648, 10749, 878, 10770, 53, 10752, 37]

# Decade windows used to pull older/classic titles that /popular and /top_rated rarely surface
DECADE_WINDOWS = [
    ("1960-01-01", "1979-12-31"),
    ("1980-01-01", "1999-12-31"),
    ("2000-01-01", "2014-12-31"),
    ("2015-01-01", "2026-12-31"),
]

# A few non-English original languages to pull in international titles alongside Hollywood
LANGUAGE_POOL = ["en", "ja", "ko", "fr", "es", "hi"]


def _fetch_json(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode('utf-8'))


def _discover_page(api_key: str, page: int = 1, **params) -> list:
    """
    Calls TMDb's /discover/movie endpoint with arbitrary filter params
    (with_genres, sort_by, primary_release_date.gte/lte, with_original_language, vote_count.gte, etc.)
    """
    query_params = {"api_key": api_key, "language": "en-US", "page": page, **params}
    url = f"https://api.themoviedb.org/3/discover/movie?{urllib.parse.urlencode(query_params)}"
    try:
        data = _fetch_json(url)
        return data.get('results', [])
    except Exception as e:
        print(f"Discover fetch failed ({params}, page {page}): {e}")
        return []


def sync_movies_from_tmdb(db: Session, api_key: str, count: int = 100, max_api_calls: int = 300):
    """
    Syncs a broad, diverse set of movies from TMDb into the local database.

    Unlike a single /movie/popular crawl (which plateaus at a few hundred recent,
    mostly-Hollywood titles), this pulls from multiple complementary sources so the
    catalog actually approaches "all possible movies" within the requested count:
      1. Curated endpoints: popular, top_rated, now_playing, upcoming
      2. /discover across every genre, multiple sort orders, and decade windows
         (surfaces classics, hidden gems, and genre-specific deep catalog)
      3. /discover across several non-English original languages (international cinema)

    Each source gets a GUARANTEED quota of the total `count` (allocated up front)
    rather than being filled greedily in sequence. Greedy sequential filling was
    the bug behind "barely any international movies": curated + genre-discover
    (both English-heavy) would exhaust the whole budget before the international
    pass ever ran. Quotas ensure international titles always get their share.

    Full details (cast, director, trailer) remain lazy-loaded on-demand elsewhere.
    """
    seen_ids = set()
    tmdb_movies = []
    api_calls = 0

    def add_results(results):
        for r in results:
            rid = r.get('id')
            if rid and rid not in seen_ids:
                seen_ids.add(rid)
                tmdb_movies.append(r)

    def calls_left():
        return api_calls < max_api_calls

    # --- Quota allocation ---
    international_quota = max(15, int(count * 0.20))
    genre_discover_quota = max(15, int(count * 0.30))
    curated_quota = max(0, count - international_quota - genre_discover_quota)

    curated_target = curated_quota
    genre_target = curated_quota + genre_discover_quota
    full_target = count  # curated + genre + international

    # --- Source 1: curated endpoints (broad, high-quality, cheap) ---
    for endpoint in ["popular", "top_rated", "now_playing", "upcoming"]:
        page = 1
        while len(tmdb_movies) < curated_target and calls_left() and page <= 10:
            url = f"https://api.themoviedb.org/3/movie/{endpoint}?api_key={api_key}&page={page}&language=en-US"
            try:
                data = _fetch_json(url)
                api_calls += 1
                results = data.get('results', [])
                if not results:
                    break
                add_results(results)
                page += 1
            except Exception as e:
                print(f"Failed to fetch {endpoint} page {page}: {e}")
                break
        if len(tmdb_movies) >= curated_target:
            break

    # --- Source 2: discover across genres x sort orders x decades (deep catalog + classics) ---
    sort_options = ["popularity.desc", "vote_average.desc", "revenue.desc"]
    for genre_id in GENRE_IDS:
        if len(tmdb_movies) >= genre_target or not calls_left():
            break
        for sort_by in sort_options:
            if len(tmdb_movies) >= genre_target or not calls_left():
                break
            for start, end in DECADE_WINDOWS:
                if len(tmdb_movies) >= genre_target or not calls_left():
                    break
                params = {
                    "with_genres": genre_id,
                    "sort_by": sort_by,
                    "primary_release_date.gte": start,
                    "primary_release_date.lte": end,
                }
                # Avoid surfacing obscure/no-vote junk when sorting by rating
                if sort_by == "vote_average.desc":
                    params["vote_count.gte"] = 100
                results = _discover_page(api_key, page=1, **params)
                api_calls += 1
                add_results(results)
                time.sleep(0.02)

    # --- Source 3: international cinema via original-language discover ---
    # This runs with its own guaranteed room up to `full_target`, regardless of
    # how much of the budget sources 1-2 used, as long as api_calls remain.
    lang_page_cap = 6  # allow deeper paging per language so the quota can actually be met
    for lang in LANGUAGE_POOL:
        if len(tmdb_movies) >= full_target or not calls_left():
            break
        page = 1
        while len(tmdb_movies) < full_target and calls_left() and page <= lang_page_cap:
            results = _discover_page(
                api_key, page=page,
                sort_by="popularity.desc",
                with_original_language=lang,
                **{"vote_count.gte": 30}
            )
            api_calls += 1
            if not results:
                break
            add_results(results)
            page += 1
            time.sleep(0.02)

    tmdb_movies = tmdb_movies[:count]
    saved = save_lightweight_tmdb_movies(db, tmdb_movies, api_key)
    synced_count = len(saved)

    print(f"TMDb sync finished. {api_calls} API calls made, {len(tmdb_movies)} unique candidates found, "
          f"{synced_count} movies saved/updated in database. "
          f"(quotas -> curated: {curated_quota}, genre-discover: {genre_discover_quota}, international: {international_quota})")
    return synced_count


def search_tmdb_movies(api_key: str, query: str):
    """
    Searches TMDb for a movie by query and returns lightweight results for UI.
    """
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(query)}&language=en-US&page=1"
    try:
        data = _fetch_json(url, timeout=5)
        results = data.get('results', [])[:5]  # Return top 5 matches
        return [{
            "tmdb_id": r['id'],
            "title": r.get('title'),
            "poster_path": r.get('poster_path'),
            "release_date": r.get('release_date')
        } for r in results]
    except Exception as e:
        print(f"TMDb Search Error: {e}")
        return []


def fetch_tmdb_movie_by_id(db: Session, tmdb_id: int, api_key: str):
    """
    Fetches a single movie by its TMDb ID and saves it to the local database if missing.
    Returns the local Movie object.
    """
    try:
        detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=en-US"
        detail = _fetch_json(detail_url, timeout=5)

        title = detail.get('title')
        if not title:
            return None

        existing = db.query(Movie).filter((Movie.tmdb_id == tmdb_id) | (Movie.title == title)).first()
        if existing:
            if not existing.tmdb_id:
                existing.tmdb_id = tmdb_id
                db.commit()
            return existing

        # Fetch credits
        credits_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={api_key}"
        credits = _fetch_json(credits_url, timeout=5)

        director = "Unknown Director"
        for crew_member in credits.get('crew', []):
            if crew_member.get('job') == 'Director':
                director = crew_member.get('name')
                break

        cast = [actor.get('name') for actor in credits.get('cast', [])[:4]]
        genres = [g['name'] for g in detail.get('genres', [])]
        if not genres:
            genres = ["Drama"]

        trailer_id = None
        try:
            videos_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={api_key}"
            vid_data = _fetch_json(videos_url, timeout=5)
            for v in vid_data.get('results', []):
                if v.get('type') == 'Trailer' and v.get('site') == 'YouTube':
                    trailer_id = v.get('key')
                    break
        except Exception:
            pass

        new_movie = Movie(
            tmdb_id=tmdb_id,
            title=title,
            genres=genres,
            overview=detail.get('overview', ''),
            cast=cast,
            director=director,
            poster_path=detail.get('poster_path'),
            backdrop_path=detail.get('backdrop_path'),
            runtime=detail.get('runtime', 120) or 120,
            vote_average=detail.get('vote_average', 7.0),
            popularity=detail.get('popularity', 50.0),
            release_date=detail.get('release_date', '2026-07-01'),
            budget=detail.get('budget', 0) or 0,
            revenue=detail.get('revenue', 0) or 0,
            youtube_trailer_id=trailer_id,
            streaming_platforms=["Netflix", "Prime Video", "Max"],
            languages=[detail.get('original_language', 'en')],
            awards=["TMDb Sync"],
            country=detail.get('production_countries', [{}])[0].get('name', 'United States') if detail.get('production_countries') else 'United States'
        )
        db.add(new_movie)
        db.commit()
        db.refresh(new_movie)
        return new_movie
    except Exception as e:
        print(f"Error fetching movie {tmdb_id}: {e}")
        return None


def fetch_trailer_by_title(title: str, api_key: str):
    """
    Searches TMDb by movie title and retrieves the official YouTube trailer key.
    """
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(title)}&language=en-US&page=1"
        data = _fetch_json(search_url, timeout=5)
        results = data.get('results', [])
        if not results:
            return None
        tmdb_id = results[0]['id']

        videos_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={api_key}"
        vid_data = _fetch_json(videos_url, timeout=5)
        for v in vid_data.get('results', []):
            if v.get('type') == 'Trailer' and v.get('site') == 'YouTube':
                return v.get('key')
    except Exception as e:
        print(f"Error fetching trailer for {title}: {e}")
    return None


def fetch_tmdb_recommendations(tmdb_id: int, api_key: str) -> list:
    """
    Fetches recommendations from TMDb API for a given movie ID.
    """
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/recommendations?api_key={api_key}&language=en-US&page=1"
    try:
        data = _fetch_json(url, timeout=5)
        return data.get('results', [])
    except Exception as e:
        print(f"Error fetching TMDb recommendations for movie {tmdb_id}: {e}")
        return []


def fetch_tmdb_similar(tmdb_id: int, api_key: str) -> list:
    """
    Fetches similar movies from TMDb API for a given movie ID.
    """
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/similar?api_key={api_key}&language=en-US&page=1"
    try:
        data = _fetch_json(url, timeout=5)
        return data.get('results', [])
    except Exception as e:
        print(f"Error fetching TMDb similar movies for movie {tmdb_id}: {e}")
        return []


def save_lightweight_tmdb_movies(db: Session, tmdb_movies: list, api_key: str = None) -> list:
    """
    Takes a list of raw movie dicts returned by TMDb API (recommendations, popular, discover, etc.)
    and inserts them into the database as lightweight movie entries if they don't exist.
    Avoids extra network requests! Maps genre IDs to names.
    Returns list of local Movie objects.
    """
    genre_map = {
        28: "Action", 12: "Adventure", 16: "Anime", 35: "Comedy", 80: "Crime",
        99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy",
        36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery",
        10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie", 53: "Thriller",
        10752: "War", 37: "Western"
    }

    saved_movies = []
    for m in tmdb_movies:
        try:
            tmdb_id = m.get('id')
            title = m.get('title')
            if not tmdb_id or not title:
                continue

            existing = db.query(Movie).filter((Movie.tmdb_id == tmdb_id) | (Movie.title == title)).first()
            if existing:
                if not existing.tmdb_id:
                    existing.tmdb_id = tmdb_id
                    db.commit()
                saved_movies.append(existing)
                continue

            genre_ids = m.get('genre_ids', [])
            genres = [genre_map.get(gid) for gid in genre_ids if gid in genre_map]
            if not genres:
                genres = ["Drama"]

            new_movie = Movie(
                tmdb_id=tmdb_id,
                title=title,
                genres=genres,
                overview=m.get('overview', ''),
                cast=[],
                director="Unknown Director",
                poster_path=m.get('poster_path'),
                backdrop_path=m.get('backdrop_path'),
                runtime=120,
                vote_average=m.get('vote_average', 7.0),
                popularity=m.get('popularity', 50.0),
                release_date=m.get('release_date', '2026-07-01'),
                budget=0,
                revenue=0,
                youtube_trailer_id=None,
                streaming_platforms=["Netflix", "Prime Video", "Max"],
                languages=[m.get('original_language', 'en')],
                awards=["TMDb Ingest"],
                country="United States"
            )
            db.add(new_movie)
            db.commit()
            db.refresh(new_movie)
            saved_movies.append(new_movie)
        except Exception as e:
            print(f"Error saving lightweight TMDB movie: {e}")
            db.rollback()

    return saved_movies


def backfill_missing_posters(db: Session, api_key: str, limit: int = 80, max_api_calls: int = 150) -> dict:
    """
    One-time repair utility: finds movies in the local DB with a missing/empty
    poster_path (the ones currently rendering as generic stock-photo fallbacks
    in the UI) and tries to resolve real artwork for them from TMDb by title.

    - If a tmdb_id already exists, fetches details directly by ID (fast, exact).
    - Otherwise, searches TMDb by title and takes the closest match.
    - Movies that still can't be resolved (e.g. fictional/test entries with no
      real TMDb counterpart) are reported back separately so you can decide
      whether to manually fix or delete them.

    `limit` and `max_api_calls` bound how much work a single call can do, so
    this can never turn into a long-running, request-blocking operation -
    call it repeatedly (e.g. from a background task) if you have more than
    `limit` movies needing repair.
    """
    candidates = db.query(Movie).filter(
        (Movie.poster_path == None) | (Movie.poster_path == "")
    ).limit(limit).all()

    fixed = []
    unresolved = []
    api_calls = 0

    for i, movie in enumerate(candidates):
        if api_calls >= max_api_calls:
            print(f"Poster backfill: hit max_api_calls ({max_api_calls}) budget, stopping early "
                  f"({i}/{len(candidates)} candidates processed).")
            break
        try:
            detail = None
            if movie.tmdb_id:
                detail_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?api_key={api_key}&language=en-US"
                detail = _fetch_json(detail_url, timeout=5)
                api_calls += 1
            else:
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(movie.title)}&language=en-US&page=1"
                search_data = _fetch_json(search_url, timeout=5)
                api_calls += 1
                results = search_data.get('results', [])
                if results:
                    tmdb_id = results[0]['id']
                    detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=en-US"
                    detail = _fetch_json(detail_url, timeout=5)
                    api_calls += 1
                    movie.tmdb_id = tmdb_id

            if detail and detail.get('poster_path'):
                movie.poster_path = detail.get('poster_path')
                if detail.get('backdrop_path'):
                    movie.backdrop_path = detail.get('backdrop_path')
                db.commit()
                fixed.append(movie.title)
            else:
                unresolved.append(movie.title)
        except Exception as e:
            print(f"Poster backfill failed for '{movie.title}': {e}")
            unresolved.append(movie.title)
            db.rollback()

        if (i + 1) % 10 == 0:
            print(f"Poster backfill progress: {i + 1}/{len(candidates)} processed "
                  f"({len(fixed)} fixed so far)")

    print(f"Poster backfill complete. Fixed: {len(fixed)}, Unresolved: {len(unresolved)}, API calls used: {api_calls}")
    return {"fixed": fixed, "unresolved": unresolved, "fixed_count": len(fixed), "unresolved_count": len(unresolved)}


def _poster_url_reachable(poster_path: str, timeout: int = 4) -> bool:
    """
    Checks whether a TMDb poster path actually resolves to a real image,
    rather than just checking it's non-null. This catches hand-typed/guessed
    poster hashes (e.g. from early hardcoded seed data) that look valid but
    404 when the browser actually tries to load them.
    """
    if not poster_path:
        return False
    url = f"https://image.tmdb.org/t/p/w200{poster_path}"
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return 200 <= res.status < 300
    except Exception:
        return False


def repair_broken_posters(db: Session, api_key: str, limit: int = 50, max_api_calls: int = 150) -> dict:
    """
    Unlike backfill_missing_posters (which only catches poster_path IS NULL),
    this validates that EXISTING poster paths actually resolve to a real
    image, and re-fetches from TMDb by title for any that don't. This is
    specifically for hand-typed/guessed poster hashes that were never verified
    (e.g. early hardcoded classics list) and silently 404 forever otherwise.

    Bounded by `limit` (movies checked) and `max_api_calls` (TMDb calls made
    for re-fetching), same safety pattern as backfill_missing_posters - call
    repeatedly / as a background task rather than assuming one call covers
    the whole catalog.
    """
    candidates = db.query(Movie).filter(
        Movie.poster_path.isnot(None), Movie.poster_path != ""
    ).limit(limit).all()

    fixed = []
    still_broken = []
    checked = 0
    api_calls = 0

    for movie in candidates:
        checked += 1
        if _poster_url_reachable(movie.poster_path):
            continue  # already fine, nothing to do

        if api_calls >= max_api_calls:
            still_broken.append(movie.title)
            continue

        try:
            detail = None
            if movie.tmdb_id:
                detail_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?api_key={api_key}&language=en-US"
                detail = _fetch_json(detail_url, timeout=5)
                api_calls += 1
            else:
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(movie.title)}&language=en-US&page=1"
                search_data = _fetch_json(search_url, timeout=5)
                api_calls += 1
                results = search_data.get('results', [])
                if results:
                    tmdb_id = results[0]['id']
                    detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=en-US"
                    detail = _fetch_json(detail_url, timeout=5)
                    api_calls += 1
                    movie.tmdb_id = tmdb_id

            if detail and detail.get('poster_path'):
                movie.poster_path = detail.get('poster_path')
                if detail.get('backdrop_path'):
                    movie.backdrop_path = detail.get('backdrop_path')
                db.commit()
                fixed.append(movie.title)
            else:
                still_broken.append(movie.title)
        except Exception as e:
            print(f"Poster repair failed for '{movie.title}': {e}")
            still_broken.append(movie.title)
            db.rollback()

    print(f"Poster repair complete. Checked: {checked}, Fixed: {len(fixed)}, Still broken: {len(still_broken)}, API calls: {api_calls}")
    return {
        "checked": checked,
        "fixed": fixed,
        "fixed_count": len(fixed),
        "still_broken": still_broken,
        "still_broken_count": len(still_broken)
    }


def lazy_load_movie_details(db: Session, movie: Movie, api_key: str) -> Movie:

    """
    Lazy loads credits (cast, director) and videos (YouTube trailer) for a movie from TMDb
    if they are missing, updating the record in the database.
    """
    if not api_key or not movie.tmdb_id:
        return movie

    has_cast = len(movie.cast) > 0 if isinstance(movie.cast, list) else False
    has_director = movie.director and movie.director != "Unknown Director"
    has_trailer = movie.youtube_trailer_id is not None

    if has_cast and has_director and has_trailer:
        return movie

    updated = False
    try:
        if not has_cast or not has_director:
            credits_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/credits?api_key={api_key}"
            credits = _fetch_json(credits_url, timeout=5)

            if not has_director:
                director = "Unknown Director"
                for crew_member in credits.get('crew', []):
                    if crew_member.get('job') == 'Director':
                        director = crew_member.get('name')
                        break
                movie.director = director
                updated = True

            if not has_cast:
                cast = [actor.get('name') for actor in credits.get('cast', [])[:4]]
                movie.cast = cast
                updated = True

        if not has_trailer:
            videos_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/videos?api_key={api_key}"
            vid_data = _fetch_json(videos_url, timeout=5)
            trailer_id = None
            for v in vid_data.get('results', []):
                if v.get('type') == 'Trailer' and v.get('site') == 'YouTube':
                    trailer_id = v.get('key')
                    break
            movie.youtube_trailer_id = trailer_id
            updated = True

        if movie.runtime == 120 or movie.budget == 0 or movie.revenue == 0:
            detail_url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}?api_key={api_key}&language=en-US"
            detail = _fetch_json(detail_url, timeout=5)
            movie.runtime = detail.get('runtime', movie.runtime) or movie.runtime
            movie.budget = detail.get('budget', movie.budget) or movie.budget
            movie.revenue = detail.get('revenue', movie.revenue) or movie.revenue
            updated = True

        if updated:
            db.commit()
            db.refresh(movie)
            print(f"Lazy loaded full details for movie: {movie.title}")

    except Exception as e:
        print(f"Failed to lazy load details for movie {movie.title} (ID: {movie.tmdb_id}): {e}")
        db.rollback()

    return movie