import React, { useState, useEffect } from 'react';
import Layout from '../../components/layout/Layout';
import { Search, Filter, User, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import patientService from '../../services/patientService';
import toast from 'react-hot-toast';

const PatientsPage = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState('all');

  useEffect(() => {
    loadPatients();
  }, [filterRisk]);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const params = { page_size: 100 };
      if (filterRisk !== 'all') {
        params.current_risk_level = filterRisk;
      }
      const data = await patientService.getPatients(params);
      setPatients(data.results || data);
    } catch (error) {
      console.error('Failed to load patients:', error);
      toast.error('Failed to load patients');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeColor = (risk) => {
    switch (risk) {
      case 'red':    return 'bg-red-100 text-red-800';
      case 'yellow': return 'bg-yellow-100 text-yellow-800';
      case 'green':  return 'bg-green-100 text-green-800';
      default:       return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskLabel = (risk) => {
    switch (risk) {
      case 'red':    return 'High Risk';
      case 'yellow': return 'Moderate';
      case 'green':  return 'Low Risk';
      default:       return 'Unknown';
    }
  };

  const formatCondition = (condition) => {
    const map = {
      heart_failure: 'Heart Failure',
      copd: 'COPD',
      diabetes: 'Diabetes',
      hypertension: 'Hypertension',
      pneumonia: 'Pneumonia',
      other: 'Other',
    };
    return map[condition] || condition;
  };

  const formatFollowUp = (dateStr) => {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    const today = new Date();
    const diffDays = Math.ceil((date - today) / 86400000);
    if (diffDays < 0) return 'Overdue';
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    return `In ${diffDays} days`;
  };

  const getInitials = (name) =>
    name
      ? name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
      : '?';

  const filteredPatients = patients.filter((patient) => {
    const name = patient.user_name || '';
    return name.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
            <p className="text-gray-600 mt-1">Manage and monitor your patients</p>
          </div>
          <button
            onClick={loadPatients}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search patients by name…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Risk Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={filterRisk}
                onChange={(e) => setFilterRisk(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none bg-white"
              >
                <option value="all">All Risks</option>
                <option value="red">High Risk</option>
                <option value="yellow">Moderate Risk</option>
                <option value="green">Low Risk</option>
              </select>
            </div>
          </div>
        </div>

        {/* Patients List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Condition
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Since Discharge
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Next Follow-up
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                      Loading patients…
                    </td>
                  </tr>
                ) : filteredPatients.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <User className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-500">No patients found</p>
                    </td>
                  </tr>
                ) : (
                  filteredPatients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                            <span className="text-primary-600 font-semibold text-sm">
                              {getInitials(patient.user_name)}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {patient.user_name || '—'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCondition(patient.condition)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getRiskBadgeColor(
                            patient.current_risk_level
                          )}`}
                        >
                          {getRiskLabel(patient.current_risk_level)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {patient.days_since_discharge != null
                          ? `${patient.days_since_discharge} days`
                          : '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFollowUp(patient.follow_up_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {patient.provider_name || '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          to={`/patients/${patient.id}`}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default PatientsPage;

