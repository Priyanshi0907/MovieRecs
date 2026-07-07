import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import MovieCard from './MovieCard';

export default function RecommendationRow({ title, movies, watchlistStatuses, onWatchlistToggle }) {
  const rowRef = useRef(null);

  const handleScroll = (direction) => {
    if (rowRef.current) {
      const { scrollLeft, clientWidth } = rowRef.current;
      const scrollAmount = direction === 'left' ? -clientWidth * 0.75 : clientWidth * 0.75;
      rowRef.current.scrollTo({
        left: scrollLeft + scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (!movies || movies.length === 0) return null;

  return (
    <div className="space-y-3 md:space-y-5 px-6 md:px-16 py-6 relative group">
      {/* Row Title (Serif Typography) */}
      <h2 className="text-xl md:text-3xl font-bold tracking-tight text-brand-text font-serif hover:text-brand-gold transition-colors duration-300 cursor-pointer inline-block">
        {title}
      </h2>

      {/* Row Wrapper */}
      <div className="relative flex items-center">
        {/* Scroll Left Button */}
        <button
          onClick={() => handleScroll('left')}
          className="absolute left-0 h-[85%] w-10 md:w-12 bg-black/60 hover:bg-brand-gold/90 hover:text-black text-brand-secText opacity-0 group-hover:opacity-100 transition-all duration-300 z-30 rounded-r flex items-center justify-center border-y border-r border-white/5 select-none focus:outline-none"
        >
          <ChevronLeft className="w-6 h-6 md:w-8 md:h-8" />
        </button>

        {/* Scroll Container */}
        <div
          ref={rowRef}
          className="flex space-x-5 overflow-x-auto overflow-y-hidden py-3 px-1 no-scrollbar w-full scroll-smooth"
        >
          {movies.map((movie) => (
            <MovieCard
              key={movie.id}
              movie={movie}
              watchlistStatus={watchlistStatuses ? watchlistStatuses[movie.id] : null}
              onWatchlistToggle={onWatchlistToggle}
            />
          ))}
        </div>

        {/* Scroll Right Button */}
        <button
          onClick={() => handleScroll('right')}
          className="absolute right-0 h-[85%] w-10 md:w-12 bg-black/60 hover:bg-brand-gold/90 hover:text-black text-brand-secText opacity-0 group-hover:opacity-100 transition-all duration-300 z-30 rounded-l flex items-center justify-center border-y border-l border-white/5 select-none focus:outline-none"
        >
          <ChevronRight className="w-6 h-6 md:w-8 md:h-8" />
        </button>
      </div>
    </div>
  );
}
