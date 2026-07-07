import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Star, Clock, Calendar, Globe, Award, Heart, ThumbsDown, Bookmark, AlertTriangle, ArrowLeft, Play } from 'lucide-react';
import { api, getPosterUrl, getBackdropUrl, getFallbackPoster, getFallbackBackdrop } from '../api';
import NavBar from '../components/NavBar';
import MovieCard from '../components/MovieCard';
import ChatbotWidget from '../components/ChatbotWidget';

export default function MovieDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [reviewsList, setReviewsList] = useState([]);
  const [newReviewContent, setNewReviewContent] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  const fetchMovieDetail = async () => {
    try {
      setLoading(true);
      const detail = await api.get(`/movies/${id}`);
      setData(detail);
      setReviewsList(detail.reviews || []);
      setError('');
    } catch (err) {
      console.error(err);
      setError("Failed to fetch movie details. Make sure the database is seeded.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!newReviewContent.trim() || submittingReview) return;
    setSubmittingReview(true);
    try {
      const res = await api.post(`/movies/${id}/reviews`, { content: newReviewContent });
      setReviewsList(prev => [res, ...prev]);
      setNewReviewContent('');
    } catch (err) {
      console.error("Failed to submit review:", err);
      alert(`Failed to submit review: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmittingReview(false);
    }
  };

  useEffect(() => {
    fetchMovieDetail();
    window.scrollTo(0, 0);
  }, [id]);

  const handleAction = async (actionName) => {
    if (submittingAction) return;
    setSubmittingAction(true);
    try {
      await api.post(`/movies/${id}/action`, { action: actionName });
      
      setData(prev => {
        const copy = { ...prev };
        if (actionName === 'liked') {
          copy.user_liked = true;
          copy.user_disliked = false;
        } else if (actionName === 'disliked') {
          copy.user_liked = false;
          copy.user_disliked = true;
        }
        return copy;
      });
    } catch (err) {
      console.error("Action submit failed", err);
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleRating = async (ratingVal) => {
    try {
      await api.post(`/movies/${id}/rate`, { rating: ratingVal });
      setData(prev => ({ ...prev, user_rating: ratingVal }));
    } catch (err) {
      console.error("Rating submit failed", err);
    }
  };

  const handleWatchlistChange = async (statusVal) => {
    try {
      await api.post(`/movies/${id}/watchlist`, { action: statusVal });
      setData(prev => ({ ...prev, watchlist_status: statusVal === 'remove' ? null : statusVal }));
    } catch (err) {
      console.error("Watchlist submit failed", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-brand-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-bold tracking-widest text-brand-secText animate-pulse uppercase">Decrypting Cinematic Record...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center p-6 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-brand-gold animate-bounce" />
        <h2 className="text-xl font-bold uppercase tracking-tight text-brand-text">{error || 'Movie not found'}</h2>
        <button 
          onClick={() => navigate('/dashboard')}
          className="bg-white/5 hover:bg-white/10 text-brand-text text-xs font-black px-6 py-2.5 rounded border border-white/5 uppercase tracking-wider transition duration-300 flex items-center space-x-1"
        >
          <ArrowLeft className="w-4 h-4 text-brand-gold" />
          <span>Back to Dashboard</span>
        </button>
      </div>
    );
  }

  const { movie, ai_summary, ai_reviews, explanation, watchlist_status, user_rating, user_liked, user_disliked, similar_movies } = data;

  return (
    <div className="min-h-screen bg-brand-bg text-brand-text pb-20 select-none">
      <NavBar />

      {/* Cinematic Backdrop Banner */}
      <div className="relative w-full h-[50vh] md:h-[65vh] bg-brand-bg overflow-hidden">
        <div className="absolute inset-0">
          <img
            src={getBackdropUrl(movie.backdrop_path)}
            alt={movie.title}
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = getFallbackBackdrop(movie.id);
            }}
            className="w-full h-full object-cover opacity-35"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-brand-bg via-brand-bg/40 to-transparent"></div>
          <div className="absolute inset-0 bg-gradient-to-r from-brand-bg via-transparent to-transparent"></div>
        </div>

        {/* Floating Arrow Back */}
        <button 
          onClick={() => navigate('/dashboard')}
          className="absolute top-24 left-6 md:left-16 flex items-center space-x-1 bg-black/40 border border-white/5 hover:bg-brand-gold hover:text-black px-4 py-2 rounded-full text-xs font-bold transition duration-300 z-30 focus:outline-none"
        >
          <ArrowLeft className="w-4 h-4 text-brand-gold" />
          <span>Dashboard</span>
        </button>
      </div>

      {/* Main Details Section */}
      <div className="max-w-6xl mx-auto px-6 relative z-30 -mt-36 sm:-mt-48 md:-mt-56 grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Poster & Actions */}
        <div className="space-y-6">
          <div className="rounded-xl overflow-hidden shadow-2xl border border-white/5 aspect-[2/3] bg-brand-card">
            <img
              src={getPosterUrl(movie.poster_path, 'w500', movie.id)}
              alt={movie.title}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = getFallbackPoster(movie.id);
              }}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Quick Action Buttons */}
          <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl space-y-4 glass">
            <h4 className="text-[10px] font-extrabold uppercase text-brand-secText tracking-wider">User Action Controls</h4>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => handleAction('liked')}
                className={`py-2 flex flex-col items-center justify-center rounded-lg border text-xs font-bold transition ${
                  user_liked 
                    ? 'border-brand-gold bg-brand-gold/10 text-brand-text' 
                    : 'border-white/5 bg-white/5 text-brand-secText hover:text-white'
                }`}
              >
                <Heart className={`w-4 h-4 mb-1 ${user_liked ? 'fill-brand-gold text-brand-gold' : ''}`} />
                <span>Like</span>
              </button>

              <button
                onClick={() => handleAction('disliked')}
                className={`py-2 flex flex-col items-center justify-center rounded-lg border text-xs font-bold transition ${
                  user_disliked 
                    ? 'border-brand-gold bg-brand-gold/10 text-brand-text' 
                    : 'border-white/5 bg-white/5 text-brand-secText hover:text-white'
                }`}
              >
                <ThumbsDown className={`w-4 h-4 mb-1 ${user_disliked ? 'fill-brand-gold text-brand-gold' : ''}`} />
                <span>Dislike</span>
              </button>

              <button
                onClick={() => handleWatchlistChange(watchlist_status ? 'remove' : 'Want to Watch')}
                className={`py-2 flex flex-col items-center justify-center rounded-lg border text-xs font-bold transition ${
                  watchlist_status 
                    ? 'border-brand-gold bg-brand-gold/10 text-brand-text' 
                    : 'border-white/5 bg-white/5 text-brand-secText hover:text-white'
                }`}
              >
                <Bookmark className={`w-4 h-4 mb-1 ${watchlist_status ? 'fill-brand-text text-brand-text' : ''}`} />
                <span>Save</span>
              </button>
            </div>

            {/* Watchlist dropdown */}
            <div className="space-y-1.5">
              <label className="text-[9px] uppercase font-bold text-brand-secText tracking-wider">Watchlist Status</label>
              <select
                value={watchlist_status || 'none'}
                onChange={(e) => handleWatchlistChange(e.target.value)}
                className="w-full bg-black/60 border border-white/5 rounded-lg text-xs py-2.5 px-3 focus:outline-none focus:border-brand-gold text-brand-text"
              >
                <option value="none">Not in Watchlist</option>
                <option value="Want to Watch">Want to Watch</option>
                <option value="Watching">Watching</option>
                <option value="Completed">Completed</option>
                <option value="Dropped">Dropped</option>
              </select>
            </div>

            {/* Star Ratings Slider */}
            <div className="space-y-1.5 pt-3 border-t border-white/5">
              <div className="flex justify-between items-center">
                <label className="text-[9px] uppercase font-bold text-brand-secText tracking-wider">Your Rating</label>
                <span className="text-xs text-brand-gold font-extrabold">{user_rating ? `${user_rating} Star` : 'Unrated'}</span>
              </div>
              <div className="flex items-center space-x-1.5 justify-between">
                {[1, 2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    onClick={() => handleRating(num)}
                    className="p-1 text-brand-secText hover:text-brand-gold transition-colors"
                  >
                    <Star className={`w-6 h-6 ${user_rating >= num ? 'fill-brand-gold text-brand-gold' : 'text-brand-secText/30'}`} />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* User Written Reviews Section */}
          <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl space-y-4 glass">
            <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider flex items-center space-x-1.5 border-b border-white/5 pb-2">
              <span>Community Reviews & Opinions</span>
            </h3>

            {/* Post Review Form */}
            <form onSubmit={handleSubmitReview} className="space-y-3">
              <textarea
                value={newReviewContent}
                onChange={(e) => setNewReviewContent(e.target.value)}
                placeholder="Share your thoughts or theories on this film..."
                rows="3"
                required
                className="w-full bg-black/60 border border-white/5 rounded-xl text-xs p-3 focus:outline-none focus:border-brand-gold text-brand-text placeholder-brand-secText/30 resize-none"
              ></textarea>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={submittingReview || !newReviewContent.trim()}
                  className="bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-bold px-4 py-2 rounded-lg transition duration-200 uppercase tracking-wider disabled:opacity-50 flex items-center space-x-1"
                >
                  {submittingReview ? 'Posting...' : 'Post Review'}
                </button>
              </div>
            </form>

            {/* Reviews List Feed */}
            <div className="space-y-3.5 pt-2 max-h-80 overflow-y-auto pr-1">
              {reviewsList.length === 0 ? (
                <p className="text-xs text-brand-secText/50 italic text-center py-4">No community reviews posted yet. Write the first one!</p>
              ) : (
                reviewsList.map((r) => (
                  <div key={r.id} className="bg-white/5 border border-white/5 rounded-xl p-3.5 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 rounded-full bg-brand-gold/10 border border-brand-gold/20 flex items-center justify-center text-[10px] font-black text-brand-gold uppercase">
                          {r.user_name ? r.user_name[0] : 'U'}
                        </div>
                        <span className="text-xs font-bold text-brand-text">{r.user_name}</span>
                      </div>
                      <span className="text-[9px] text-brand-secText">{new Date(r.timestamp).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</span>
                    </div>
                    <p className="text-xs text-brand-secText leading-relaxed whitespace-pre-wrap pl-8">{r.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Center/Right Columns: Details & Metadata */}
        <div className="md:col-span-2 space-y-6">
          <div className="space-y-2">
            <h1 className="text-4xl md:text-5xl font-extrabold text-brand-text tracking-tight leading-none uppercase font-serif">
              {movie.title}
            </h1>
            
            <div className="flex flex-wrap items-center gap-3 text-xs text-brand-secText font-semibold pt-1">
              <div className="flex items-center text-brand-gold">
                <Star className="w-4 h-4 fill-current mr-1" />
                <span>{movie.vote_average?.toFixed(1)} / 10 (IMDb)</span>
              </div>
              <span>&bull;</span>
              <div className="flex items-center">
                <Clock className="w-3.5 h-3.5 mr-1 text-brand-gold" />
                <span>{movie.runtime} mins</span>
              </div>
              <span>&bull;</span>
              <div className="flex items-center">
                <Calendar className="w-3.5 h-3.5 mr-1 text-brand-gold" />
                <span>{movie.release_date}</span>
              </div>
              <span>&bull;</span>
              <div className="flex items-center">
                <Globe className="w-3.5 h-3.5 mr-1 text-brand-gold" />
                <span>{movie.country}</span>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-1.5 pt-2">
              {movie.genres?.map((g) => (
                <span key={g} className="bg-white/5 border border-white/5 rounded px-2.5 py-0.5 text-xs text-brand-text font-bold uppercase tracking-wider">
                  {g}
                </span>
              ))}
            </div>
          </div>

          {/* AI Explanation Bar */}
          {explanation && (
            <div className="bg-brand-gold/10 border-l-4 border-brand-gold p-4 rounded-r-xl text-xs sm:text-sm text-brand-text leading-relaxed font-semibold">
              {explanation}
            </div>
          )}

          {/* AI Non-Spoiler Hook */}
          {ai_summary && (
            <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl space-y-2 glass glow-gold">
              <h3 className="text-xs font-black uppercase text-brand-gold tracking-wider flex items-center space-x-1.5">
                <Award className="w-4 h-4 fill-current" />
                <span>AI Cinematic Hook (No Spoilers)</span>
              </h3>
              <p className="text-sm font-medium italic text-brand-text leading-relaxed">
                "{ai_summary}"
              </p>
            </div>
          )}

          {/* Synopsis */}
          <div className="space-y-2">
            <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider">Synopsis</h3>
            <p className="text-xs sm:text-sm text-brand-secText leading-relaxed">
              {movie.overview}
            </p>
          </div>

          {/* Movie Details Grid */}
          <div className="grid grid-cols-2 gap-4 text-xs bg-brand-secondary border border-white/5 p-4 rounded-xl">
            <div>
              <span className="text-brand-secText font-bold uppercase block mb-0.5">Director</span>
              <span className="text-brand-text font-semibold">{movie.director}</span>
            </div>
            <div>
              <span className="text-brand-secText font-bold uppercase block mb-0.5">Key Cast</span>
              <span className="text-brand-text font-semibold">{movie.cast?.join(', ')}</span>
            </div>
            <div>
              <span className="text-brand-secText font-bold uppercase block mb-0.5">Languages</span>
              <span className="text-brand-text font-semibold">{movie.languages?.join(', ')}</span>
            </div>
            <div>
              <span className="text-brand-secText font-bold uppercase block mb-0.5">Streaming Services</span>
              <span className="text-brand-gold font-bold">{movie.streaming_platforms?.join(', ')}</span>
            </div>
            {movie.awards && movie.awards.length > 0 && (
              <div className="col-span-2 border-t border-white/5 pt-2 flex items-start space-x-2">
                <Award className="w-4 h-4 text-brand-gold flex-shrink-0" />
                <div>
                  <span className="text-brand-secText font-bold uppercase block mb-0.5">Accolades</span>
                  <span className="text-brand-text font-semibold">{movie.awards?.join(', ')}</span>
                </div>
              </div>
            )}
          </div>

          {/* YouTube Trailer Frame */}
          {movie.youtube_trailer_id && movie.youtube_trailer_id !== "NO_TRAILER" && (
            <div className="space-y-3">
              <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider flex items-center">
                <Play className="w-4 h-4 mr-1 text-brand-gold fill-brand-gold" />
                <span>Trailer & Video Clips</span>
              </h3>
              <div className="video-responsive rounded-xl overflow-hidden aspect-video border border-white/5 shadow-2xl bg-brand-card">
                <iframe
                  src={`https://www.youtube.com/embed/${movie.youtube_trailer_id}`}
                  title={`${movie.title} Official Trailer`}
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            </div>
          )}



          {/* AI Review Highlights */}
          {ai_reviews && (
            <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl space-y-4 glass">
              <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider flex items-center space-x-1.5 border-b border-white/5 pb-2">
                <span>AI Review & Sentiment Highlights</span>
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2 space-y-3">
                  <div>
                    <span className="text-[9px] text-brand-secText font-bold uppercase block">Audience Consensus</span>
                    <p className="text-xs text-brand-text leading-relaxed font-semibold">{ai_reviews.audience_opinion}</p>
                  </div>
                  <div>
                    <span className="text-[9px] text-green-500 font-bold uppercase block">Most Appreciated Aspect</span>
                    <p className="text-xs text-brand-secText leading-relaxed">&bull; {ai_reviews.most_loved}</p>
                  </div>
                  <div>
                    <span className="text-[9px] text-red-500 font-bold uppercase block">Critique / Note</span>
                    <p className="text-xs text-brand-secText leading-relaxed">&bull; {ai_reviews.most_criticized}</p>
                  </div>
                </div>

                <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col items-center justify-center text-center space-y-1">
                  <span className="text-[9px] text-brand-secText font-bold uppercase">Emotional Tone</span>
                  <div className="text-lg font-black text-brand-gold uppercase tracking-wider animate-pulse">
                    {ai_reviews.tone}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Similar Movies Row */}
      {similar_movies && similar_movies.length > 0 && (
        <div className="mt-16 space-y-4">
          <div className="px-6 md:px-16">
            <h3 className="text-xl md:text-3xl font-bold uppercase text-brand-text tracking-tight border-b border-white/5 pb-2 font-serif">
              People Also Liked (Similar Movies)
            </h3>
          </div>
          <div className="flex space-x-5 overflow-x-auto py-4 px-6 md:px-16 no-scrollbar scroll-smooth">
            {similar_movies.map((sm) => (
              <MovieCard
                key={sm.id}
                movie={sm}
              />
            ))}
          </div>
        </div>
      )}

      {/* Chatbot overlay */}
      <ChatbotWidget />
    </div>
  );
}
