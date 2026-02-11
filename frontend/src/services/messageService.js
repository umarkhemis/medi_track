import api from './api';

/**
 * Message Service
 * Handles all message-related API calls
 */

const messageService = {
  /**
   * Get all messages with optional filters
   */
  getMessages: async (params = {}) => {
    const response = await api.get('/messages/', { params });
    return response.data;
  },

  /**
   * Get messages for a specific patient
   */
  getPatientMessages: async (patientId) => {
    const response = await api.get('/messages/', {
      params: { patient: patientId }
    });
    return response.data;
  },

  /**
   * Get a single message by ID
   */
  getMessage: async (id) => {
    const response = await api.get(`/messages/${id}/`);
    return response.data;
  },

  /**
   * Send a new message
   */
  sendMessage: async (messageData) => {
    const response = await api.post('/messages/', messageData);
    return response.data;
  },

  /**
   * Get all message templates
   */
  getTemplates: async (params = {}) => {
    const response = await api.get('/messages/templates/', { params });
    return response.data;
  },

  /**
   * Get a specific template
   */
  getTemplate: async (id) => {
    const response = await api.get(`/messages/templates/${id}/`);
    return response.data;
  },

  /**
   * Get conversation history between provider and patient
   * Groups messages into a conversation thread
   */
  getConversation: async (patientId) => {
    const response = await api.get('/messages/', {
      params: { 
        patient: patientId,
        ordering: '-created_at'
      }
    });
    return response.data;
  },

  /**
   * Get message statistics
   */
  getMessageStats: async () => {
    const response = await api.get('/messages/', {
      params: { page_size: 1000 }
    });
    
    const messages = response.data.results || response.data;
    
    return {
      total: messages.length,
      sent: messages.filter(m => m.direction === 'outbound').length,
      received: messages.filter(m => m.direction === 'inbound').length,
      delivered: messages.filter(m => m.status === 'delivered').length,
      failed: messages.filter(m => m.status === 'failed').length,
    };
  },

  /**
   * Format message with template and patient data
   */
  formatTemplate: (template, patientData) => {
    let content = template.content;
    
    if (patientData) {
      content = content.replace('{patient_name}', patientData.user?.first_name || 'Patient');
      content = content.replace('{first_name}', patientData.user?.first_name || '');
      content = content.replace('{last_name}', patientData.user?.last_name || '');
    }
    
    return content;
  }
};

export default messageService;
