import os
import random
import json
import re
import difflib
import google.generativeai as genai
from sqlalchemy.orm import Session
from .models import Movie
from .recommender import get_similar_movies, semantic_search_movies

# Check for API Key in Environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

VALID_GENRES = [
    "Action", "Adventure", "Anime", "Comedy", "Crime", "Documentary", "Drama",
    "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance",
    "Sci-Fi", "TV Movie", "Thriller", "War", "Western"
]

# Literal genre names/synonyms/slang -> one or more genres. These are objective
# labels (not emotional descriptors), so they're always a positive signal
# regardless of surrounding words.
GENRE_KEYWORDS = {
    "sci-fi": ["Sci-Fi"], "scifi": ["Sci-Fi"], "space": ["Sci-Fi"], "futuristic": ["Sci-Fi"],
    "comedy": ["Comedy"],
    "horror": ["Horror"],
    "romance": ["Romance"], "romantic comedy": ["Romance", "Comedy"],
    "romcom": ["Romance", "Comedy"], "rom-com": ["Romance", "Comedy"], "rom com": ["Romance", "Comedy"],
    "thriller": ["Thriller"], "suspense": ["Thriller"],
    "action": ["Action"], "crime": ["Crime"], "gangster": ["Crime"],
    "mystery": ["Mystery"], "whodunit": ["Mystery"],
    "fantasy": ["Fantasy"], "anime": ["Anime"], "animated": ["Anime"],
    "drama": ["Drama"], "war movie": ["War"], "western": ["Western"],
    "musical": ["Music"], "documentary": ["Documentary"],
    "family movie": ["Family"], "historical": ["History"], "history": ["History"],
}

# Descriptive/emotional trait words that IMPLY genres, in whichever direction
# the user means them. "Make you cry" implies wanting more Drama/Romance;
# "less emotional" implies wanting LESS of the same genres. Same mapping,
# direction decided by whether a negation phrase precedes the word.
TRAIT_GENRE_MAP = {
    "emotional": ["Drama", "Romance"],
    "sad": ["Drama"],
    "cry": ["Drama", "Romance"],
    "crying": ["Drama", "Romance"],
    "tearjerker": ["Drama", "Romance"],
    "heartbreaking": ["Drama", "Romance"],
    "depressing": ["Drama"],
    "funny": ["Comedy"],
    "hilarious": ["Comedy"],
    "lighthearted": ["Comedy"],
    "scary": ["Horror"],
    "creepy": ["Horror"],
    "terrifying": ["Horror"],
    "violent": ["War", "Crime", "Action"],
    "dark": ["Thriller", "Crime", "Horror"],
    "serious": ["Drama", "History"],
    "slow": ["Drama", "History"],
    "feel-good": ["Comedy", "Romance", "Family"],
    "feel good": ["Comedy", "Romance", "Family"],
    "heartwarming": ["Comedy", "Romance", "Family"],
    "uplifting": ["Comedy", "Family"],
    "romantic": ["Romance"],
    "mind-bending": ["Sci-Fi", "Thriller", "Mystery"],
    "mind bending": ["Sci-Fi", "Thriller", "Mystery"],
}

NEGATION_PREFIX = r'(?:less\s+|not too\s+|not very\s+|without\s+(?:much\s+)?|no\s+|barely\s+any\s+)'


def _detect_trait_signals(query_lower: str):
    """
    Scans the query for descriptive trait words. Each match is classified as:
      - an EXCLUDE signal if immediately preceded by a negation phrase
        ("less emotional", "not too violent", "without much sadness")
      - otherwise a POSITIVE genre signal ("that would make you cry" -> wants
        more Drama/Romance)
    Same underlying trait->genre mapping is used for both directions, so
    "less emotional" and "make you cry" can never be confused with each other.
    """
    genres_to_add = []
    exclude_traits = []
    for trait, mapped_genres in TRAIT_GENRE_MAP.items():
        negated_pattern = rf'{NEGATION_PREFIX}{re.escape(trait)}'
        if re.search(negated_pattern, query_lower):
            exclude_traits.append(trait)
        elif trait in query_lower:
            for g in mapped_genres:
                if g not in genres_to_add:
                    genres_to_add.append(g)
    return genres_to_add, exclude_traits


# ---------------------------------------------------------------------------
# AI Summary & Review helpers (unchanged behavior)
# ---------------------------------------------------------------------------

def get_fallback_summary(title: str, overview: str) -> str:
    """
    Formulates a neat cinematic hook based on the overview.
    """
    sentences = [s.strip() for s in (overview or "").split(".") if s.strip()]
    if sentences:
        first_part = sentences[0]
        hook = f"Step into the world of '{title}', where {first_part.lower() if first_part.lower().startswith('a') or first_part.lower().startswith('the') else first_part}."
        if len(sentences) > 1:
            hook += f" As events unfold, prepare for a captivating journey that will challenge everything you think you know."
        return hook
    return f"Experience '{title}', an unforgettable cinematic journey full of depth, suspense, and emotional resonance."


def get_fallback_reviews(title: str, genres: list, director: str) -> dict:
    """
    Generates realistic looking mock reviews based on movie parameters.
    """
    g_str = genres[0] if genres else "Drama"

    # Deterministic seed based on movie title length to keep fallback values stable
    random.seed(len(title))

    opinions = [
        f"Audiences are widely praising this film's atmosphere and the compelling execution of its {g_str} elements.",
        f"A visual masterpiece that holds viewer interest, even if the pacing slows down slightly in the middle.",
        f"A striking performance by the cast makes this film directed by {director} one of the most memorable of its genre."
    ]

    loved = [
        "The incredible cinematography and the immersive musical score that heightens every scene.",
        "The nuanced acting and chemistry between the lead characters, bringing genuine emotional depth.",
        "The visionary directing style and mind-bending narrative structure that leaves you thinking long after."
    ]

    criticized = [
        "Some viewers felt the runtime was slightly long and could benefit from tighter editing.",
        "A few plot points in the second act require a bit of suspended disbelief.",
        "The dialogue can occasionally feel overly dramatic or expository during key moments."
    ]

    tones = ["Intellectual", "Somber", "Thrilling", "Heartwarming", "Intense", "Whimsical"]

    return {
        "audience_opinion": random.choice(opinions),
        "most_loved": random.choice(loved),
        "most_criticized": random.choice(criticized),
        "tone": random.choice(tones)
    }


def generate_ai_summary(title: str, overview: str) -> str:
    if not GEMINI_API_KEY:
        return get_fallback_summary(title, overview)

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Write a cinematic, extremely engaging, maximum 2-sentence movie summary hook for the film '{title}' WITHOUT containing any major spoilers. Base it on this overview: {overview}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error in summary: {e}")
        return get_fallback_summary(title, overview)


def generate_ai_review_analysis(title: str, genres: list, director: str) -> dict:
    if not GEMINI_API_KEY:
        return get_fallback_reviews(title, genres, director)

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        Analyze general review sentiments for the movie '{title}' (Genres: {', '.join(genres)}, Directed by: {director}).
        Respond in structured JSON format with the following keys:
        - "audience_opinion": One sentence summarizing overall audience consensus.
        - "most_loved": One concise point detailing what viewers love most.
        - "most_criticized": One concise point detailing what reviewers critique.
        - "tone": Single word representing the emotional tone of the movie.
        Ensure your response is valid JSON only. Do not wrap in markdown code blocks.
        """
        response = model.generate_content(prompt)

        text = _strip_json_fences(response.text)
        return json.loads(text)
    except Exception as e:
        print(f"Gemini API Error in review analysis: {e}")
        return get_fallback_reviews(title, genres, director)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


# ---------------------------------------------------------------------------
# Chatbot: intent extraction
# ---------------------------------------------------------------------------

def _extract_intent_with_gemini(query: str):
    """
    Uses Gemini to turn a free-form request into structured search intent.
    Returns None on any failure so the caller can fall back to heuristics.
    """
    if not GEMINI_API_KEY:
        return None
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        Extract structured movie-search intent from this user request for a movie recommendation chatbot.
        Request: "{query}"

        Respond with ONLY valid JSON (no markdown fences, no commentary) with exactly these keys:
        - "reference_movie": a specific movie title the user is comparing to or asking about, or null if none
        - "genres": array of genre names the user wants, chosen ONLY from this list: {json.dumps(VALID_GENRES)}
        - "exclude_traits": array of short lowercase single-word qualities the user wants LESS of or wants to avoid
          (choose from: emotional, sad, depressing, violent, scary, dark, slow, serious - or leave empty)
        - "director": a director name mentioned, or null
        - "actor": an actor name mentioned, or null

        Example output: {{"reference_movie": "Interstellar", "genres": ["Sci-Fi"], "exclude_traits": ["emotional"], "director": null, "actor": null}}
        """
        response = model.generate_content(prompt)
        text = _strip_json_fences(response.text)
        parsed = json.loads(text)
        # Basic shape validation so a malformed LLM response can't crash downstream logic
        parsed.setdefault("reference_movie", None)
        parsed.setdefault("genres", [])
        parsed.setdefault("exclude_traits", [])
        parsed.setdefault("director", None)
        parsed.setdefault("actor", None)
        return parsed
    except Exception as e:
        print(f"Gemini intent extraction failed, falling back to heuristics: {e}")
        return None


# Phrases that typically precede a direct movie mention with no "like"/"similar to"
# wording, e.g. "how about Inception", "what about the Dark Knight", "show me Dune".
LEADING_FILLER_PATTERNS = [
    r'^how about\s+',
    r'^what about\s+',
    r'^tell me about\s+',
    r'^recommend me\s+',
    r'^suggest me\s+',
    r'^give me\s+',
    r'^show me\s+',
    r'^i want\s+',
    r'^recommend\s+',
    r'^suggest\s+',
    r'^how bout\s+',
    r'^what\'s\s+',
    r'^whats\s+',
    r'^find\s+',
    r'^search for\s+',
]


def _extract_intent_fallback(query: str) -> dict:
    """
    Regex/keyword based intent extraction used when Gemini is unavailable or fails.
    """
    query_lower = query.lower()

    # Reference movie, in order of confidence:
    # 1. Quoted titles
    # 2. "like X" / "similar to X" phrasing, stopping before trailing qualifier
    #    clauses like "but less emotional"
    # 3. Direct mentions with no like/similar wording at all, e.g. "how about X",
    #    "what about X" - strip the leading filler phrase and treat the remainder
    #    as a candidate title. This is intentionally permissive: the caller
    #    verifies the candidate against the local catalog / TMDb before using it,
    #    so a wrong guess here just falls through to genre-based scoring instead
    #    of ever producing a bad recommendation.
    quoted = re.findall(r'"([^"]+)"', query)
    reference_movie = quoted[0] if quoted else None

    if not reference_movie:
        match = re.search(
            r'(?:like|similar to)\s+([A-Za-z0-9][A-Za-z0-9\s\-\:\',]*?)(?=\s+but\b|\s+that\b|\s+which\b|,|\.|$)',
            query, re.IGNORECASE
        )
        if match:
            reference_movie = match.group(1).strip()

    if not reference_movie:
        candidate = query.strip()
        for pattern in LEADING_FILLER_PATTERNS:
            stripped = re.sub(pattern, '', candidate, flags=re.IGNORECASE)
            if stripped != candidate:
                candidate = stripped.strip()
                break
        candidate = candidate.rstrip('?.! ').strip()
        # Only treat as a reference-movie guess if there's substance left
        # (avoids e.g. a bare "recommend" or "show me" with nothing after it).
        if candidate and len(candidate.split()) >= 2:
            reference_movie = candidate

    genres = []
    for kw, genre_list in GENRE_KEYWORDS.items():
        if kw in query_lower:
            for g in genre_list:
                if g not in genres:
                    genres.append(g)

    trait_genres, exclude_traits = _detect_trait_signals(query_lower)
    for g in trait_genres:
        if g not in genres:
            genres.append(g)

    return {
        "reference_movie": reference_movie,
        "genres": genres,
        "exclude_traits": exclude_traits,
        "director": None,
        "actor": None,
    }


def _extract_intent(query: str) -> dict:
    return _extract_intent_with_gemini(query) or _extract_intent_fallback(query)


def _scan_query_for_local_title(db: Session, query: str):
    """
    Last-resort safety net, run regardless of whether Gemini or the heuristic
    fallback handled extraction: checks if the raw query directly names a movie
    already in the local catalog. Catches direct mentions that structured
    extraction missed for any reason (e.g. "how about Interstellar" if intent
    extraction returned no reference_movie at all).
    """
    all_movies = db.query(Movie).all()
    if not all_movies:
        return None

    query_lower = query.lower()

    # Longest matching title wins, to avoid a short title false-matching inside
    # a longer unrelated phrase.
    substring_matches = [m for m in all_movies if m.title.lower() in query_lower]
    if substring_matches:
        return max(substring_matches, key=lambda m: len(m.title))

    candidate = query.strip()
    for pattern in LEADING_FILLER_PATTERNS:
        stripped = re.sub(pattern, '', candidate, flags=re.IGNORECASE)
        if stripped != candidate:
            candidate = stripped.strip()
            break
    candidate = candidate.rstrip('?.! ').strip().lower()

    if not candidate:
        return None

    titles_lower = {m.title.lower(): m for m in all_movies}
    close = difflib.get_close_matches(candidate, titles_lower.keys(), n=1, cutoff=0.55)
    if close:
        return titles_lower[close[0]]

    return None


# ---------------------------------------------------------------------------
# Chatbot: candidate retrieval & ranking
# ---------------------------------------------------------------------------

def _find_local_movie(db: Session, title_query: str):
    """
    Fuzzy-matches a title against the local catalog instead of hitting TMDb
    for every chat message. Returns a Movie or None.
    """
    if not title_query:
        return None
    all_movies = db.query(Movie).all()
    if not all_movies:
        return None

    titles_lower = {m.title.lower(): m for m in all_movies}
    q = title_query.lower().strip()

    if q in titles_lower:
        return titles_lower[q]

    close = difflib.get_close_matches(q, titles_lower.keys(), n=1, cutoff=0.6)
    if close:
        return titles_lower[close[0]]

    for t, m in titles_lower.items():
        if q in t or t in q:
            return m

    return None


def _try_ingest_reference_from_tmdb(db: Session, title_query: str):
    """
    Only reached if the reference movie isn't already in the local catalog.
    Uses the existing tmdb.py helpers (which persist full details) instead of
    duplicating raw API calls here. Fails safe (returns None) on any error.
    """
    api_key = os.getenv("TMDB_API_KEY", "")
    if not api_key or not title_query:
        return None
    try:
        from .tmdb import search_tmdb_movies, fetch_tmdb_movie_by_id
        matches = search_tmdb_movies(api_key, title_query)
        if not matches:
            return None
        return fetch_tmdb_movie_by_id(db, matches[0]["tmdb_id"], api_key)
    except Exception as e:
        print(f"Reference movie TMDb lookup failed: {e}")
        return None


def _score_all_movies_by_intent(db: Session, intent: dict) -> list:
    """
    Fallback candidate generation when there's no reference movie: scores the
    whole local catalog by genre/director/actor overlap plus quality signals.
    """
    all_movies = db.query(Movie).all()
    genres_wanted = set(intent.get("genres") or [])
    director_wanted = (intent.get("director") or "").lower()
    actor_wanted = (intent.get("actor") or "").lower()

    scored = []
    for m in all_movies:
        score = 0.0
        m_genres = set(m.genres or [])
        score += len(genres_wanted.intersection(m_genres)) * 10

        if director_wanted and m.director and director_wanted in m.director.lower():
            score += 8

        if actor_wanted:
            for actor in (m.cast or []):
                if actor_wanted in (actor or "").lower():
                    score += 6
                    break

        score += (m.vote_average or 0) * 0.5
        score += (m.popularity or 0) * 0.01
        scored.append((m, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored]


def _apply_trait_filters(candidates: list, exclude_traits: list) -> list:
    """
    Re-ranks (doesn't hard-drop, so we never return an empty list unnecessarily)
    candidates to push down movies matching genres associated with unwanted traits.
    """
    if not exclude_traits or not candidates:
        return candidates

    avoid_genres = set()
    for trait in exclude_traits:
        avoid_genres.update(TRAIT_GENRE_MAP.get(trait, []))

    if not avoid_genres:
        return candidates

    def penalty(m):
        return len(avoid_genres.intersection(set(m.genres or [])))

    ranked = sorted(candidates, key=penalty)
    min_penalty = penalty(ranked[0])
    filtered = [m for m in ranked if penalty(m) == min_penalty]
    return filtered if filtered else candidates


def _serialize_movies(movies: list) -> list:
    return [{
        "id": m.id,
        "title": m.title,
        "poster_path": m.poster_path,
        "vote_average": m.vote_average,
        "genres": m.genres
    } for m in movies]


def handle_chatbot_query(query: str, db: Session) -> dict:
    """
    Grounded chatbot pipeline:
      1. Extract structured intent (Gemini if available, else heuristics) -
         still used for exclude-trait detection and reference-movie messaging
      2. PRIMARY retrieval: embed the raw query and semantically search the
         catalog directly (semantic_search_movies). This is what actually
         understands meaning ("romcoms that would make you cry", "movies like
         <foreign title not in our catalog>") instead of requiring exact
         keyword/genre matches or a perfectly-resolved reference movie.
      3. If a specific reference movie also resolved, blend in its nearest
         neighbors too so a well-known reference still carries weight.
      4. FALLBACK (no Gemini key, or no embeddings cached yet): the original
         reference-movie / genre-keyword pipeline, unchanged.
      5. Re-rank to respect "avoid X" phrasing (e.g. "less emotional")
      6. Compose a short, grounded reply that only references the retrieved movies
    """
    intent = _extract_intent(query)
    attempted_reference_title = intent.get("reference_movie")

    reference_movie_obj = None
    if intent.get("reference_movie"):
        reference_movie_obj = _find_local_movie(db, intent["reference_movie"])
        if not reference_movie_obj:
            reference_movie_obj = _try_ingest_reference_from_tmdb(db, intent["reference_movie"])

    # Last-resort safety net: even if structured extraction (Gemini or heuristic)
    # found no reference movie at all, check whether the raw query directly names
    # one already in the catalog, or - failing that - try ingesting it from TMDb
    # using the same filler-stripped guess.
    if not reference_movie_obj:
        reference_movie_obj = _scan_query_for_local_title(db, query)
    if not reference_movie_obj and not intent.get("reference_movie"):
        candidate = query.strip()
        for pattern in LEADING_FILLER_PATTERNS:
            stripped = re.sub(pattern, '', candidate, flags=re.IGNORECASE)
            if stripped != candidate:
                candidate = stripped.strip()
                break
        candidate = candidate.rstrip('?.! ').strip()
        if candidate and len(candidate.split()) >= 2:
            attempted_reference_title = candidate
            reference_movie_obj = _try_ingest_reference_from_tmdb(db, candidate)

    # PRIMARY retrieval: semantic search directly against the raw query text.
    # Returns [] (not an error) when Gemini isn't configured or the catalog
    # has no cached embeddings yet, so this cleanly no-ops into the fallback
    # pipeline below rather than needing a try/except here.
    semantic_candidates = semantic_search_movies(query, db, limit=20)
    used_semantic_search = bool(semantic_candidates)

    if used_semantic_search:
        candidates = semantic_candidates
        # Blend in the reference movie's own nearest neighbors too, so a
        # well-known reference still carries its full weight even when the
        # rest of the query was terse (e.g. just "movies like Interstellar").
        if reference_movie_obj:
            ref_similar = get_similar_movies(reference_movie_obj.id, db, limit=10)
            seen_ids = {m.id for m in candidates}
            for m in ref_similar:
                if m.id not in seen_ids:
                    candidates.append(m)
                    seen_ids.add(m.id)
    elif reference_movie_obj:
        candidates = get_similar_movies(reference_movie_obj.id, db, limit=20)
        if not candidates:
            candidates = _score_all_movies_by_intent(db, intent)
    else:
        candidates = _score_all_movies_by_intent(db, intent)

    # Whether this response is actually grounded in something the user asked
    # for - a semantic match (meaning-based), a resolved reference movie, or
    # extracted genre/director/actor signal - as opposed to a blind "just
    # return top-rated movies" fallback with zero connection to the query.
    had_real_signal = used_semantic_search or bool(reference_movie_obj) or bool(intent.get("genres")) \
        or bool(intent.get("director")) or bool(intent.get("actor"))

    candidates = _apply_trait_filters(candidates, intent.get("exclude_traits", []))

    results = candidates[:3]

    if not results:
        all_movies = db.query(Movie).all()
        results = sorted(all_movies, key=lambda x: x.popularity or 0, reverse=True)[:3]

    movies_list_str = "\n".join(
        f"- ID {m.id}: {m.title} (Genres: {', '.join(m.genres)}, Directed by: {m.director}). Overview: {m.overview}"
        for m in results
    )

    # Compose reply with Gemini if available, grounded strictly in `results`
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            reference_line = f'The user referenced the movie "{reference_movie_obj.title}".' if reference_movie_obj else ""
            exclude_line = f"They want to avoid: {', '.join(intent.get('exclude_traits', []))}." if intent.get("exclude_traits") else ""
            honesty_line = ""
            if not had_real_signal:
                if attempted_reference_title:
                    honesty_line = (
                        f'IMPORTANT: You could NOT find "{attempted_reference_title}" in the catalog, and no genre '
                        f"could be determined from the request. Openly say you couldn't find that title yet, "
                        f"then offer these as general acclaimed picks instead - do not claim they are personalized "
                        f"or similar to the request."
                    )
                else:
                    honesty_line = (
                        "IMPORTANT: No specific movie, genre, director, or actor could be determined from this "
                        "request. Openly say so, then offer these as general acclaimed picks instead - do not "
                        "claim they are personalized or similar to the request."
                    )
            prompt = f"""
            You are a helpful, film-expert AI chatbot for our cinematic Movie Recommendation web app (MovieRecs).
            The user asked: "{query}"
            {reference_line}
            {exclude_line}
            {honesty_line}

            Here are the ONLY movies you may recommend (do not mention any movie not in this list):
            {movies_list_str}

            Compose a friendly, engaging response recommending these movies and briefly explain why each fits the request.
            Keep the response to 3-4 sentences max. Mention the movie titles exactly as given above.
            """
            response = model.generate_content(prompt)
            return {
                "message": response.text.strip(),
                "movies": _serialize_movies(results)
            }
        except Exception as e:
            print(f"Gemini API Chatbot Error: {e}")

    # Local fallback message (no LLM available or it errored)
    titles = [m.title for m in results]
    genres_str = ", ".join(results[0].genres) if results else ""

    if not had_real_signal:
        # Be upfront when we have zero actual connection between the query and
        # these results, instead of confidently claiming false relevance.
        if attempted_reference_title:
            prefix = f"I couldn't find \"{attempted_reference_title}\" in our catalog yet, so I can't base a recommendation on it. In the meantime, here are some acclaimed picks: "
        else:
            prefix = "I couldn't pin down a specific movie, genre, or mood from that - here are some acclaimed picks from our catalog instead: "
        if len(titles) >= 2:
            msg = prefix + ", ".join(f"**{t}**" for t in titles[:-1]) + f" and **{titles[-1]}**."
        else:
            msg = prefix + f"**{titles[0]}**."
    elif len(titles) >= 3:
        msg = f"I've searched our catalog and found some fantastic options! Based on similar genres, I highly recommend checking out **{titles[0]}** (a premium {genres_str} movie directed by {results[0].director}). You might also enjoy **{titles[1]}** or **{titles[2]}** for similar vibes!"
    elif len(titles) == 2:
        msg = f"Here are two excellent movies from our catalog: **{titles[0]}** and **{titles[1]}**. Both offer great storylines and fit your request perfectly!"
    else:
        msg = f"I recommend watching **{titles[0]}**. It matches your keywords and offers a superb cinematic experience!"

    return {
        "message": msg,
        "movies": _serialize_movies(results)
    }