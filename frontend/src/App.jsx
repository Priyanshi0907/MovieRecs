import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Questionnaire from './pages/Questionnaire';
import HomeDashboard from './pages/HomeDashboard';
import MovieDetailPage from './pages/MovieDetailPage';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import WatchlistPage from './pages/WatchlistPage';

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Public Portals */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        
        {/* Recommendation Setup Questionnaire */}
        <Route path="/questionnaire" element={<Questionnaire />} />
        
        {/* Netflix Main Dashboards */}
        <Route path="/dashboard" element={<HomeDashboard />} />
        <Route path="/movie/:id" element={<MovieDetailPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/analytics" element={<AnalyticsDashboard />} />
        
        {/* Fallback redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
