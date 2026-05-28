import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  MapPin,
  Utensils,
  Star,
  DollarSign,
  TrendingUp,
  ArrowLeft,
  Navigation,
  Heart,
  Share2,
  MapPinned,
  Phone,
  Clock
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Helper to get cuisine-based images from Unsplash
const getCuisineImage = (cuisine, index) => {
  const c = (cuisine || '').toLowerCase();
  if (c.includes('italian') || c.includes('pizza') || c.includes('pasta')) {
    return `https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&sig=${index}`;
  }
  if (c.includes('indian') || c.includes('biryani') || c.includes('kebab') || c.includes('curry')) {
    return `https://images.unsplash.com/photo-1585938338392-50a599e0217b?w=800&q=80&sig=${index}`;
  }
  if (c.includes('asian') || c.includes('chinese') || c.includes('thai') || c.includes('sushi')) {
    return `https://images.unsplash.com/photo-1563245372-f21724e3856d?w=800&q=80&sig=${index}`;
  }
  if (c.includes('cafe') || c.includes('bakery') || c.includes('dessert') || c.includes('coffee')) {
    return `https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80&sig=${index}`;
  }
  if (c.includes('burger') || c.includes('fast food') || c.includes('american')) {
    return `https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80&sig=${index}`;
  }
  return `https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80&sig=${index}`;
};

// Helper to get popular dishes based on cuisine
const getPopularDishes = (cuisine) => {
  const c = (cuisine || '').toLowerCase();
  if (c.includes('italian')) return ["Truffle Pasta", "Margherita Pizza", "Tiramisu"];
  if (c.includes('indian')) return ["Butter Chicken", "Garlic Naan", "Paneer Tikka"];
  if (c.includes('asian') || c.includes('chinese')) return ["Dim Sum", "Kung Pao Chicken", "Hakka Noodles"];
  if (c.includes('cafe') || c.includes('continental')) return ["Avocado Toast", "Club Sandwich", "Red Velvet Waffle"];
  return ["Chef's Special", "Signature Dish", "House Dessert"];
};

// Helper to get ambiance tags based on rating/cost
const getAmbiance = (rating, cost) => {
  const tags = [];
  if (rating >= 4.3) tags.push("Fine Dining");
  else tags.push("Casual Dining");
  
  if (cost >= 1200) tags.push("Romantic");
  else if (cost <= 500) tags.push("Pocket Friendly");
  else tags.push("Cozy Vibe");
  
  tags.push("Great Service");
  return tags;
};

function App() {
  const [view, setView] = useState("search"); // "search" | "results" | "detail"
  const [selectedItem, setSelectedItem] = useState(null);
  const [location, setLocation] = useState("Bangalore");
  const [cuisine, setCuisine] = useState("");
  const [budget, setBudget] = useState("medium");
  const [minRating, setMinRating] = useState(3.5);
  const [extras, setExtras] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [locationsList, setLocationsList] = useState(["Bangalore", "Mumbai", "Delhi", "Pune", "Hyderabad", "Chennai", "Kolkata"]);
  const [recommendations, setRecommendations] = useState([]);
  const [aiSummary, setAiSummary] = useState("");
  const [warnings, setWarnings] = useState([]);

  // Load locations on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/locations`)
      .then(res => res.json())
      .then(data => {
        if (data.locations && data.locations.length > 0) {
          setLocationsList(data.locations);
          // Set first location as default
          setLocation(data.locations[0]);
        }
      })
      .catch(err => {
        console.error("Failed to load locations from API:", err);
      });
  }, []);

  const enrichResults = (rawRecs, targetLocation) => {
    return rawRecs.map((rec, index) => {
      const mockDistance = `${((parseInt(rec.restaurant_id.substring(0, 4), 16) % 35 + 10) / 10).toFixed(1)} km`;
      const mockReviewCount = (rec.rating * 74 + (parseInt(rec.restaurant_id.substring(4, 6), 16) % 150)).toFixed(0);
      const mockPhone = `+91 80 4${(parseInt(rec.restaurant_id.substring(0, 6), 16) % 9000000 + 1000000)}`;
      const mockAddress = `${rec.name}, Locality Road, ${targetLocation}, India`;
      const cuisineTag = rec.cuisine || 'Continental';

      return {
        ...rec,
        image: getCuisineImage(cuisineTag, index),
        address: mockAddress,
        phone: mockPhone,
        hours: "12:00 PM - 11:30 PM",
        distance: mockDistance,
        reviewCount: parseInt(mockReviewCount),
        popularDishes: getPopularDishes(cuisineTag),
        ambiance: getAmbiance(rec.rating, rec.estimated_cost || 500)
      };
    });
  };

  const handleSubmit = async (e, forceAi = false) => {
    if (e) e.preventDefault();
    setError(null);
    if (forceAi) {
      setIsAiLoading(true);
    } else {
      setIsLoading(true);
    }

    const payload = {
      location: location,
      budget: budget,
      cuisines: cuisine ? cuisine.split(",").map(c => c.trim()).filter(Boolean) : ["Indian"],
      min_rating: minRating,
      extras: extras ? extras.split(",").map(ext => ext.trim()).filter(Boolean) : [],
      top_n: 9
    };

    try {
      const response = await fetch(`${API_BASE}/api/v1/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || "Failed to fetch recommendations.");
      }

      const data = await response.json();
      const enriched = enrichResults(data.recommendations || [], location);
      
      setRecommendations(enriched);
      setAiSummary(data.summary || "");
      setWarnings(data.metadata?.warnings || []);
      
      // Navigate to results
      setView("results");
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong.");
    } finally {
      setIsLoading(false);
      setIsAiLoading(false);
    }
  };

  const handleCardClick = (item) => {
    setSelectedItem(item);
    setView("detail");
  };

  const handleBackToResults = () => {
    setView("results");
    setSelectedItem(null);
  };

  const handleBackToSearch = () => {
    setView("search");
  };

  return (
    <div className="min-h-screen w-full relative overflow-hidden" style={{
      background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)"
    }}>
      {/* Background Glow Mesh */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-rose-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-500/20 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-[1400px] mx-auto p-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-orange-500 flex items-center justify-center shadow-lg shadow-rose-500/20">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-semibold text-white tracking-wide">FlavorIQ</h1>
          </div>
          <p className="text-slate-400 ml-13">AI-powered culinary intelligence for your perfect dining experience</p>
        </motion.div>

        {/* Global Error Banner */}
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }} 
            animate={{ opacity: 1, y: 0 }} 
            className="mb-6 rounded-xl p-4 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-2"
          >
            <span>⚠️ {error}</span>
          </motion.div>
        )}

        {/* 1. Search View */}
        {view === "search" && (
          <div className="grid grid-cols-1 lg:grid-cols-[350px,1fr] gap-6">
            {/* Sidebar form */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <form onSubmit={(e) => handleSubmit(e, false)} className="rounded-2xl p-6 backdrop-blur-xl border border-white/10 sticky top-8" style={{
                background: "rgba(30, 41, 59, 0.7)",
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(244, 63, 94, 0.1)"
              }}>
                <h2 className="text-lg font-semibold text-white mb-6">Preferences</h2>
                
                {/* Location */}
                <div className="mb-5">
                  <label className="block text-sm text-slate-300 mb-2">Location</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10" />
                    <select
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-slate-700/50 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-rose-500/50 transition-all appearance-none cursor-pointer"
                    >
                      {locationsList.map((loc) => (
                        <option key={loc} value={loc} className="bg-slate-800">{loc}</option>
                      ))}
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Cuisine */}
                <div className="mb-5">
                  <label className="block text-sm text-slate-300 mb-2">Cuisine</label>
                  <div className="relative">
                    <Utensils className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="text"
                      value={cuisine}
                      onChange={(e) => setCuisine(e.target.value)}
                      placeholder="e.g. Italian, North Indian"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-700/50 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/50 transition-all"
                    />
                  </div>
                </div>

                {/* Budget */}
                <div className="mb-5">
                  <label className="block text-sm text-slate-300 mb-3">Budget</label>
                  <div className="grid grid-cols-3 gap-2">
                    {["low", "medium", "high"].map((tier) => (
                      <button
                        key={tier}
                        type="button"
                        onClick={() => setBudget(tier)}
                        className={`py-2.5 px-4 rounded-xl capitalize transition-all duration-300 ${
                          budget === tier
                            ? "bg-gradient-to-r from-rose-500 to-orange-500 text-white shadow-lg shadow-rose-500/30 font-semibold"
                            : "bg-slate-700/50 text-slate-300 border border-white/10 hover:border-white/20"
                        }`}
                      >
                        {tier}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Min Rating */}
                <div className="mb-5">
                  <label className="block text-sm text-slate-300 mb-3">
                    Minimum Rating: <span className="text-white font-semibold">{minRating.toFixed(1)}</span>
                  </label>
                  <div className="relative">
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.1"
                      value={minRating}
                      onChange={(e) => setMinRating(parseFloat(e.target.value))}
                      className="w-full h-2 rounded-full appearance-none cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, #f43f5e ${minRating / 5 * 100}%, rgba(71, 85, 105, 0.5) ${minRating / 5 * 100}%)`
                      }}
                    />
                  </div>
                </div>

                {/* Extras */}
                <div className="mb-6">
                  <label className="block text-sm text-slate-300 mb-2">Extras (Optional)</label>
                  <input
                    type="text"
                    value={extras}
                    onChange={(e) => setExtras(e.target.value)}
                    placeholder="e.g. outdoor seating, romantic"
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-700/50 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/50 transition-all"
                  />
                </div>

                {/* Submit buttons */}
                <button
                  type="submit"
                  disabled={isLoading || isAiLoading}
                  className="w-full py-3.5 rounded-full bg-gradient-to-r from-rose-500 to-orange-500 text-white font-semibold hover:shadow-xl hover:shadow-rose-500/30 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Searching...
                    </span>
                  ) : "Find Recommendations"}
                </button>

                <button
                  type="button"
                  onClick={(e) => handleSubmit(e, true)}
                  disabled={isLoading || isAiLoading}
                  className="w-full mt-3 py-3.5 rounded-full bg-slate-700/60 border border-white/10 text-white font-semibold hover:bg-slate-700/80 hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isAiLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-emerald-400 rounded-full animate-spin" />
                      <span>AI Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 text-emerald-400" />
                      <span>Get AI Recommendations</span>
                    </>
                  )}
                </button>
              </form>
            </motion.div>

            {/* Empty view on right */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="flex flex-col items-center justify-center p-12 rounded-2xl border border-white/10 text-center"
              style={{ background: "rgba(30, 41, 59, 0.4)" }}
            >
              <Utensils className="w-16 h-16 text-slate-500 mb-4 animate-bounce" />
              <h3 className="text-xl font-medium text-white mb-2">Ready to Discover?</h3>
              <p className="text-slate-400 max-w-md">Configure your preferences on the left and submit to find the absolute best-suited restaurants powered by our recommendation engine.</p>
            </motion.div>
          </div>
        )}

        {/* 2. Results View */}
        {view === "results" && (
          <div>
            <button
              onClick={handleBackToSearch}
              className="mb-6 flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Search
            </button>

            {/* AI Summary Banner */}
            {aiSummary && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl p-5 backdrop-blur-xl border border-emerald-500/20 mb-6"
                style={{
                  background: "linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05))",
                  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2), 0 0 20px rgba(16, 185, 129, 0.1)"
                }}
              >
                <div className="flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="text-emerald-400 font-semibold mb-1">AI Summary</h3>
                    <p className="text-slate-300 text-sm leading-relaxed">{aiSummary}</p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Warning Banner */}
            {warnings.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl p-4 bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm mb-6 flex flex-col gap-1"
              >
                {warnings.map((warn, i) => (
                  <span key={i}>⚠️ {warn}</span>
                ))}
              </motion.div>
            )}

            {/* Results Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendations.map((item, index) => (
                <motion.div
                  key={item.restaurant_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleCardClick(item)}
                  whileHover={{ scale: 1.02, y: -4 }}
                  className="relative rounded-2xl overflow-hidden backdrop-blur-xl border border-white/10 group hover:border-rose-500/50 transition-all duration-300 cursor-pointer"
                  style={{
                    background: "rgba(30, 41, 59, 0.7)",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
                  }}
                >
                  {/* Rank Badge */}
                  <div className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-orange-500 flex items-center justify-center shadow-lg shadow-rose-500/30">
                    <span className="text-white font-bold text-sm">#{item.rank}</span>
                  </div>

                  {/* Card Image */}
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={item.image}
                      alt={item.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent" />
                  </div>

                  {/* Card Content */}
                  <div className="p-5">
                    <h3 className="text-xl font-semibold text-white mb-2">{item.name}</h3>
                    
                    <div className="flex items-center gap-3 mb-3">
                      <span className="flex items-center gap-1 text-amber-400">
                        <Star className="w-4 h-4 fill-amber-400" />
                        <span className="text-sm font-semibold">{item.rating}</span>
                        <span className="text-slate-400 text-xs">({item.reviewCount})</span>
                      </span>
                      <span className="text-slate-400 text-sm flex items-center gap-1">
                        <Navigation className="w-3 h-3" />
                        {item.distance}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-3">
                      <span className="px-2.5 py-1 rounded-full bg-slate-700/60 border border-white/10 text-xs text-slate-200">
                        {item.cuisine}
                      </span>
                      {item.estimated_cost && (
                        <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-xs text-emerald-300">
                          ₹{item.estimated_cost} for two
                        </span>
                      )}
                    </div>

                    <div className="mb-3">
                      <p className="text-xs text-slate-400 mb-1">Popular:</p>
                      <p className="text-sm text-slate-300">{item.popularDishes.join(", ")}</p>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {item.ambiance.map((tag) => (
                        <span key={tag} className="px-2 py-0.5 rounded-md bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* 3. Detail View */}
        {view === "detail" && selectedItem && (
          <div>
            <button
              onClick={handleBackToResults}
              className="mb-6 flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Results
            </button>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Details & Explanation (left) */}
              <div className="lg:col-span-2 space-y-6">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="relative rounded-2xl overflow-hidden h-96"
                >
                  <img
                    src={selectedItem.image}
                    alt={selectedItem.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />
                  
                  {/* Share & Favorite buttons */}
                  <div className="absolute top-4 right-4 flex gap-2">
                    <button className="w-10 h-10 rounded-full backdrop-blur-xl bg-white/10 border border-white/20 flex items-center justify-center hover:bg-white/20 transition-colors">
                      <Share2 className="w-5 h-5 text-white" />
                    </button>
                    <button className="w-10 h-10 rounded-full backdrop-blur-xl bg-white/10 border border-white/20 flex items-center justify-center hover:bg-rose-500 transition-colors">
                      <Heart className="w-5 h-5 text-white" />
                    </button>
                  </div>

                  {/* Overlay Title Card */}
                  <div className="absolute bottom-0 left-0 right-0 p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-3xl font-bold text-white">{selectedItem.name}</h1>
                      <div className="px-3 py-1 rounded-full bg-gradient-to-br from-rose-500 to-orange-500 shadow-md">
                        <span className="text-white font-semibold text-sm">#{selectedItem.rank}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1 text-amber-400">
                        <Star className="w-5 h-5 fill-amber-400" />
                        <span className="text-lg font-bold">{selectedItem.rating}</span>
                        <span className="text-slate-300">({selectedItem.reviewCount} reviews)</span>
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="text-slate-300">{selectedItem.cuisine}</span>
                      <span className="text-slate-300">•</span>
                      <span className="text-emerald-300">₹{selectedItem.estimated_cost} for two</span>
                    </div>
                  </div>
                </motion.div>

                {/* Ambiance */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="rounded-2xl p-6 backdrop-blur-xl border border-white/10"
                  style={{
                    background: "rgba(30, 41, 59, 0.7)",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
                  }}
                >
                  <h3 className="text-lg font-semibold text-white mb-4">Ambiance & Features</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedItem.ambiance.map((tag) => (
                      <span key={tag} className="px-4 py-2 rounded-full bg-gradient-to-r from-rose-500/20 to-orange-500/20 border border-rose-500/30 text-rose-200 font-medium">
                        {tag}
                      </span>
                    ))}
                  </div>
                </motion.div>

                {/* AI Reasoning */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="rounded-2xl p-6 backdrop-blur-xl border border-emerald-500/20"
                  style={{
                    background: "linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05))",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2)"
                  }}
                >
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-6 h-6 text-emerald-400 mt-1 flex-shrink-0" />
                    <div>
                      <h3 className="text-lg font-semibold text-emerald-400 mb-2">Why AI Recommends This</h3>
                      <p className="text-slate-300 leading-relaxed italic">"{selectedItem.explanation}"</p>
                    </div>
                  </div>
                </motion.div>

                {/* Must Try Dishes */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="rounded-2xl p-6 backdrop-blur-xl border border-white/10"
                  style={{
                    background: "rgba(30, 41, 59, 0.7)",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
                  }}
                >
                  <h3 className="text-lg font-semibold text-white mb-4">Must-Try Dishes</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {selectedItem.popularDishes.map((dish) => (
                      <div key={dish} className="rounded-xl p-4 bg-slate-700/50 border border-white/10 hover:border-orange-500/30 transition-colors">
                        <Utensils className="w-5 h-5 text-orange-400 mb-2" />
                        <p className="text-white font-medium">{dish}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              </div>

              {/* Side Detail Sheet */}
              <div className="space-y-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="rounded-2xl p-6 backdrop-blur-xl border border-white/10 sticky top-8"
                  style={{
                    background: "rgba(30, 41, 59, 0.7)",
                    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)"
                  }}
                >
                  <h3 className="text-lg font-semibold text-white mb-4">Details</h3>
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <MapPinned className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Address</p>
                        <p className="text-sm text-slate-200">{selectedItem.address}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Navigation className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Distance</p>
                        <p className="text-sm text-slate-200">{selectedItem.distance} away</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Phone className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Phone</p>
                        <p className="text-sm text-slate-200">{selectedItem.phone}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Clock className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Hours</p>
                        <p className="text-sm text-slate-200">{selectedItem.hours}</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 space-y-3">
                    <button className="w-full py-3 rounded-full bg-gradient-to-r from-rose-500 to-orange-500 text-white font-semibold hover:shadow-xl hover:shadow-rose-500/30 transition-all duration-300">
                      Reserve Table
                    </button>
                    <button className="w-full py-3 rounded-full bg-slate-700/60 border border-white/10 text-white font-medium hover:bg-slate-700/80 transition-all">
                      Get Directions
                    </button>
                  </div>
                </motion.div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Fullscreen blur loading state */}
      {(isLoading || isAiLoading) && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="relative">
            <div className="w-24 h-24 rounded-full border-4 border-slate-700/50" />
            <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-rose-500 border-r-orange-500 animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-rose-400 animate-pulse" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
