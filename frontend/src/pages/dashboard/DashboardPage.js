import React from 'react';
import { useAuth } from '../../context/AuthContext';
import Layout from '../../components/layout/Layout';
import { Activity, Users, AlertTriangle, CheckCircle } from 'lucide-react';

const DashboardPage = () => {
  const { user } = useAuth();

  const stats = [
    {
      title: 'Total Patients',
      value: '48',
      change: '+2 from last week',
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      title: 'High Risk',
      value: '5',
      change: '2 new alerts',
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
    {
      title: 'Moderate Risk',
      value: '12',
      change: 'Stable',
      icon: Activity,
      color: 'bg-yellow-500',
    },
    {
      title: 'Low Risk',
      value: '31',
      change: 'All good',
      icon: CheckCircle,
      color: 'bg-green-500',
    },
  ];

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

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          </div>
          <div className="p-6">
            <div className="text-center text-gray-500 py-8">
              <Activity className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No recent activity to display</p>
              <p className="text-sm mt-2">Patient check-ins and alerts will appear here</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
