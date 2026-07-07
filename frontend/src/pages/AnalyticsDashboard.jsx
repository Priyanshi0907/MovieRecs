import React, { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';
import NavBar from '../components/NavBar';
import ChatbotWidget from '../components/ChatbotWidget';
import { BarChart3, TrendingUp, Star, Tv, RefreshCw, Info } from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  AreaChart,
  Area
} from 'recharts';

// How often to silently re-fetch while the page stays open, so the dashboard
// stays reasonably fresh without needing a full websocket/push setup.
const AUTO_REFRESH_INTERVAL_MS = 60000;

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);

  const fetchAnalytics = useCallback(async (isBackgroundRefresh = false) => {
    try {
      if (isBackgroundRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      const res = await api.get('/analytics');
      setData(res);
      setLastUpdated(new Date());
      setError('');
    } catch (err) {
      console.error(err);
      // Don't clobber an already-successful view with an error banner just
      // because a background refresh failed once (e.g. transient network blip).
      if (!isBackgroundRefresh) {
        setError(err.message || "Failed to load user watch analytics.");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics(false);

    // Periodic background refresh while the page is open.
    intervalRef.current = setInterval(() => fetchAnalytics(true), AUTO_REFRESH_INTERVAL_MS);

    // Also refresh whenever the user comes back to this tab, since that's
    // the moment new ratings/watchlist activity from elsewhere is most
    // likely to have happened.
    const handleFocus = () => fetchAnalytics(true);
    window.addEventListener('focus', handleFocus);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      window.removeEventListener('focus', handleFocus);
    };
  }, [fetchAnalytics]);

  const handleManualRefresh = () => {
    fetchAnalytics(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-brand-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-bold tracking-widest text-brand-secText animate-pulse uppercase">Assembling Watch Statistics...</p>
      </div>
    );
  }

  if (error || !data || data.error) {
    return (
      <div className="min-h-screen bg-brand-bg text-brand-text flex flex-col items-center justify-center p-6 text-center space-y-4">
        <BarChart3 className="w-12 h-12 text-brand-gold animate-pulse" />
        <h2 className="text-xl font-bold uppercase tracking-tight text-brand-text">{error || data?.error || "Analytics not available."}</h2>
        <p className="text-xs text-brand-secText max-w-sm mx-auto">Rate at least 3 movies or complete your questionnaire to populate your taste vectors!</p>
        <button
          onClick={handleManualRefresh}
          className="bg-brand-gold hover:bg-brand-lightgold text-black text-xs font-black px-6 py-2.5 rounded uppercase tracking-wider transition duration-300"
        >
          Retry Load
        </button>
      </div>
    );
  }

  // Premium Gold & Metallic Palette
  const COLORS = ['#D4AF37', '#E5C05B', '#AA7C11', '#B89742', '#8F6F16', '#FFDF00', '#C5A059'];

  return (
    <div className="min-h-screen bg-brand-bg text-brand-text pb-20 select-none">
      <NavBar />

      <div className="max-w-6xl mx-auto px-6 pt-28 space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
          <div className="space-y-1">
            <h1 className="text-3xl font-black uppercase text-brand-text tracking-tight flex items-center font-serif">
              <BarChart3 className="w-6 h-6 text-brand-gold mr-2" />
              <span>Taste Analytics Dashboard</span>
            </h1>
            <p className="text-xs text-brand-secText">Discover your streaming distributions, favorite directors, and temporal watch activity.</p>
          </div>

          <div className="flex items-center space-x-3">
            {lastUpdated && (
              <span className="text-[10px] text-brand-secText uppercase tracking-wider font-bold">
                Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
            <button
              onClick={handleManualRefresh}
              disabled={refreshing}
              className="flex items-center space-x-1.5 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-brand-gold text-brand-text text-[10px] font-black uppercase tracking-wider px-3.5 py-2 rounded-lg transition-all duration-200 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Refreshing' : 'Refresh'}</span>
            </button>
          </div>
        </div>

        {/* Transparent notice when showing fallback (Guest) data instead of the current user's own */}
        {data.used_fallback_data && (
          <div className="flex items-start space-x-2.5 bg-brand-gold/5 border border-brand-gold/20 rounded-xl px-4 py-3">
            <Info className="w-4 h-4 text-brand-gold flex-shrink-0 mt-0.5" />
            <p className="text-[11px] text-brand-text leading-relaxed">
              You haven't rated enough movies yet for personalized analytics, so this is showing sample data instead.
              Rate at least 5 movies to see your own taste breakdown here.
            </p>
          </div>
        )}

        {/* Counter cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl flex items-center space-x-4 glass animate-fade-in">
            <div className="p-3.5 rounded-xl bg-brand-gold/10 text-brand-gold">
              <Tv className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] text-brand-secText font-bold uppercase block tracking-wider">Total Movies Rated</span>
              <span className="text-2xl font-black text-brand-text">{data.total_watched}</span>
            </div>
          </div>

          <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl flex items-center space-x-4 glass animate-fade-in">
            <div className="p-3.5 rounded-xl bg-brand-gold/10 text-brand-gold">
              <Star className="w-6 h-6 fill-current" />
            </div>
            <div>
              <span className="text-[10px] text-brand-secText font-bold uppercase block tracking-wider">Average Score Given</span>
              <span className="text-2xl font-black text-brand-text">{data.average_rating} Star</span>
            </div>
          </div>

          <div className="bg-brand-secondary border border-white/5 p-5 rounded-2xl flex items-center space-x-4 glass animate-fade-in">
            <div className="p-3.5 rounded-xl bg-brand-gold/10 text-brand-gold">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] text-brand-secText font-bold uppercase block tracking-wider">Active Watchlist</span>
              <span className="text-2xl font-black text-brand-text">Hybrid Optimized</span>
            </div>
          </div>
        </div>

        {/* Grid charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs font-semibold">
          {/* Chart 1: Favorite Genres (Pie Chart) */}
          <div className="bg-brand-secondary border border-white/5 p-6 rounded-2xl space-y-4 glass">
            <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider">Favorite Genres</h3>
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.favorite_genres}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {data.favorite_genres.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#15151D', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-[10px] text-brand-secText">
              {data.favorite_genres.map((g, idx) => (
                <div key={idx} className="flex items-center justify-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
                  <span className="truncate max-w-16">{g.name} ({g.value})</span>
                </div>
              ))}
            </div>
          </div>

          {/* Chart 2: Genre Distribution Radar Chart */}
          <div className="bg-brand-secondary border border-white/5 p-6 rounded-2xl space-y-4 glass">
            <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider">Genre distribution matrix</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data.radar_distribution}>
                  <PolarGrid stroke="rgba(255,255,255,0.05)" />
                  <PolarAngleAxis dataKey="subject" stroke="#888" tick={{ fontSize: 9 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 'auto']} stroke="#444" tick={{ fontSize: 8 }} />
                  <Radar name="User Preferences" dataKey="A" stroke="#D4AF37" fill="#D4AF37" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: Movies per Year Bar Chart */}
          <div className="bg-brand-secondary border border-white/5 p-6 rounded-2xl space-y-4 glass">
            <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider">Rated Movies per Release Year</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.movies_per_year}>
                  <XAxis dataKey="year" stroke="#555" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#555" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#15151D', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="count" fill="#D4AF37" radius={[4, 4, 0, 0]}>
                    {data.movies_per_year.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#D4AF37' : '#E5C05B'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 4: Watching Activity Timeline Area Chart */}
          <div className="bg-brand-secondary border border-white/5 p-6 rounded-2xl space-y-4 glass">
            <h3 className="text-xs font-black uppercase text-brand-secText tracking-wider">Watching activity timeline</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.watching_activity}>
                  <XAxis dataKey="name" stroke="#555" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#555" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#15151D', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <defs>
                    <linearGradient id="colorWatches" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#D4AF37" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#D4AF37" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="watches" stroke="#D4AF37" fillOpacity={1} fill="url(#colorWatches)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      <ChatbotWidget />
    </div>
  );
}