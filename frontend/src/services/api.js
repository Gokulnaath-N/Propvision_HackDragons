import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000
})

// Add Auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pv_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// ── SEARCH ──────────────────────────────────

export const searchListings = async (query, filters = {}, isNewConversation = false) => {
  // The backend SearchRequest model expects: query, country, city, price_min, price_max, bhk, vastu, conversation_history
  const res = await api.post('/search', {
    query,
    ...filters,
    conversation_history: [] // isNewConversation logic can be expanded here
  })
  
  const data = res.data;
  
  // Transform backend response to match frontend component expectations
  return {
    results: (data.results || []).map(item => ({
      ...item,
      hero_image_url: item.image_url, // Map Backend image_url to hero_image_url
      original_url: item.image_url,   // Search results usually show processed images
      price_formatted: item.price_display,
      match_score: item.match_percentage,
      property_type: item.property_type || "Apartment",
      room_tags: item.component_scores ? Object.keys(item.component_scores) : []
    })),
    extracted_intent: data.parsed_intent || {},
    dynamic_filters: data.parsed_intent || {},
    meta: {
        model_used: data.parsed_intent?._meta?.model_used || "PropVision AI",
        latency_ms: data.search_time_ms || 0,
        reasons: data.parsed_intent?._meta?.reasons || []
    }
  }
}

// ── UPLOAD ──────────────────────────────────

export const uploadImages = async (files, metadata = {}, onProgress) => {
  const formData = new FormData()
  
  // Append images
  files.forEach(file => formData.append('images', file)) // Backend expects 'images'
  
  // Append metadata keys expected by the backend Form(...)
  // listing_id, city, location, price, bhk, vastu
  if (metadata.city) formData.append('city', metadata.city);
  if (metadata.location) formData.append('location', metadata.location);
  if (metadata.price) formData.append('price', metadata.price);
  if (metadata.bhk) formData.append('bhk', metadata.bhk);
  if (metadata.vastu !== undefined) formData.append('vastu', metadata.vastu);
  
  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round(e.loaded * 100 / e.total))
    }
  })
  return res.data
}

// ── JOB STATUS ──────────────────────────────

export const getJobStatus = async (jobId) => {
  const res = await api.get(`/status/${jobId}`)
  return res.data
}

// ── LISTING DETAIL ───────────────────────────

export const getListing = async (listingId) => {
  const res = await api.get(`/listings/${listingId}`)
  return res.data
}

// ── HEALTH CHECK ─────────────────────────────

export const checkHealth = async () => {
  const res = await api.get('/health')
  return res.data
}

// ── MOCKS & STUBS ─────────────────────────────

export const getDiscoverItems = async () => {
    return [
      { id: 1, title: 'Trending in Anna Nagar', icon: '🔥', image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=400&auto=format&fit=crop' },
      { id: 2, title: 'New Vastu Homes', icon: '✨', image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?q=80&w=400&auto=format&fit=crop' },
      { id: 3, title: 'Price Drops in OMR', icon: '📉', image: 'https://images.unsplash.com/photo-1600566753086-00f18efc2291?q=80&w=400&auto=format&fit=crop' },
      { id: 4, title: 'Luxury Villas', icon: '💎', image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=400&auto=format&fit=crop' }
    ]
}

export const getHistory = async () => {
    return [
        { id: 1, query: "2BHK under 80 Lakhs in T Nagar" },
        { id: 2, query: "Villas with private pool OMR" },
        { id: 3, query: "sea facing apartments ECR" }
    ]
}

export default api;
