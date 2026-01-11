import api from './api';

export const patientService = {
  getAll: async (params = {}) => {
    const response = await api.get('/patients/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/patients/${id}/`);
    return response.data;
  },

  create: async (patientData) => {
    const response = await api.post('/patients/', patientData);
    return response.data;
  },

  update: async (id, patientData) => {
    const response = await api.put(`/patients/${id}/`, patientData);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/patients/${id}/`);
    return response.data;
  },

  getHighRisk: async () => {
    const response = await api.get('/patients/high-risk/');
    return response.data;
  },

  getPendingResponse: async () => {
    const response = await api.get('/patients/pending-response/');
    return response.data;
  },

  getCheckins: async (id) => {
    const response = await api.get(`/patients/${id}/checkins/`);
    return response.data;
  },

  getAlerts: async (id) => {
    const response = await api.get(`/patients/${id}/alerts/`);
    return response.data;
  },

  getMessages: async (id) => {
    const response = await api.get(`/patients/${id}/messages/`);
    return response.data;
  },
};
