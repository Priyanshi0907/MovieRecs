from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    preferred_genres = Column(JSON, default=list)
    preferred_languages = Column(JSON, default=list)
    preferred_actors = Column(JSON, default=list)
    preferred_directors = Column(JSON, default=list)
    preferred_runtime = Column(String, default="90-120 mins")
    preferred_mood = Column(String, default="Feel-good")
    age = Column(Integer, nullable=True)
    region = Column(String, nullable=True)

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=True)
    title = Column(String, index=True, nullable=False)
    genres = Column(JSON, default=list)
    overview = Column(String, nullable=True)
    cast = Column(JSON, default=list)
    director = Column(String, nullable=True)
    poster_path = Column(String, nullable=True)
    backdrop_path = Column(String, nullable=True)
    runtime = Column(Integer, nullable=True)
    vote_average = Column(Float, default=0.0)
    popularity = Column(Float, default=0.0)
    release_date = Column(String, nullable=True)
    budget = Column(Integer, nullable=True)
    revenue = Column(Integer, nullable=True)
    youtube_trailer_id = Column(String, nullable=True)
    streaming_platforms = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    awards = Column(JSON, default=list)
    country = Column(String, nullable=True)
    # Cached Gemini embedding vector (list of floats) for semantic similarity.
    # Nullable so existing rows work fine before backfill; computed lazily and
    # cached here specifically so we never re-call the embedding API for a
    # movie whose content hasn't changed.
    embedding = Column(JSON, nullable=True)

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="Want to Watch")  # "Want to Watch", "Watching", "Completed", "Dropped"

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action = Column(String, nullable=False)  # "viewed", "liked", "disliked", "watched"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())