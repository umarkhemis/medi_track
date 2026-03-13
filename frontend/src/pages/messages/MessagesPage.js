import React, { useState, useEffect } from 'react';
import Layout from '../../components/layout/Layout';
import { 
  MessageSquare, Send, Search, Filter, Phone, 
  MessageCircle, Clock, CheckCircle, XCircle, 
  Mail, User, Calendar 
} from 'lucide-react';
import messageService from '../../services/messageService';
import patientService from '../../services/patientService';
import toast from 'react-hot-toast';

const MessagesPage = () => {
  const [messages, setMessages] = useState([]);
  const [patients, setPatients] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [messageContent, setMessageContent] = useState('');
  const [channel, setChannel] = useState('sms');
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    sent: 0,
    received: 0,
    delivered: 0,
    failed: 0
  });

  // Load data
  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load messages
      const messagesData = await messageService.getMessages({ 
        ordering: '-created_at',
        page_size: 100 
      });
      setMessages(messagesData.results || messagesData);

      // Load patients
      const patientsData = await patientService.getPatients({ page_size: 100 });
      setPatients(patientsData.results || patientsData);

      // Load templates
      const templatesData = await messageService.getTemplates({ is_active: true });
      setTemplates(templatesData.results || templatesData);

      // Load stats
      const statsData = await messageService.getMessageStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  // Handle template selection
  const handleTemplateSelect = (e) => {
    const templateId = e.target.value;
    setSelectedTemplate(templateId);
    
    if (templateId) {
      const template = templates.find(t => t.id === parseInt(templateId));
      if (template && selectedPatient) {
        const patient = patients.find(p => p.id === selectedPatient);
        const formatted = messageService.formatTemplate(template, patient);
        setMessageContent(formatted);
      } else if (template) {
        setMessageContent(template.content);
      }
    }
  };

  // Handle patient selection
  const handlePatientSelect = (patientId) => {
    setSelectedPatient(patientId);
    
    // If template is selected, reformat with new patient
    if (selectedTemplate) {
      const template = templates.find(t => t.id === parseInt(selectedTemplate));
      const patient = patients.find(p => p.id === patientId);
      if (template && patient) {
        const formatted = messageService.formatTemplate(template, patient);
        setMessageContent(formatted);
      }
    }
  };

  // Send message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!selectedPatient || !messageContent.trim()) {
      toast.error('Please select a patient and enter a message');
      return;
    }

    setSending(true);
    try {
      await messageService.sendMessage({
        patient: selectedPatient,
        content: messageContent,
        channel: channel,
        direction: 'outbound',
        is_automated: false
      });

      toast.success('Message sent successfully!');
      setMessageContent('');
      setSelectedTemplate('');
      loadData(); // Reload messages
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  // Filter messages
  const filteredMessages = messages.filter(message => {
    const matchesFilter = filter === 'all' || 
      (filter === 'sent' && message.direction === 'outbound') ||
      (filter === 'received' && message.direction === 'inbound') ||
      (filter === 'failed' && message.status === 'failed');
    
    const matchesSearch = searchTerm === '' || 
      message.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.patient_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent':
      case 'delivered':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  // Get channel icon
  const getChannelIcon = (channelType) => {
    return channelType === 'whatsapp' ? 
      <MessageCircle className="w-4 h-4 text-green-600" /> : 
      <Phone className="w-4 h-4 text-blue-600" />;
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
          <p className="text-gray-600 mt-1">SMS and WhatsApp communication with patients</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Messages</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <MessageSquare className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Sent</p>
                <p className="text-2xl font-bold text-gray-900">{stats.sent}</p>
              </div>
              <Send className="w-8 h-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Received</p>
                <p className="text-2xl font-bold text-gray-900">{stats.received}</p>
              </div>
              <Mail className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Delivered</p>
                <p className="text-2xl font-bold text-gray-900">{stats.delivered}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-2xl font-bold text-gray-900">{stats.failed}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Send Message Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Send Message</h2>
              
              <form onSubmit={handleSendMessage} className="space-y-4">
                {/* Patient Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Patient
                  </label>
                  <select
                    value={selectedPatient || ''}
                    onChange={(e) => handlePatientSelect(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Select a patient...</option>
                    {patients.map(patient => (
                      <option key={patient.id} value={patient.id}>
                        {patient.user?.first_name} {patient.user?.last_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Channel Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Channel
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="sms"
                        checked={channel === 'sms'}
                        onChange={(e) => setChannel(e.target.value)}
                        className="mr-2"
                      />
                      <Phone className="w-4 h-4 mr-1" />
                      SMS
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="whatsapp"
                        checked={channel === 'whatsapp'}
                        onChange={(e) => setChannel(e.target.value)}
                        className="mr-2"
                      />
                      <MessageCircle className="w-4 h-4 mr-1" />
                      WhatsApp
                    </label>
                  </div>
                </div>

                {/* Template Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template (Optional)
                  </label>
                  <select
                    value={selectedTemplate}
                    onChange={handleTemplateSelect}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Custom message...</option>
                    {templates.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Message Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message
                  </label>
                  <textarea
                    value={messageContent}
                    onChange={(e) => setMessageContent(e.target.value)}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Type your message here..."
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {messageContent.length} characters
                  </p>
                </div>

                {/* Send Button */}
                <button
                  type="submit"
                  disabled={sending}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {sending ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Send Message
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Message History */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Message History</h2>
                
                {/* Filters */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilter('all')}
                    className={`px-3 py-1 text-sm rounded ${
                      filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setFilter('sent')}
                    className={`px-3 py-1 text-sm rounded ${
                      filter === 'sent' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    Sent
                  </button>
                  <button
                    onClick={() => setFilter('received')}
                    className={`px-3 py-1 text-sm rounded ${
                      filter === 'received' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    Received
                  </button>
                </div>
              </div>

              {/* Search */}
              <div className="mb-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search messages..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Messages List */}
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {loading ? (
                  <div className="text-center py-8 text-gray-500">Loading messages...</div>
                ) : filteredMessages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>No messages found</p>
                  </div>
                ) : (
                  filteredMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`p-4 rounded-lg border ${
                        message.direction === 'outbound'
                          ? 'bg-blue-50 border-blue-200'
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-gray-600" />
                          <span className="font-medium text-gray-900">
                            {message.patient_name || 'Unknown Patient'}
                          </span>
                          {getChannelIcon(message.channel)}
                          <span className="text-xs text-gray-500">
                            {message.channel.toUpperCase()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(message.status)}
                          <span className="text-xs text-gray-500">
                            {formatDate(message.created_at)}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {message.content}
                      </p>
                      <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                        <span className={`px-2 py-1 rounded ${
                          message.direction === 'outbound' 
                            ? 'bg-blue-100 text-blue-700' 
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {message.direction === 'outbound' ? 'Sent' : 'Received'}
                        </span>
                        <span className={`px-2 py-1 rounded ${
                          message.status === 'delivered' ? 'bg-green-100 text-green-700' :
                          message.status === 'failed' ? 'bg-red-100 text-red-700' :
                          'bg-yellow-100 text-yellow-700'
                        }`}>
                          {message.status}
                        </span>
                        {message.is_automated && (
                          <span className="px-2 py-1 rounded bg-purple-100 text-purple-700">
                            Automated
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default MessagesPage;
