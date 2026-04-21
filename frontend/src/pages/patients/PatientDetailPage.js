import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Layout from '../../components/layout/Layout';
import {
  User, ArrowLeft, AlertTriangle, MessageSquare,
  Calendar, Activity, Phone, Clock,
} from 'lucide-react';
import patientService from '../../services/patientService';
import toast from 'react-hot-toast';

const PatientDetailPage = () => {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [checkins, setCheckins] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadPatient();
  }, [id]);

  const loadPatient = async () => {
    setLoading(true);
    try {
      const [patientData, checkinsData, alertsData, messagesData] = await Promise.all([
        patientService.getById(id),
        patientService.getCheckins(id).catch(() => []),
        patientService.getAlerts(id).catch(() => []),
        patientService.getMessages(id).catch(() => []),
      ]);
      setPatient(patientData);
      setCheckins(checkinsData.results || checkinsData);
      setAlerts(alertsData.results || alertsData);
      setMessages(messagesData.results || messagesData);
    } catch (error) {
      console.error('Failed to load patient:', error);
      toast.error('Failed to load patient details');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeColor = (risk) => {
    if (risk === 'red') return 'bg-red-100 text-red-800';
    if (risk === 'yellow') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getRiskLabel = (risk) => {
    if (risk === 'red') return 'High Risk';
    if (risk === 'yellow') return 'Moderate Risk';
    return 'Low Risk';
  };

  const formatCondition = (condition) => {
    const map = {
      heart_failure: 'Heart Failure', copd: 'COPD', diabetes: 'Diabetes',
      hypertension: 'Hypertension', pneumonia: 'Pneumonia', other: 'Other',
    };
    return map[condition] || condition;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString();
  };

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return `${Math.floor(mins / 1440)}d ago`;
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-20 text-gray-500">Loading patient details…</div>
      </Layout>
    );
  }

  if (!patient) {
    return (
      <Layout>
        <div className="text-center py-20">
          <p className="text-gray-500">Patient not found.</p>
          <Link to="/patients" className="mt-4 inline-block text-blue-600 hover:underline">
            Back to Patients
          </Link>
        </div>
      </Layout>
    );
  }

  const fullName = patient.user
    ? `${patient.user.first_name || ''} ${patient.user.last_name || ''}`.trim()
    : patient.user_name || `Patient #${id}`;

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'checkins', label: `Check-ins (${checkins.length})` },
    { key: 'alerts', label: `Alerts (${alerts.length})` },
    { key: 'messages', label: `Messages (${messages.length})` },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        {/* Back nav */}
        <Link
          to="/patients"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Patients
        </Link>

        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start gap-6">
            <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <span className="text-primary-600 font-bold text-xl">
                {fullName.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl font-bold text-gray-900">{fullName}</h1>
                <span
                  className={`px-3 py-1 text-sm font-semibold rounded-full ${getRiskBadgeColor(
                    patient.current_risk_level
                  )}`}
                >
                  {getRiskLabel(patient.current_risk_level)}
                </span>
              </div>
              <p className="text-gray-600 mt-1">{formatCondition(patient.condition)}</p>
              <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500">
                {patient.user?.phone_number && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-4 h-4" /> {patient.user.phone_number}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" /> Discharged: {formatDate(patient.discharge_date)}
                </span>
                {patient.days_since_discharge != null && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" /> {patient.days_since_discharge} days since discharge
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex gap-6">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Medical Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Medical Information</h2>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Condition</dt>
                  <dd className="font-medium">{formatCondition(patient.condition)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Discharge Date</dt>
                  <dd className="font-medium">{formatDate(patient.discharge_date)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Follow-up Date</dt>
                  <dd className="font-medium">{formatDate(patient.follow_up_date)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Monitoring Active</dt>
                  <dd>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        patient.monitoring_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {patient.monitoring_active ? 'Active' : 'Inactive'}
                    </span>
                  </dd>
                </div>
                {patient.discharge_notes && (
                  <div>
                    <dt className="text-gray-500 mb-1">Discharge Notes</dt>
                    <dd className="text-gray-700 bg-gray-50 rounded p-2">
                      {patient.discharge_notes}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Medications */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Medications</h2>
              {patient.medications && patient.medications.length > 0 ? (
                <ul className="space-y-2">
                  {patient.medications.map((med, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                      <span>
                        {typeof med === 'string'
                          ? med
                          : med.name || med.medication || '(unknown medication)'}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500">No medications recorded</p>
              )}

              <h3 className="text-md font-semibold mt-6 mb-3">Emergency Contact</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Name</dt>
                  <dd className="font-medium">{patient.emergency_contact_name || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Phone</dt>
                  <dd className="font-medium">{patient.emergency_contact_phone || '—'}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        {activeTab === 'checkins' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Level</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {checkins.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="px-6 py-10 text-center text-gray-500">
                      No check-ins recorded
                    </td>
                  </tr>
                ) : (
                  checkins.map((ci) => (
                    <tr key={ci.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{formatDate(ci.scheduled_date)}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          ci.status === 'completed' ? 'bg-green-100 text-green-700' :
                          ci.status === 'missed' ? 'bg-red-100 text-red-700' :
                          'bg-yellow-100 text-yellow-700'
                        }`}>
                          {ci.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {ci.risk_score != null ? `${ci.risk_score}/10` : '—'}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {ci.risk_level ? (
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${getRiskBadgeColor(ci.risk_level)}`}>
                            {getRiskLabel(ci.risk_level)}
                          </span>
                        ) : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-10 text-center text-gray-500">
                No alerts for this patient
              </div>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`border rounded-lg p-4 flex items-start gap-3 ${
                    alert.alert_type === 'red'
                      ? 'bg-red-50 border-red-200'
                      : 'bg-yellow-50 border-yellow-200'
                  }`}
                >
                  <AlertTriangle
                    className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                      alert.alert_type === 'red' ? 'text-red-500' : 'text-yellow-500'
                    }`}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{alert.trigger_reason}</p>
                    <p className="text-xs text-gray-500 mt-1">{formatTimeAgo(alert.created_at)}</p>
                  </div>
                  <span className="ml-auto text-xs px-2 py-0.5 rounded bg-white border border-gray-200 text-gray-600">
                    {alert.status}
                  </span>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'messages' && (
          <div className="bg-white rounded-lg shadow p-6 space-y-3 max-h-[600px] overflow-y-auto">
            {messages.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                <MessageSquare className="w-10 h-10 mx-auto mb-2 text-gray-300" />
                No messages yet
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`p-3 rounded-lg ${
                    msg.direction === 'outbound'
                      ? 'bg-blue-50 border border-blue-200 ml-8'
                      : 'bg-gray-50 border border-gray-200 mr-8'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-medium text-gray-600">
                      {msg.direction === 'outbound' ? 'Sent' : 'Received'}
                    </span>
                    <span className="text-xs text-gray-400">{formatTimeAgo(msg.created_at)}</span>
                  </div>
                  <p className="text-sm text-gray-800">{msg.content}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default PatientDetailPage;
