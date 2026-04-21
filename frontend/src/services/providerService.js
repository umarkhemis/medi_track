import api from './api';

const providerService = {
  getAll: async (params = {}) => {
    const response = await api.get('/providers/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/providers/${id}/`);
    return response.data;
  },

  /** Return the provider profile of the currently authenticated user. */
  getMe: async () => {
    const response = await api.get('/providers/me/');
    return response.data;
  },

  /**
   * Return dashboard summary data for the currently authenticated provider.
   * Uses the server-side my_dashboard action so a single request fetches all stats.
   */
  getMyDashboard: async () => {
    const response = await api.get('/providers/my_dashboard/');
    return response.data;
  },

  /** Return dashboard summary data for a specific provider by ID. */
  getDashboard: async (id) => {
    const response = await api.get(`/providers/${id}/dashboard/`);
    return response.data;
  },

  getPatients: async (id) => {
    const response = await api.get(`/providers/${id}/patients/`);
    return response.data;
  },

  updateAvailability: async (id, isAvailable) => {
    const response = await api.put(`/providers/${id}/availability/`, {
      is_available: isAvailable,
    });
    return response.data;
  },
};

export default providerService;
