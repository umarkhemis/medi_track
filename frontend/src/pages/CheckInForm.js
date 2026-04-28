import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, AlertTriangle, AlertCircle, ClipboardList } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

/**
 * CheckInForm — patient-facing symptom check-in form.
 *
 * Accessible at /checkin?phone=+256...&checkin_id=123
 * No login required — patients submit via this public form.
 * Can also be accessed by providers on behalf of patients.
 */
const CheckInForm = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [phone, setPhone] = useState(searchParams.get('phone') || '');
  const [checkinId, setCheckinId] = useState(searchParams.get('checkin_id') || '');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [step, setStep] = useState('form'); // 'identify' | 'form' | 'done'

  useEffect(() => {
    loadQuestions();
  }, []);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/checkins/questions/');
      setQuestions(response.data);
      // Pre-initialize responses
      const initial = {};
      response.data.forEach((q) => {
        if (q.type === 'scale') {
          initial[q.key] = '0';
        } else {
          initial[q.key] = q.choices?.[0] || '';
        }
      });
      setResponses(initial);
    } catch (err) {
      console.error('Failed to load questions:', err);
      toast.error('Failed to load check-in questions');
    } finally {
      setLoading(false);
    }
  };

  const handleResponseChange = (key, value) => {
    setResponses((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!phone && !checkinId) {
      toast.error('Please enter your phone number');
      return;
    }
    setSubmitting(true);
    try {
      const payload = { responses };
      if (phone) payload.phone_number = phone;
      if (checkinId) payload.checkin_id = parseInt(checkinId);

      const response = await api.post('/checkins/submit/', payload);
      setResult(response.data);
      setSubmitted(true);
      setStep('done');
    } catch (err) {
      const data = err.response?.data;
      if (data?.error === 'Patient not found') {
        toast.error('Phone number not found. Please check and try again.');
      } else if (data?.message === 'Check-in already completed for today') {
        toast.success('You already submitted your check-in for today!');
        setResult({ status: 'already_completed', risk_level: 'green' });
        setStep('done');
      } else {
        toast.error(data?.error || 'Submission failed. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getRiskConfig = (level) => {
    if (level === 'red') {
      return {
        icon: <AlertCircle className="w-12 h-12 text-red-500" />,
        title: 'Urgent Attention Needed',
        message: 'Your responses indicate you may need medical attention. Your doctor has been notified and will contact you soon.',
        bg: 'bg-red-50',
        border: 'border-red-200',
        badge: 'bg-red-100 text-red-800',
        label: 'High Risk',
      };
    }
    if (level === 'yellow') {
      return {
        icon: <AlertTriangle className="w-12 h-12 text-yellow-500" />,
        title: 'Monitoring Required',
        message: 'Your responses suggest you need some monitoring. Your doctor has been notified and will follow up with you.',
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        badge: 'bg-yellow-100 text-yellow-800',
        label: 'Moderate Risk',
      };
    }
    return {
      icon: <CheckCircle className="w-12 h-12 text-green-500" />,
      title: 'Recovering Well!',
      message: 'Great news — your responses suggest you are recovering normally. Keep taking your medications and rest well.',
      bg: 'bg-green-50',
      border: 'border-green-200',
      badge: 'bg-green-100 text-green-800',
      label: 'Low Risk',
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-600">Loading check-in form...</p>
        </div>
      </div>
    );
  }

  if (step === 'done' && result) {
    const config = getRiskConfig(result.risk_level);
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className={`max-w-md w-full ${config.bg} border ${config.border} rounded-xl p-8 text-center shadow-md`}>
          {config.icon}
          <div className={`inline-block mt-3 px-3 py-1 rounded-full text-sm font-semibold ${config.badge}`}>
            {config.label}
          </div>
          <h2 className="text-xl font-bold text-gray-900 mt-4">{config.title}</h2>
          <p className="text-gray-600 mt-3 leading-relaxed">{config.message}</p>
          <div className="mt-6 p-4 bg-white rounded-lg text-sm text-gray-600">
            <p>✅ Check-in received</p>
            <p className="mt-1">📋 Record updated</p>
            {result.risk_level !== 'green' && <p className="mt-1">🔔 Doctor notified</p>}
          </div>
          <p className="mt-6 text-xs text-gray-400">
            MediTrack — Post-Discharge Patient Monitoring
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <ClipboardList className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Daily Health Check-in</h1>
          <p className="text-gray-600 mt-2">
            Answer a few quick questions to help your doctor monitor your recovery.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Phone identification */}
          {!checkinId && (
            <div className="bg-white rounded-xl shadow p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Phone Number
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                placeholder="+256700000000"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter the phone number registered with your doctor
              </p>
            </div>
          )}

          {/* Questions */}
          {questions.map((q, i) => (
            <div key={q.key} className="bg-white rounded-xl shadow p-6">
              <p className="text-sm text-blue-600 font-medium mb-1">Question {i + 1} of {questions.length}</p>
              <h3 className="text-base font-semibold text-gray-900 mb-4">{q.question}</h3>

              {q.type === 'choice' && (
                <div className="space-y-2">
                  {q.choices.map((choice) => (
                    <label
                      key={choice}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        responses[q.key] === choice
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="radio"
                        name={q.key}
                        value={choice}
                        checked={responses[q.key] === choice}
                        onChange={() => handleResponseChange(q.key, choice)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="text-sm text-gray-800">{choice}</span>
                    </label>
                  ))}
                </div>
              )}

              {q.type === 'scale' && (
                <div>
                  <div className="flex justify-between text-xs text-gray-500 mb-2">
                    <span>No pain (0)</span>
                    <span>Severe pain (10)</span>
                  </div>
                  <input
                    type="range"
                    min={q.min}
                    max={q.max}
                    value={responses[q.key] || 0}
                    onChange={(e) => handleResponseChange(q.key, e.target.value)}
                    className="w-full accent-blue-600"
                  />
                  <div className="flex justify-between mt-1">
                    {Array.from({ length: q.max - q.min + 1 }, (_, i) => i + q.min).map((n) => (
                      <span
                        key={n}
                        className={`text-xs ${
                          parseInt(responses[q.key]) === n
                            ? 'text-blue-600 font-bold'
                            : 'text-gray-400'
                        }`}
                      >
                        {n}
                      </span>
                    ))}
                  </div>
                  <p className="text-center text-2xl font-bold text-blue-600 mt-2">
                    {responses[q.key] || 0}
                  </p>
                </div>
              )}
            </div>
          ))}

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-lg"
          >
            {submitting ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                Submit Check-in
              </>
            )}
          </button>

          <p className="text-center text-xs text-gray-400 pb-4">
            Your responses are private and only visible to your healthcare provider.
          </p>
        </form>
      </div>
    </div>
  );
};

export default CheckInForm;
