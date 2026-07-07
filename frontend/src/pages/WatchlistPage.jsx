import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, getBackdropUrl, getFallbackBackdrop } from '../api';
import NavBar from '../components/NavBar';
import ChatbotWidget from '../components/ChatbotWidget';
import { Bookmark, Star, Trash2, Play } from 'lucide-react';

export default function WatchlistPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const res = await api.get('/watchlist');
      setItems(res);
      setError('');
    } catch (err) {
      console.error(err);
      setError("Failed to fetch watchlist. Ensure Python server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleStatusChange = async (movieId, newStatus) => {
    try {
      await api.post(`/movies/${movieId}/watchlist`, { action: newStatus });
      setItems(prev => {
        if (newStatus === 'remove') {
          return prev.filter(item => item.movie.id !== movieId);
        } else {
          return prev.map(item => item.movie.id === movieId ? { ...item, status: newStatus } : item);
        }
      });
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-brand-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-bold tracking-widest text-brand-secText animate-pulse uppercase">Opening Watchlists...</p>
      </div>
    );
  }

  const statuses = ["Want to Watch", "Watching", "Completed", "Dropped"];

  return (
    <div className="min-h-screen bg-brand-bg text-brand-text pb-20 select-none">
      <NavBar />

      <div className="max-w-6xl mx-auto px-6 pt-28 space-y-8">
        <div className="space-y-1">
          <h1 className="text-3xl font-black uppercase text-brand-text tracking-tight flex items-center font-serif">
            <Bookmark className="w-6 h-6 text-brand-gold mr-2" />
            <span>My Movie Watchlists</span>
          </h1>
          <p className="text-xs text-brand-secText">Manage saved titles, view streaming statuses, and change watch status metrics.</p>
        </div>

        {items.length === 0 ? (
          <div className="bg-brand-secondary/40 border border-white/5 p-12 rounded-2xl text-center space-y-4 glass">
            <Bookmark className="w-12 h-12 text-brand-secText/30 mx-auto" />
            <h3 className="text-lg font-bold text-brand-text font-serif">Your Watchlist is empty</h3>
            <p className="text-xs text-brand-secText max-w-sm mx-auto">Explore recommendations on the dashboard and click the bookmark icon to save films you want to view!</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-6 py-2.5 rounded uppercase tracking-wider transition duration-300 shadow-md"
            >
              Discover Movies
            </button>
          </div>
        ) : (
          <div className="space-y-8 animate-fade-in">
            {statuses.map(status => {
              const statusItems = items.filter(item => item.status === status);
              if (statusItems.length === 0) return null;
              return (
                <div key={status} className="space-y-4">
                  <h3 className="text-xs font-black uppercase tracking-wider text-brand-gold border-l-2 border-brand-gold pl-3">
                    {status} ({statusItems.length})
                  </h3>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {statusItems.map(({ movie }) => (
                      <div
                        key={movie.id}
                        className="bg-brand-secondary border border-white/5 rounded-xl overflow-hidden shadow-lg flex flex-col justify-between group glass"
                      >
                        <div 
                          className="relative cursor-pointer aspect-video bg-zinc-900 overflow-hidden border-b border-white/5"
                          onClick={() => navigate(`/movie/${movie.id}`)}
                        >
                          <img
                            src={getBackdropUrl(movie.backdrop_path)}
                            alt={movie.title}
                            onError={(e) => {
                              e.target.onerror = null;
                              e.target.src = getFallbackBackdrop(movie.id);
                            }}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-black/45 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            <Play className="w-9 h-9 text-brand-gold fill-brand-gold" />
                          </div>
                        </div>

                        <div className="p-4 space-y-3">
                          <div>
                            <h4 
                              onClick={() => navigate(`/movie/${movie.id}`)}
                              className="text-xs sm:text-sm font-bold text-brand-text truncate cursor-pointer hover:text-brand-gold transition font-serif"
                            >
                              {movie.title}
                            </h4>
                            <div className="flex items-center justify-between text-[10px] text-brand-secText pt-0.5 font-bold uppercase tracking-wide">
                              <span>{movie.release_date?.split('-')[0]} &bull; {movie.runtime}m</span>
                              <span className="flex items-center text-brand-gold">
                                <Star className="w-2.5 h-2.5 fill-current mr-0.5" />
                                {movie.vote_average?.toFixed(1)}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-between pt-2.5 border-t border-white/5">
                            <select
                              value={status}
                              onChange={(e) => handleStatusChange(movie.id, e.target.value)}
                              className="bg-black/60 border border-white/10 rounded px-2.5 py-1 text-[10px] focus:outline-none text-brand-text w-32 focus:border-brand-gold"
                            >
                              <option value="Want to Watch">Want to Watch</option>
                              <option value="Watching">Watching</option>
                              <option value="Completed">Completed</option>
                              <option value="Dropped">Dropped</option>
                            </select>

                            <button
                              onClick={() => handleStatusChange(movie.id, 'remove')}
                              className="p-1.5 rounded-full hover:bg-brand-gold/10 text-brand-secText hover:text-brand-gold transition"
                              title="Delete from Watchlist"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <ChatbotWidget />
    </div>
  );
}
