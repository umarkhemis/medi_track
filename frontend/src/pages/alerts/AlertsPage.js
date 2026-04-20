import React, { useState, useEffect } from 'react';
import Layout from '../../components/layout/Layout';
import { AlertTriangle, AlertCircle, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import { alertService } from '../../services/alertService';
import toast from 'react-hot-toast';

const AlertsPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [actionLoading, setActionLoading] = useState({});

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await alertService.getAll({ ordering: '-created_at', page_size: 100 });
      setAlerts(data.results || data);
    } catch (error) {
      console.error('Failed to load alerts:', error);
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId) => {
    setActionLoading((prev) => ({ ...prev, [alertId]: 'acknowledging' }));
    try {
      const updated = await alertService.acknowledge(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: updated.status || 'acknowledged' } : a))
      );
      toast.success('Alert acknowledged');
    } catch (error) {
      toast.error('Failed to acknowledge alert');
    } finally {
      setActionLoading((prev) => ({ ...prev, [alertId]: null }));
    }
  };

  const handleResolve = async (alertId) => {
    setActionLoading((prev) => ({ ...prev, [alertId]: 'resolving' }));
    try {
      const updated = await alertService.resolve(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: updated.status || 'resolved' } : a))
      );
      toast.success('Alert resolved');
    } catch (error) {
      toast.error('Failed to resolve alert');
    } finally {
      setActionLoading((prev) => ({ ...prev, [alertId]: null }));
    }
  };

  const getAlertIcon = (type) => {
    if (type === 'red') return <AlertTriangle className="w-6 h-6 text-red-600" />;
    if (type === 'yellow') return <AlertCircle className="w-6 h-6 text-yellow-600" />;
    return <AlertCircle className="w-6 h-6 text-gray-600" />;
  };

  const getAlertBgColor = (type) => {
    if (type === 'red') return 'bg-red-50 border-red-200';
    if (type === 'yellow') return 'bg-yellow-50 border-yellow-200';
    return 'bg-gray-50 border-gray-200';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
            Active
          </span>
        );
      case 'acknowledged':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
            Acknowledged
          </span>
        );
      case 'resolved':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
            Resolved
          </span>
        );
      default:
        return null;
    }
  };

  const formatTimeAgo = (dateString) => {
    if (!dateString) return '';
    const diff = Date.now() - new Date(dateString).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return `${Math.floor(mins / 1440)}d ago`;
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (filterStatus === 'all') return true;
    return alert.status === filterStatus;
  });

  const activeCount = alerts.filter((a) => a.status === 'active').length;
  const acknowledgedCount = alerts.filter((a) => a.status === 'acknowledged').length;
  const resolvedCount = alerts.filter((a) => a.status === 'resolved').length;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
            <p className="text-gray-600 mt-1">Monitor and manage patient alerts</p>
          </div>
          <button
            onClick={loadAlerts}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
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
                <p className="text-sm text-gray-600">Resolved</p>
                <p className="text-3xl font-bold text-green-600">{resolvedCount}</p>
              </div>
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
          </div>
        </div>

        {/* Filter */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex gap-2 flex-wrap">
            {['all', 'active', 'acknowledged', 'resolved'].map((s) => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={`px-4 py-2 rounded-md capitalize ${
                  filterStatus === s
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {loading ? (
            <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
              Loading alerts…
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <CheckCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">No alerts to display</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded-lg p-6 ${getAlertBgColor(alert.alert_type)}`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">{getAlertIcon(alert.alert_type)}</div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {alert.patient_name || `Patient #${alert.patient}`}
                        </h3>
                        <p className="text-gray-700 mt-1">{alert.trigger_reason}</p>
                        {alert.risk_score != null && (
                          <p className="text-sm text-gray-500 mt-1">
                            Risk score: <strong>{alert.risk_score}/10</strong>
                          </p>
                        )}
                        <p className="text-sm text-gray-400 mt-1">
                          {formatTimeAgo(alert.created_at)}
                        </p>
                      </div>
                      <div className="flex-shrink-0 ml-4">{getStatusBadge(alert.status)}</div>
                    </div>

                    {/* Action buttons */}
                    {alert.status === 'active' && (
                      <div className="mt-4 flex gap-2">
                        <button
                          onClick={() => handleAcknowledge(alert.id)}
                          disabled={!!actionLoading[alert.id]}
                          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                        >
                          {actionLoading[alert.id] === 'acknowledging'
                            ? 'Acknowledging…'
                            : 'Acknowledge'}
                        </button>
                        <button
                          onClick={() => handleResolve(alert.id)}
                          disabled={!!actionLoading[alert.id]}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                        >
                          {actionLoading[alert.id] === 'resolving' ? 'Resolving…' : 'Resolve'}
                        </button>
                      </div>
                    )}
                    {alert.status === 'acknowledged' && (
                      <div className="mt-4">
                        <button
                          onClick={() => handleResolve(alert.id)}
                          disabled={!!actionLoading[alert.id]}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                        >
                          {actionLoading[alert.id] === 'resolving' ? 'Resolving…' : 'Resolve'}
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

