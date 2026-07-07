// Deployment-ready: reads the backend URL from a Vite env var so the built
// frontend can point at a real production backend instead of localhost.
// Set VITE_API_BASE_URL in your hosting platform's environment (e.g.
// "https://your-backend.onrender.com/api"). Falls back to localhost for
// local development when the env var isn't set.
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const getHeaders = () => {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token && token !== "undefined" && token !== "null" ? { "Authorization": `Bearer ${token}` } : {}),
  };
};

export const api = {
  get: async (endpoint) => {
    const res = await fetch(`${API_BASE}${endpoint}`, { headers: getHeaders() });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  },
  post: async (endpoint, data) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  },
  delete: async (endpoint) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }
};

const CINEMATIC_FALLBACK_POSTERS = [
  "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=500&auto=format&fit=crop", // Cinema seats
  "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?q=80&w=500&auto=format&fit=crop", // Movie theater
  "https://images.unsplash.com/photo-1478720568477-151d9b147267?q=80&w=500&auto=format&fit=crop", // Projector
  "https://images.unsplash.com/photo-1505686994434-e3cc5abf1330?q=80&w=500&auto=format&fit=crop", // Film canister
  "https://images.unsplash.com/photo-1598899134739-24c46f58b8c0?q=80&w=500&auto=format&fit=crop", // Clapperboard
  "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop", // Vintage camera
  "https://images.unsplash.com/photo-1513151233558-d860c5398176?q=80&w=500&auto=format&fit=crop", // Neon cinema
  "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=500&auto=format&fit=crop"  // Director chair
];

const CINEMATIC_FALLBACK_BACKDROPS = [
  "https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1200&auto=format&fit=crop", // Film projector
  "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1200&auto=format&fit=crop", // Theater
  "https://images.unsplash.com/photo-1478720568477-151d9b147267?q=80&w=1200&auto=format&fit=crop", // Projection room
  "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?q=80&w=1200&auto=format&fit=crop", // Red seats
  "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=1200&auto=format&fit=crop"  // Movie reel
];

export const getFallbackPoster = (movieId) => {
  const index = Math.abs(movieId || 0) % CINEMATIC_FALLBACK_POSTERS.length;
  return CINEMATIC_FALLBACK_POSTERS[index];
};

export const getFallbackBackdrop = (movieId) => {
  const index = Math.abs(movieId || 0) % CINEMATIC_FALLBACK_BACKDROPS.length;
  return CINEMATIC_FALLBACK_BACKDROPS[index];
};

export const getPosterUrl = (path, size = "w500", movieId = null) => {
  if (!path) return getFallbackPoster(movieId);
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `https://image.tmdb.org/t/p/${size}${cleanPath}`;
};

export const getBackdropUrl = (path, size = "original", movieId = null) => {
  if (!path) return getFallbackBackdrop(movieId);
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `https://image.tmdb.org/t/p/${size}${cleanPath}`;
};