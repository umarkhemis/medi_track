import api from './api';

export const alertService = {
  getAll: async (params = {}) => {
    const response = await api.get('/alerts/', { params });
    return response.data;
  },

  getActive: async () => {
    const response = await api.get('/alerts/active/');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/alerts/${id}/`);
    return response.data;
  },

  acknowledge: async (id) => {
    const response = await api.post(`/alerts/${id}/acknowledge/`);
    return response.data;
  },

  resolve: async (id, resolutionNotes) => {
    const response = await api.post(`/alerts/${id}/resolve/`, {
      resolution_notes: resolutionNotes,
    });
    return response.data;
  },

  update: async (id, alertData) => {
    const response = await api.put(`/alerts/${id}/`, alertData);
    return response.data;
  },
};
