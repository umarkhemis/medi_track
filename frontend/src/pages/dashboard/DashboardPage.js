import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Layout from '../../components/layout/Layout';
import { Activity, Users, AlertTriangle, CheckCircle, Clock, MessageSquare } from 'lucide-react';
import providerService from '../../services/providerService';
import { alertService } from '../../services/alertService';
import toast from 'react-hot-toast';

const DashboardPage = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [dashboard, alerts] = await Promise.all([
        providerService.getMyDashboard().catch(() => null),
        alertService.getAll({ ordering: '-created_at', page_size: 5 }).catch(() => ({ results: [] })),
      ]);

      setDashboardData(dashboard);
      const alertList = alerts.results || alerts;
      setRecentAlerts(Array.isArray(alertList) ? alertList.slice(0, 5) : []);
    } catch (error) {
      console.error('Dashboard load error:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const stats = dashboardData
    ? [
        {
          title: 'Total Patients',
          value: dashboardData.total_patients ?? '—',
          change: `${dashboardData.pending_checkins ?? 0} pending check-ins`,
          icon: Users,
          color: 'bg-blue-500',
        },
        {
          title: 'High Risk',
          value: dashboardData.high_risk_patients ?? '—',
          change: `${dashboardData.active_alerts ?? 0} active alerts`,
          icon: AlertTriangle,
          color: 'bg-red-500',
        },
        {
          title: 'Moderate Risk',
          value: dashboardData.moderate_risk_patients ?? '—',
          change: `${dashboardData.pending_followups ?? 0} follow-ups due`,
          icon: Activity,
          color: 'bg-yellow-500',
        },
        {
          title: 'Low Risk',
          value: dashboardData.low_risk_patients ?? '—',
          change: `${dashboardData.checkin_response_rate ?? 0}% response rate today`,
          icon: CheckCircle,
          color: 'bg-green-500',
        },
      ]
    : [];

  const getAlertBgColor = (type) => {
    if (type === 'red') return 'bg-red-50 border-red-200';
    if (type === 'yellow') return 'bg-yellow-50 border-yellow-200';
    return 'bg-gray-50 border-gray-200';
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

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, Dr. {user?.first_name || user?.username || 'Provider'}!
          </h1>
          <p className="text-gray-600 mt-1">Here's your patient monitoring overview</p>
        </div>

        {/* Stats Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4" />
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-full" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div key={index} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-600">{stat.title}</h3>
                  <div className={`${stat.color} p-2 rounded-lg`}>
                    <stat.icon className="w-5 h-5 text-white" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
                <p className="text-sm text-gray-500">{stat.change}</p>
              </div>
            ))}
          </div>
        )}

        {/* Recent Alerts */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
            <a href="/alerts" className="text-sm text-blue-600 hover:underline">
              View all
            </a>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="text-center text-gray-500 py-4">Loading alerts…</div>
            ) : recentAlerts.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <Activity className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No recent alerts</p>
                <p className="text-sm mt-2">Patient check-ins and alerts will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`flex items-center gap-4 p-4 rounded-lg border ${getAlertBgColor(alert.alert_type)}`}
                  >
                    <AlertTriangle
                      className={`w-5 h-5 flex-shrink-0 ${
                        alert.alert_type === 'red' ? 'text-red-500' : 'text-yellow-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {alert.patient_name || `Patient #${alert.patient}`}
                      </p>
                      <p className="text-sm text-gray-600 truncate">{alert.trigger_reason}</p>
                    </div>
                    <span className="text-xs text-gray-400 whitespace-nowrap">
                      {formatTimeAgo(alert.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;

