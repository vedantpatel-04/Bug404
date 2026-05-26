import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('shelfiq_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 → redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      sessionStorage.removeItem('shelfiq_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

// ── API functions ──────────────────────────────────

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/api/v1/auth/login', { email, password }),
  logout: () => api.post('/api/v1/auth/logout'),
};

export const alertsAPI = {
  list: (params?: Record<string, unknown>) =>
    api.get('/api/v1/alerts', { params }),
  resolve: (id: number, note: string) =>
    api.post(`/api/v1/alerts/${id}/resolve`, { resolution_note: note }),
};

export const forecastAPI = {
  get: (skuId: string, storeId = 'STORE01') =>
    api.get(`/api/v1/forecast/${skuId}`, { params: { store_id: storeId } }),
  festivalPreview: (eventName: string) =>
    api.get(`/api/v1/forecast/festival-preview/${eventName}`),
};

export const complianceAPI = {
  get: (storeId: string) => api.get(`/api/v1/compliance/${storeId}`),
};

export const analyticsAPI = {
  heatmap: (storeId = 'STORE01') =>
    api.get('/api/v1/analytics/heatmap', { params: { store_id: storeId } }),
  revenueRecovery: (storeId = 'STORE01') =>
    api.get('/api/v1/analytics/revenue-recovery', { params: { store_id: storeId } }),
};

export const eventsAPI = {
  upcoming: () => api.get('/api/v1/events/upcoming'),
};

export const shelvesAPI = {
  get: (storeId: string) => api.get(`/api/v1/shelves/${storeId}`),
};

export const storesAPI = {
  list: () => api.get('/api/v1/stores'),
  create: (data: Record<string, unknown>) => api.post('/api/v1/stores', data),
};

export const healthAPI = {
  check: () => api.get('/health'),
};
