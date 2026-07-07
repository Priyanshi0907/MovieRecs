import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Star } from 'lucide-react';
import { getPosterUrl, getFallbackPoster } from '../api';

export default function MovieCard({ movie, watchlistStatus, onWatchlistToggle }) {
  const navigate = useNavigate();

  const releaseYear = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';

  return (
    <div
      onClick={() => navigate(`/movie/${movie.id}`)}
      className="relative flex-none w-40 sm:w-48 md:w-56 h-60 sm:h-72 md:h-84 bg-brand-card rounded-xl overflow-hidden cursor-pointer transform transition-all duration-500 hover:scale-105 hover:z-20 border border-white/5 hover:border-brand-gold group shadow-2xl"
    >
      {/* Movie Poster Image */}
      <img
        src={getPosterUrl(movie.poster_path, "w500", movie.id)}
        alt={movie.title}
        loading="lazy"
        onError={(e) => {
          e.target.onerror = null;
          e.target.src = getFallbackPoster(movie.id);
        }}
        className="w-full h-full object-cover group-hover:opacity-30 transition-opacity duration-500"
      />

      {/* Hover Info Overlay */}
      <div className="absolute inset-0 p-4 flex flex-col justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-t from-black via-black/80 to-transparent">
        {/* Top Indicators */}
        <div className="flex justify-between items-start">
          <span className="text-[9px] bg-brand-gold text-black px-2 py-0.5 rounded font-black tracking-wider uppercase">
            {movie.genres?.[0] || 'Drama'}
          </span>
          <div className="flex items-center text-brand-gold text-[11px] font-black bg-black/60 px-2 py-0.5 rounded border border-white/5">
            <Star className="w-3.5 h-3.5 fill-brand-gold mr-1" />
            {movie.vote_average?.toFixed(1) || '0.0'}
          </div>
        </div>

        {/* Bottom Details */}
        <div className="space-y-2">
          <h4 className="text-sm sm:text-base font-black text-brand-text font-serif line-clamp-1 leading-snug">
            {movie.title}
          </h4>

          <div className="flex items-center space-x-2 text-[10px] text-brand-secText font-bold uppercase tracking-wide">
            <span>{releaseYear}</span>
            <span>&bull;</span>
            <span>{movie.runtime ? `${movie.runtime}m` : 'N/A'}</span>
          </div>

          <p className="text-[10px] text-brand-secText line-clamp-3 leading-relaxed">
            {movie.overview}
          </p>
        </div>
      </div>
    </div>
  );
}