import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Search, Film, LogOut, BarChart3, User, Heart } from 'lucide-react';
import { api, getPosterUrl, getFallbackPoster } from '../api';

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [user, setUser] = useState(null);
  const dropdownRef = useRef(null);
  const profileMenuRef = useRef(null);
  const [ingesting, setIngesting] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const u = await api.get('/auth/me');
        setUser(u);
      } catch (err) {
        console.error("Failed to load user info", err);
      }
    };
    fetchUser();
  }, [location.pathname]);

  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setResults([]);
      return;
    }

    const delayDebounce = setTimeout(async () => {
      try {
        const tmdbKey = localStorage.getItem("tmdb_api_key") || '';
        const url = `/movies/search?q=${searchQuery}${tmdbKey ? `&api_key=${tmdbKey}` : ''}`;
        const data = await api.get(url);
        setResults(data);
      } catch (err) {
        console.error(err);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setShowProfileMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate('/');
  };

  const handleResultClick = async (movie) => {
    setSearchQuery('');
    setShowDropdown(false);
    if (movie.is_local) {
      navigate(`/movie/${movie.id}`);
    } else {
      setIngesting(true);
      try {
        const tmdbKey = localStorage.getItem("tmdb_api_key") || '';
        const res = await api.post('/movies/ingest', {
          tmdb_id: movie.tmdb_id,
          api_key: tmdbKey
        });
        navigate(`/movie/${res.movie_id}`);
      } catch (err) {
        console.error("Failed to ingest movie:", err);
        alert(`Failed to import movie from TMDb: ${err.message || 'Unknown error'}`);
      } finally {
        setIngesting(false);
      }
    }
  };

  return (
    <nav className="fixed top-4 left-0 right-0 mx-auto max-w-7xl z-50 transition-all duration-500 rounded-2xl bg-brand-bg/75 backdrop-blur-md border border-white/10 py-3.5 px-4 sm:px-6 md:px-8 flex items-center justify-between shadow-2xl glass">
      {/* Brand Logo */}
      <div className="flex items-center space-x-8">
        <Link to="/dashboard" className="flex flex-col leading-none hover:scale-105 transition-transform duration-300">
          <span className="text-brand-text text-3xl md:text-4xl font-black tracking-tight font-serif">
            MovieRecs
          </span>
          <span className="text-[10px] md:text-[11px] text-brand-secText mt-1.5 uppercase tracking-widest font-black">
            Advanced AI Movie Recommendation Dashboard
          </span>
        </Link>
        
        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-6 text-xs font-bold uppercase tracking-wider">
          <Link 
            to="/dashboard" 
            className={`hover:text-brand-gold transition-colors duration-300 ${location.pathname === '/dashboard' ? 'text-brand-gold' : 'text-brand-secText'}`}
          >
            Home
          </Link>
          <Link 
            to="/watchlist" 
            className={`hover:text-brand-gold transition-colors duration-300 ${location.pathname === '/watchlist' ? 'text-brand-gold' : 'text-brand-secText'}`}
          >
            Watchlist
          </Link>
          <Link 
            to="/analytics" 
            className={`hover:text-brand-gold transition-colors duration-300 ${location.pathname === '/analytics' ? 'text-brand-gold' : 'text-brand-secText'}`}
          >
            Analytics
          </Link>
        </div>
      </div>

      {/* Right Navigation Panel */}
      <div className="flex items-center space-x-6">
        {/* Search Autocomplete */}
        <div className="relative" ref={dropdownRef}>
          <div className="flex items-center bg-black/40 border border-white/5 rounded-full px-3 py-1.5 w-40 sm:w-56 md:w-64 focus-within:border-brand-gold focus-within:ring-1 focus-within:ring-brand-gold transition-all duration-300">
            <Search className="text-brand-secText w-3.5 h-3.5 mr-2" />
            <input
              type="text"
              placeholder="Search library..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              className="bg-transparent text-xs w-full focus:outline-none text-brand-text placeholder-brand-secText/60"
            />
          </div>

          {/* Autocomplete Dropdown */}
          {showDropdown && results.length > 0 && (
            <div className="absolute right-0 mt-3 w-72 md:w-80 bg-brand-secondary border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 max-h-96 overflow-y-auto glass">
              <div className="px-3 py-2 text-[10px] uppercase font-bold tracking-wider text-brand-secText bg-white/5 border-b border-white/5">
                Suggested Titles
              </div>
              {results.map((m) => (
                <div
                  key={m.is_local ? m.id : `tmdb-${m.tmdb_id}`}
                  onClick={() => handleResultClick(m)}
                  className="flex items-center space-x-3 p-3 hover:bg-white/5 cursor-pointer transition-colors duration-200 border-b border-white/5"
                >
                  <img
                    src={getPosterUrl(m.poster_path, 'w92', m.id)}
                    alt={m.title}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = getFallbackPoster(m.is_local ? m.id : m.tmdb_id);
                    }}
                    className="w-10 h-14 object-cover rounded shadow border border-white/5"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold truncate text-brand-text font-serif">{m.title}</p>
                    {m.is_local ? (
                      <>
                        <p className="text-[10px] text-brand-secText truncate">{m.director} &bull; {m.genres?.slice(0, 2).join(', ')}</p>
                        <p className="text-[10px] text-brand-gold font-bold">{m.vote_average} ⭐</p>
                      </>
                    ) : (
                      <>
                        <p className="text-[10px] text-brand-secText truncate flex items-center space-x-1.5 mt-0.5">
                          <span className="bg-brand-gold/10 text-brand-gold text-[8px] font-bold px-1.5 py-0.5 rounded border border-brand-gold/20 flex items-center">
                            <svg className="w-2.5 h-2.5 mr-1 fill-brand-gold" viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
                            TMDb Import
                          </span>
                          <span>{m.release_date ? `(${m.release_date.split('-')[0]})` : ''}</span>
                        </p>
                        <p className="text-[9px] text-brand-secText/75 italic mt-0.5">Click to import & view details</p>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* User Info & Sign Out */}
        {user && (
          <div className="flex items-center space-x-4">
            <div className="hidden lg:flex flex-col text-right">
              <span className="text-xs font-bold text-brand-text max-w-28 truncate">{user.name}</span>
              <span className="text-[9px] text-brand-gold font-bold uppercase tracking-wider">{user.mood || 'Standard'}</span>
            </div>
            
            <div className="relative" ref={profileMenuRef}>
              <button 
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="flex items-center space-x-1 focus:outline-none p-1.5 rounded-full bg-white/5 border border-white/10 hover:border-brand-gold transition-all duration-300"
              >
                <User className="w-3.5 h-3.5 text-brand-secText" />
              </button>
              
              {/* Profile Dropdown Menu */}
              {showProfileMenu && (
                <div className="absolute right-0 mt-3 w-48 bg-brand-secondary border border-white/10 rounded-xl shadow-2xl py-1 z-50 glass animate-fade-in">
                  <div className="px-4 py-2 border-b border-white/5 text-[10px] uppercase font-bold text-brand-secText">
                    User: <strong className="text-brand-text font-sans">{user.is_guest ? 'Guest' : user.name}</strong>
                  </div>
                  <Link 
                    to="/questionnaire" 
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center px-4 py-2 text-xs text-brand-secText hover:bg-white/5 hover:text-brand-gold transition-colors duration-200"
                  >
                    <Heart className="w-3.5 h-3.5 mr-2" />
                    Preferences Profile
                  </Link>
                  <Link 
                    to="/analytics" 
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center px-4 py-2 text-xs text-brand-secText hover:bg-white/5 hover:text-brand-gold transition-colors duration-200"
                  >
                    <BarChart3 className="w-3.5 h-3.5 mr-2" />
                    Taste Analytics
                  </Link>
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      handleLogout();
                    }}
                    className="flex items-center w-full text-left px-4 py-2 text-xs text-brand-secText hover:bg-white/5 hover:text-brand-gold transition-colors duration-200 border-t border-white/5"
                  >
                    <LogOut className="w-3.5 h-3.5 mr-2" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      {ingesting && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-[9999] flex flex-col items-center justify-center space-y-4 animate-fade-in pointer-events-auto">
          <div className="relative w-14 h-14">
            <div className="absolute inset-0 border-4 border-brand-gold/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-brand-gold border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div className="text-center space-y-1.5">
            <h3 className="text-xs font-black uppercase tracking-widest text-brand-gold animate-pulse">Ingesting Movie</h3>
            <p className="text-[10px] text-brand-secText max-w-[280px] px-4">Connecting to TMDb... Ingesting poster, genres, cast, crew details, and official trailers to local database.</p>
          </div>
        </div>
      )}
    </nav>
  );
}