import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, getPosterUrl, getFallbackPoster } from '../api';
import NavBar from '../components/NavBar';
import MovieCard from '../components/MovieCard';
import ChatbotWidget from '../components/ChatbotWidget';
import {
  AlertTriangle, Sliders, Check, ChevronDown, ChevronUp, Star, Play,
  Award, Compass, Heart, Filter, RotateCcw, Globe, Clock, Calendar, ArrowUpDown, Plus
} from 'lucide-react';

const AVAILABLE_GENRES = ["Action", "Sci-Fi", "Thriller", "Drama", "Romance", "Comedy", "Anime", "Fantasy", "Adventure", "Crime", "Mystery", "Horror"];
const AVAILABLE_MOODS = ["Mind-bending", "Happy", "Sad", "Feel-good", "Dark", "Family"];
const AVAILABLE_LANGUAGES = ["Any", "English", "Japanese", "French", "Spanish", "Korean"];
const AVAILABLE_RUNTIMES = ["Any", "Under 90 mins", "90-120 mins", "Over 2 hours"];
const AVAILABLE_ERAS = ["Any", "2020s", "2010s", "2000s", "90s & older"];
const AVAILABLE_SORTS = ["Recommended", "Rating", "Popularity", "Release Date"];

// Persistent action bar shown BELOW every movie card (outside the card itself).
// The card's own hover overlay stays clean with no buttons.
function MovieCardFooter({ movie, watchlistStatus, onWatchlistToggle, onOpenDetails }) {
  const isSaved = watchlistStatus === 'Want to Watch' || watchlistStatus === 'Watching' || watchlistStatus === 'Completed';
  return (
    <div className="flex items-center justify-between bg-black/40 border border-white/5 rounded-xl px-3 py-2">
      <button
        onClick={() => onOpenDetails(movie.id)}
        className="flex items-center space-x-1.5 text-[10px] font-black text-brand-gold uppercase hover:text-brand-lightgold transition-colors duration-200"
      >
        <Play className="w-3 h-3 fill-current" />
        <span>Details</span>
      </button>

      {onWatchlistToggle && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onWatchlistToggle(movie.id);
          }}
          className="p-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-brand-gold hover:text-black text-white transition-colors duration-200"
        >
          {isSaved ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
        </button>
      )}
    </div>
  );
}

export default function HomeDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [watchlistStatuses, setWatchlistStatuses] = useState({});
  const [watchlistMovies, setWatchlistMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Preference baseline user state
  const [user, setUser] = useState(null);

  // Active filter states for Sidebar
  const [filterGenres, setFilterGenres] = useState([]);
  const [filterMood, setFilterMood] = useState('Any');
  const [filterLanguage, setFilterLanguage] = useState('Any');
  const [filterRuntime, setFilterRuntime] = useState('Any');
  const [filterMinRating, setFilterMinRating] = useState(0);
  const [filterEra, setFilterEra] = useState('Any');
  const [filterSortBy, setFilterSortBy] = useState('Recommended');

  // Filtered results state
  const [filteredMovies, setFilteredMovies] = useState(null);
  const [isFiltering, setIsFiltering] = useState(false);

  // Tab State for default view
  const [activeTab, setActiveTab] = useState('recs');

  const fetchData = async () => {
    try {
      setLoading(true);
      const sectionsData = await api.get('/movies/sections');
      setData(sectionsData);

      const wl = await api.get('/watchlist');
      const statuses = {};
      wl.forEach(item => {
        statuses[item.movie.id] = item.status;
      });
      setWatchlistStatuses(statuses);
      setWatchlistMovies(wl.map(item => item.movie));

      const me = await api.get('/auth/me');
      setUser(me);
      setError('');
    } catch (err) {
      console.error(err);
      setError("Unable to connect to recommendation server. Ensure Python backend is running!");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter Trigger Logic (Cohesive Intersection)
  useEffect(() => {
    const applyFilters = async () => {
      const isGenresActive = filterGenres.length > 0;
      const isMoodActive = filterMood !== 'Any';
      const isLangActive = filterLanguage !== 'Any';
      const isRuntimeActive = filterRuntime !== 'Any';
      const isRatingActive = filterMinRating > 0;
      const isEraActive = filterEra !== 'Any';
      const isSortActive = filterSortBy !== 'Recommended';

      // If no filters are active, clear filteredMovies state to show default dashboard rows
      if (!isGenresActive && !isMoodActive && !isLangActive && !isRuntimeActive && !isRatingActive && !isEraActive && !isSortActive) {
        setFilteredMovies(null);
        return;
      }

      setIsFiltering(true);
      try {
        const res = await api.post('/movies/filter', {
          genres: filterGenres,
          mood: filterMood === 'Any' ? null : filterMood,
          language: filterLanguage === 'Any' ? null : filterLanguage,
          runtime: filterRuntime === 'Any' ? null : filterRuntime,
          min_rating: filterMinRating === 0 ? null : filterMinRating,
          era: filterEra === 'Any' ? null : filterEra,
          sort_by: filterSortBy
        });
        setFilteredMovies(res);
      } catch (err) {
        console.error("Filter request failed", err);
      } finally {
        setIsFiltering(false);
      }
    };

    applyFilters();
  }, [filterGenres, filterMood, filterLanguage, filterRuntime, filterMinRating, filterEra, filterSortBy]);

  const handleWatchlistToggle = async (movieId) => {
    const currentStatus = watchlistStatuses[movieId];
    let nextAction = 'Want to Watch';
    if (currentStatus === 'Want to Watch' || currentStatus === 'Watching' || currentStatus === 'Completed') {
      nextAction = 'remove';
    }

    try {
      await api.post(`/movies/${movieId}/watchlist`, { action: nextAction });
      setWatchlistStatuses(prev => {
        const copy = { ...prev };
        if (nextAction === 'remove') {
          delete copy[movieId];
        } else {
          copy[movieId] = nextAction;
        }
        return copy;
      });

      if (nextAction === 'remove') {
        setWatchlistMovies(prev => prev.filter(m => m.id !== movieId));
      } else {
        // Find movie details in current sections or filtered list
        let movieObj = null;
        if (filteredMovies) {
          movieObj = filteredMovies.find(m => m.id === movieId);
        }
        if (!movieObj && data?.sections) {
          for (const s of data.sections) {
            if (s) {
              const found = s.movies.find(m => m.id === movieId);
              if (found) {
                movieObj = found;
                break;
              }
            }
          }
        }
        if (movieObj) {
          setWatchlistMovies(prev => [...prev, movieObj]);
        }
      }
    } catch (err) {
      console.error("Failed to toggle watchlist", err);
    }
  };

  const handleToggleGenreFilter = (genre) => {
    setFilterGenres(prev => {
      if (prev.includes(genre)) {
        return prev.filter(g => g !== genre);
      } else {
        return [...prev, genre];
      }
    });
  };

  const handleResetFilters = () => {
    setFilterGenres([]);
    setFilterMood('Any');
    setFilterLanguage('Any');
    setFilterRuntime('Any');
    setFilterMinRating(0);
    setFilterEra('Any');
    setFilterSortBy('Recommended');
    setFilteredMovies(null);
  };

  const handleOpenDetails = (movieId) => {
    navigate(`/movie/${movieId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-brand-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-bold tracking-widest text-brand-secText animate-pulse uppercase">Analyzing Taste Clusters...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center p-6 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-brand-gold animate-bounce" />
        <h2 className="text-xl font-bold uppercase tracking-tight text-brand-text">{error}</h2>
        <button
          onClick={fetchData}
          className="bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-6 py-2.5 rounded uppercase tracking-wider transition duration-300 shadow-md"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  // Extract sections for default dashboard
  const recsSection = data?.sections?.find(s => s?.title === "Recommended For You");
  const recommendedMovies = recsSection ? recsSection.movies : [];

  const topPick = recommendedMovies.length > 0 ? recommendedMovies[0] : null;
  const remainingRecs = recommendedMovies.slice(1);

  const hiddenGemsSection = data?.sections?.find(s => s?.title === "Hidden Gems");
  const hiddenGems = hiddenGemsSection ? hiddenGemsSection.movies : [];

  const moodSection = data?.sections?.find(s => s?.title?.startsWith("Mood Boosters"));
  const moodMovies = moodSection ? moodSection.movies : [];

  const trendingSection = data?.sections?.find(s => s?.title === "Trending Today");
  const trendingMovies = trendingSection ? trendingSection.movies : [];

  // Determine active movies for standard tabbed view
  let activeMoviesList = [];
  if (activeTab === 'recs') activeMoviesList = remainingRecs;
  else if (activeTab === 'gems') activeMoviesList = hiddenGems;
  else if (activeTab === 'mood') activeMoviesList = moodMovies;
  else if (activeTab === 'watchlist') activeMoviesList = watchlistMovies;
  else if (activeTab === 'trending') activeMoviesList = trendingMovies;

  const isAnyFilterActive =
    filterGenres.length > 0 ||
    filterMood !== 'Any' ||
    filterLanguage !== 'Any' ||
    filterRuntime !== 'Any' ||
    filterMinRating > 0 ||
    filterEra !== 'Any' ||
    filterSortBy !== 'Recommended';

  return (
    <div className="min-h-screen bg-brand-bg text-brand-text pb-20 select-none">
      <NavBar />

      {/* Main Grid Layout: 2-Column Sidebar Layout */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 pt-32 flex flex-col md:flex-row gap-8">

        {/* ================= LEFT SIDEBAR FILTER PANEL ================= */}
        <div className="w-full md:w-64 md:flex-shrink-0 space-y-6 md:sticky md:top-28 self-start bg-brand-secondary/70 border border-white/5 p-5 rounded-2xl glass shadow-xl md:max-h-[calc(100vh-8rem)] md:overflow-y-auto">

          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div className="flex items-center space-x-2 text-brand-gold">
              <Filter className="w-4 h-4" />
              <h3 className="text-xs font-black uppercase tracking-wider">Taste Filters</h3>
            </div>
            {isAnyFilterActive && (
              <button
                onClick={handleResetFilters}
                className="text-[9px] font-black uppercase text-brand-secText hover:text-brand-gold flex items-center space-x-1 transition duration-150"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            )}
          </div>

          {/* 1. Genres multi-select */}
          <div className="space-y-2">
            <span className="text-[9px] uppercase font-black text-brand-secText tracking-wider block">Genres</span>
            <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1 no-scrollbar">
              {AVAILABLE_GENRES.map((genre) => {
                const isSelected = filterGenres.includes(genre);
                return (
                  <button
                    key={genre}
                    onClick={() => handleToggleGenreFilter(genre)}
                    className={`text-[9px] uppercase font-extrabold px-2.5 py-1.5 rounded-full border transition-all duration-150 ${isSelected
                        ? 'bg-brand-gold border-brand-gold text-black font-black shadow-lg shadow-brand-gold/10'
                        : 'bg-black/40 border-white/5 text-brand-secText hover:border-white/10 hover:text-white'
                      }`}
                  >
                    <span>{genre}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Mood single-select */}
          <div className="space-y-2">
            <span className="text-[9px] uppercase font-black text-brand-secText tracking-wider block">Current Vibe</span>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                onClick={() => setFilterMood('Any')}
                className={`text-[9px] uppercase font-extrabold py-2 rounded-lg border text-center transition-all ${filterMood === 'Any'
                    ? 'bg-brand-gold border-brand-gold text-black font-black'
                    : 'bg-black/40 border-white/5 text-brand-secText hover:border-white/10'
                  }`}
              >
                Any Vibe
              </button>
              {AVAILABLE_MOODS.map((mood) => {
                const isSelected = filterMood === mood;
                return (
                  <button
                    key={mood}
                    onClick={() => setFilterMood(mood)}
                    className={`text-[9px] uppercase font-extrabold py-2 rounded-lg border text-center transition-all ${isSelected
                        ? 'bg-brand-gold border-brand-gold text-black font-black'
                        : 'bg-black/40 border-white/5 text-brand-secText hover:border-white/10'
                      }`}
                  >
                    {mood}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Minimum Rating */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-[9px] uppercase font-black text-brand-secText tracking-wider">
              <span>Min TMDb Rating</span>
              <span className="text-brand-gold font-bold">{filterMinRating === 0 ? 'Any' : `${filterMinRating.toFixed(1)}+`}</span>
            </div>
            <div className="flex items-center space-x-1 bg-black/40 border border-white/5 p-1.5 rounded-lg justify-around">
              {[0, 6.0, 7.0, 8.0].map((val) => (
                <button
                  key={val}
                  onClick={() => setFilterMinRating(val)}
                  className={`text-[9px] font-black px-2.5 py-1 rounded transition-colors ${filterMinRating === val
                      ? 'bg-brand-gold text-black'
                      : 'text-brand-secText hover:text-white'
                    }`}
                >
                  {val === 0 ? 'Any' : `${val}+`}
                </button>
              ))}
            </div>
          </div>

          {/* 4. Runtime */}
          <div className="space-y-2">
            <span className="text-[9px] uppercase font-black text-brand-secText tracking-wider block flex items-center">
              <Clock className="w-3 h-3 mr-1 text-brand-secText" />
              <span>Runtime Limit</span>
            </span>
            <select
              value={filterRuntime}
              onChange={(e) => setFilterRuntime(e.target.value)}
              className="w-full bg-black/40 border border-white/5 rounded-lg p-2.5 text-[10px] text-brand-text uppercase font-black focus:outline-none focus:border-brand-gold transition duration-150 cursor-pointer"
            >
              {AVAILABLE_RUNTIMES.map(r => (
                <option key={r} value={r} className="bg-brand-bg text-brand-text uppercase font-black text-[10px]">{r}</option>
              ))}
            </select>
          </div>

          {/* 5. Language */}
          <div className="space-y-2">
            <span className="text-[9px] uppercase font-black text-brand-secText tracking-wider block flex items-center">
              <Globe className="w-3 h-3 mr-1 text-brand-secText" />
              <span>Language</span>
            </span>
            <select
              value={filterLanguage}
              onChange={(e) => setFilterLanguage(e.target.value)}
              className="w-full bg-black/40 border border-white/5 rounded-lg p-2.5 text-[10px] text-brand-text uppercase font-black focus:outline-none focus:border-brand-gold transition duration-150 cursor-pointer"
            >
              {AVAILABLE_LANGUAGES.map(l => (
                <option key={l} value={l} className="bg-brand-bg text-brand-text uppercase font-black text-[10px]">{l}</option>
              ))}
            </select>
          </div>

          {/* 6. Release Era */}
          <div className="space-y-2">
            <span className="text-[9px] uppercase font-black text-brand-secText tracking-wider block flex items-center">
              <Calendar className="w-3 h-3 mr-1 text-brand-secText" />
              <span>Release Era</span>
            </span>
            <select
              value={filterEra}
              onChange={(e) => setFilterEra(e.target.value)}
              className="w-full bg-black/40 border border-white/5 rounded-lg p-2.5 text-[10px] text-brand-text uppercase font-black focus:outline-none focus:border-brand-gold transition duration-150 cursor-pointer"
            >
              {AVAILABLE_ERAS.map(e => (
                <option key={e} value={e} className="bg-brand-bg text-brand-text uppercase font-black text-[10px]">{e}</option>
              ))}
            </select>
          </div>

          {/* 7. Sort By */}
          <div className="space-y-2 border-t border-white/5 pt-4">
            <span className="text-[9px] uppercase font-black text-brand-secText tracking-wider block flex items-center">
              <ArrowUpDown className="w-3 h-3 mr-1 text-brand-secText" />
              <span>Sort Results</span>
            </span>
            <select
              value={filterSortBy}
              onChange={(e) => setFilterSortBy(e.target.value)}
              className="w-full bg-black/40 border border-brand-gold/20 rounded-lg p-2.5 text-[10px] text-brand-text uppercase font-black focus:outline-none focus:border-brand-gold transition duration-150 cursor-pointer"
            >
              {AVAILABLE_SORTS.map(s => (
                <option key={s} value={s} className="bg-brand-bg text-brand-text uppercase font-black text-[10px]">{s}</option>
              ))}
            </select>
          </div>

        </div>

        {/* ================= RIGHT MAIN CONTENT PANEL ================= */}
        <div className="flex-1 min-w-0 space-y-8">

          {/* DYNAMIC RENDERING: If Filters are Active, show the Filtered Grid, otherwise standard sections */}
          {isAnyFilterActive ? (
            <div className="space-y-6">

              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center space-x-2">
                  <span className="bg-brand-gold text-black px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest">
                    Filtered Grid
                  </span>
                  <span className="text-xs text-brand-secText font-bold">
                    {filteredMovies ? `${filteredMovies.length} matches found` : 'Searching Catalog...'}
                  </span>
                </div>
              </div>

              {isFiltering ? (
                <div className="py-24 text-center flex flex-col items-center justify-center space-y-4">
                  <div className="w-8 h-8 border-3 border-brand-gold border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-xs text-brand-secText font-bold uppercase tracking-widest animate-pulse">Running advanced matrix checks...</p>
                </div>
              ) : !filteredMovies || filteredMovies.length === 0 ? (
                <div className="bg-brand-secondary/40 border border-white/5 rounded-3xl p-16 text-center flex flex-col items-center justify-center space-y-3 glass">
                  <Compass className="w-12 h-12 text-brand-secText/30 animate-pulse" />
                  <h3 className="text-sm font-bold uppercase text-brand-text tracking-wide">No Matches Found</h3>
                  <p className="text-xs text-brand-secText max-w-sm leading-relaxed">
                    We couldn't find any movies matching all of the selected filters simultaneously. Try relaxing your filters or clicking reset!
                  </p>
                  <button
                    onClick={handleResetFilters}
                    className="mt-2 bg-brand-gold hover:bg-brand-lightgold text-black text-[10px] font-black px-5 py-2.5 rounded-lg uppercase tracking-wider transition duration-155 shadow-md"
                  >
                    Reset Filters
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 sm:gap-8">
                  {filteredMovies.map((movie) => (
                    <div key={movie.id} className="flex flex-col space-y-3 font-sans">
                      <div className="w-full h-full flex items-center justify-center">
                        <MovieCard
                          movie={movie}
                          watchlistStatus={watchlistStatuses[movie.id]}
                          onWatchlistToggle={handleWatchlistToggle}
                        />
                      </div>
                      <MovieCardFooter
                        movie={movie}
                        watchlistStatus={watchlistStatuses[movie.id]}
                        onWatchlistToggle={handleWatchlistToggle}
                        onOpenDetails={handleOpenDetails}
                      />
                    </div>
                  ))}
                </div>
              )}

            </div>
          ) : (
            // Default Dashboard View: Hero Pick + Sections
            <div className="space-y-8">

              {/* Featured Top Pick */}
              {topPick && (
                <div className="bg-brand-secondary/80 border border-white/10 rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row gap-8 shadow-2xl relative overflow-hidden glass">
                  <div className="absolute -top-24 -left-24 w-64 h-64 bg-brand-gold/10 rounded-full blur-3xl pointer-events-none"></div>

                  <div
                    onClick={() => navigate(`/movie/${topPick.id}`)}
                    className="w-full md:w-56 flex-shrink-0 rounded-2xl overflow-hidden shadow-2xl border border-white/10 cursor-pointer hover:scale-102 transition-transform duration-300 aspect-[2/3] bg-brand-card"
                  >
                    <img
                      src={getPosterUrl(topPick.poster_path, 'w500', topPick.id)}
                      alt={topPick.title}
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = getFallbackPoster(topPick.id);
                      }}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div className="flex-1 flex flex-col justify-between space-y-4">
                    <div className="space-y-3">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="bg-brand-gold text-black px-3 py-1 rounded-full font-black text-[9px] uppercase tracking-widest shadow-lg shadow-brand-gold/10">
                          🎯 #1 AI Pick Match
                        </span>
                        <div className="flex items-center text-brand-gold font-extrabold text-[11px] bg-black/40 border border-white/5 px-2.5 py-0.5 rounded-full">
                          <Star className="w-3.5 h-3.5 fill-brand-gold mr-1" />
                          <span>{topPick.vote_average?.toFixed(1) || '0.0'} Rating</span>
                        </div>
                        <span className="text-xs text-brand-secText font-bold">
                          {topPick.release_date?.split('-')[0]} &bull; {topPick.runtime} mins
                        </span>
                      </div>

                      <h2
                        onClick={() => navigate(`/movie/${topPick.id}`)}
                        className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-brand-text font-serif uppercase tracking-tight leading-none hover:text-brand-gold cursor-pointer transition-colors pt-1"
                      >
                        {topPick.title}
                      </h2>

                      <div className="flex flex-wrap gap-1.5 pt-0.5">
                        {topPick.genres?.map(g => (
                          <span key={g} className="bg-white/5 border border-white/5 text-brand-secText px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                            {g}
                          </span>
                        ))}
                      </div>

                      <p className="text-sm text-brand-secText leading-relaxed pt-1.5">
                        {topPick.overview}
                      </p>
                    </div>

                    <div className="space-y-4 pt-4 border-t border-white/5">
                      <div className="bg-brand-gold/5 border border-brand-gold/20 p-4 rounded-xl space-y-1 bg-gradient-to-r from-brand-gold/5 to-transparent">
                        <span className="text-[9px] font-black uppercase text-brand-gold tracking-widest block">Recommendation Analysis</span>
                        <p className="text-xs text-brand-text leading-relaxed font-bold">
                          {topPick.explanation || "Matches your movie catalog preferences."}
                        </p>
                      </div>

                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => navigate(`/movie/${topPick.id}`)}
                          className="bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-6 py-3 rounded-lg shadow-lg uppercase tracking-widest transition duration-200 flex items-center space-x-1.5"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                          <span>Watch Trailer & Details</span>
                        </button>
                        <button
                          onClick={() => handleWatchlistToggle(topPick.id)}
                          className="bg-white/5 hover:bg-white/10 text-brand-text border border-white/10 text-xs font-black px-6 py-3 rounded-lg transition duration-200 uppercase tracking-widest"
                        >
                          {watchlistStatuses[topPick.id] === 'Want to Watch' || watchlistStatuses[topPick.id] === 'Watching' ? '✓ Saved' : '+ Save'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tabbed Grid View */}
              <div className="space-y-6">

                <div className="flex border-b border-white/10 text-xs font-black uppercase tracking-wider overflow-x-auto no-scrollbar whitespace-nowrap">
                  <button
                    onClick={() => setActiveTab('recs')}
                    className={`pb-4 px-5 border-b-2 transition-all duration-200 flex items-center space-x-1.5 ${activeTab === 'recs'
                        ? 'border-brand-gold text-brand-gold'
                        : 'border-transparent text-brand-secText hover:text-white'
                      }`}
                  >
                    <Award className="w-3.5 h-3.5" />
                    <span>Tailored Picks</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('gems')}
                    className={`pb-4 px-5 border-b-2 transition-all duration-200 flex items-center space-x-1.5 ${activeTab === 'gems'
                        ? 'border-brand-gold text-brand-gold'
                        : 'border-transparent text-brand-secText hover:text-white'
                      }`}
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>Hidden Gems</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('mood')}
                    className={`pb-4 px-5 border-b-2 transition-all duration-200 flex items-center space-x-1.5 ${activeTab === 'mood'
                        ? 'border-brand-gold text-brand-gold'
                        : 'border-transparent text-brand-secText hover:text-white'
                      }`}
                  >
                    <Heart className="w-3.5 h-3.5" />
                    <span>Mood Boosters</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('trending')}
                    className={`pb-4 px-5 border-b-2 transition-all duration-200 flex items-center space-x-1.5 ${activeTab === 'trending'
                        ? 'border-brand-gold text-brand-gold'
                        : 'border-transparent text-brand-secText hover:text-white'
                      }`}
                  >
                    <Star className="w-3.5 h-3.5" />
                    <span>Trending Today</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('watchlist')}
                    className={`pb-4 px-5 border-b-2 transition-all duration-200 flex items-center space-x-1.5 ${activeTab === 'watchlist'
                        ? 'border-brand-gold text-brand-gold'
                        : 'border-transparent text-brand-secText hover:text-white'
                      }`}
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>My Watchlist ({watchlistMovies.length})</span>
                  </button>
                </div>

                {activeMoviesList.length === 0 ? (
                  <div className="bg-brand-secondary/40 border border-white/5 rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-3 glass">
                    <Compass className="w-12 h-12 text-brand-secText/30 animate-pulse" />
                    <h3 className="text-sm font-bold uppercase text-brand-text tracking-wide">No movies found</h3>
                    <p className="text-xs text-brand-secText max-w-sm leading-relaxed">
                      {activeTab === 'watchlist'
                        ? "Your watchlist is currently empty. Click the save option (+ Save) on any movie to bookmark it here!"
                        : "We couldn't retrieve recommendations for this tab. Try adjusting your Taste filters above to reload recommendations!"}
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 sm:gap-8">
                    {activeMoviesList.map((movie) => (
                      <div key={movie.id} className="flex flex-col space-y-3 font-sans">
                        <div className="w-full h-full flex items-center justify-center">
                          <MovieCard
                            movie={movie}
                            watchlistStatus={watchlistStatuses[movie.id]}
                            onWatchlistToggle={handleWatchlistToggle}
                          />
                        </div>
                        <MovieCardFooter
                          movie={movie}
                          watchlistStatus={watchlistStatuses[movie.id]}
                          onWatchlistToggle={handleWatchlistToggle}
                          onOpenDetails={handleOpenDetails}
                        />
                      </div>
                    ))}
                  </div>
                )}

              </div>

            </div>
          )}

        </div>

      </div>

      <ChatbotWidget />
    </div>
  );
}