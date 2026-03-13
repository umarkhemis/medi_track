import React, { useState } from 'react';
import Layout from '../../components/layout/Layout';
import { AlertTriangle, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const AlertsPage = () => {
  const [filterStatus, setFilterStatus] = useState('all');

  // Mock data - will be replaced with API call
  const alerts = [
    {
      id: 1,
      patient: 'John Doe',
      type: 'red',
      message: 'Critical: Significant shortness of breath reported',
      timestamp: '10 minutes ago',
      status: 'active',
    },
    {
      id: 2,
      patient: 'Charlie Brown',
      type: 'red',
      message: 'High blood pressure reading: 180/110',
      timestamp: '1 hour ago',
      status: 'active',
    },
    {
      id: 3,
      patient: 'Jane Smith',
      type: 'yellow',
      message: 'Moderate: Missed medication dose',
      timestamp: '3 hours ago',
      status: 'acknowledged',
    },
    {
      id: 4,
      patient: 'Mary Johnson',
      type: 'yellow',
      message: 'Elevated glucose levels detected',
      timestamp: '5 hours ago',
      status: 'active',
    },
    {
      id: 5,
      patient: 'Robert Lee',
      type: 'red',
      message: 'Chest pain reported during check-in',
      timestamp: '1 day ago',
      status: 'resolved',
    },
  ];

  const getAlertIcon = (type) => {
    switch (type) {
      case 'red':
        return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'yellow':
        return <AlertCircle className="w-6 h-6 text-yellow-600" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-600" />;
    }
  };

  const getAlertBgColor = (type) => {
    switch (type) {
      case 'red':
        return 'bg-red-50 border-red-200';
      case 'yellow':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Active</span>;
      case 'acknowledged':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Acknowledged</span>;
      case 'resolved':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Resolved</span>;
      default:
        return null;
    }
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (filterStatus === 'all') return true;
    return alert.status === filterStatus;
  });

  const activeCount = alerts.filter(a => a.status === 'active').length;
  const acknowledgedCount = alerts.filter(a => a.status === 'acknowledged').length;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-600 mt-1">Monitor and manage patient alerts</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Alerts</p>
                <p className="text-3xl font-bold text-red-600">{activeCount}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-red-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Acknowledged</p>
                <p className="text-3xl font-bold text-yellow-600">{acknowledgedCount}</p>
              </div>
              <Clock className="w-10 h-10 text-yellow-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Resolved Today</p>
                <p className="text-3xl font-bold text-green-600">{alerts.filter(a => a.status === 'resolved').length}</p>
              </div>
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
          </div>
        </div>

        {/* Filter */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-md ${
                filterStatus === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`px-4 py-2 rounded-md ${
                filterStatus === 'active'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilterStatus('acknowledged')}
              className={`px-4 py-2 rounded-md ${
                filterStatus === 'acknowledged'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Acknowledged
            </button>
            <button
              onClick={() => setFilterStatus('resolved')}
              className={`px-4 py-2 rounded-md ${
                filterStatus === 'resolved'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Resolved
            </button>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <CheckCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">No alerts to display</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded-lg p-6 ${getAlertBgColor(alert.type)}`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    {getAlertIcon(alert.type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {alert.patient}
                        </h3>
                        <p className="text-gray-700 mt-1">{alert.message}</p>
                        <p className="text-sm text-gray-500 mt-2">
                          {alert.timestamp}
                        </p>
                      </div>
                      <div className="flex-shrink-0 ml-4">
                        {getStatusBadge(alert.status)}
                      </div>
                    </div>
                    {alert.status === 'active' && (
                      <div className="mt-4 flex gap-2">
                        <button className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
                          Acknowledge
                        </button>
                        <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                          Resolve
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
};

export default AlertsPage;
