import React, { useState } from 'react';
import { MessageSquare, Phone, Send, CheckCheck, Check, Wifi } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

/**
 * SMSSimulator — realistic SMS/WhatsApp simulation UI.
 *
 * Shows a phone frame with the check-in message as it would appear
 * on a real patient's phone. Can switch between SMS and WhatsApp modes.
 *
 * When real Twilio credentials are in .env, real messages are sent instead.
 */
const SMSSimulator = ({ patient, onCheckInSent }) => {
  const [channel, setChannel] = useState('sms');
  const [sending, setSending] = useState(false);
  const [sentMessages, setSentMessages] = useState([]);

  const handleSendCheckIn = async () => {
    if (!patient) {
      toast.error('Select a patient first');
      return;
    }
    setSending(true);
    try {
      const response = await api.post('/messages/simulator/', {
        patient_id: patient.id,
        channel,
      });
      const preview = response.data.preview;
      setSentMessages((prev) => [preview, ...prev]);
      toast.success(`${channel === 'sms' ? 'SMS' : 'WhatsApp'} check-in sent to ${patient.full_name}`);
      if (onCheckInSent) onCheckInSent(response.data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to send check-in');
    } finally {
      setSending(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isWhatsApp = channel === 'whatsapp';

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Channel Selector */}
      <div className="flex gap-3">
        <button
          onClick={() => setChannel('sms')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
            channel === 'sms'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
          }`}
        >
          <Phone className="w-4 h-4" />
          SMS
        </button>
        <button
          onClick={() => setChannel('whatsapp')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
            channel === 'whatsapp'
              ? 'bg-green-600 text-white border-green-600'
              : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          WhatsApp
        </button>
      </div>

      {/* Phone Frame */}
      <div
        className={`relative w-64 rounded-[2.5rem] border-4 shadow-2xl overflow-hidden ${
          isWhatsApp ? 'border-gray-800 bg-gray-800' : 'border-gray-900 bg-gray-900'
        }`}
        style={{ minHeight: '480px' }}
      >
        {/* Status Bar */}
        <div
          className={`px-5 pt-3 pb-1 flex justify-between items-center text-xs ${
            isWhatsApp ? 'bg-green-700 text-white' : 'bg-gray-900 text-white'
          }`}
        >
          <span className="font-medium">9:41 AM</span>
          <div className="flex items-center gap-1">
            <Wifi className="w-3 h-3" />
            <span>📶</span>
          </div>
        </div>

        {/* App Header */}
        <div
          className={`px-4 py-3 flex items-center gap-3 ${
            isWhatsApp ? 'bg-green-700 text-white' : 'bg-blue-600 text-white'
          }`}
        >
          <div className="w-8 h-8 rounded-full bg-white bg-opacity-30 flex items-center justify-center">
            <span className="text-sm font-bold">M</span>
          </div>
          <div>
            <p className="font-semibold text-sm">MediTrack</p>
            <p className="text-xs opacity-80">
              {isWhatsApp ? 'online' : '+1 (800) MEDITRACK'}
            </p>
          </div>
        </div>

        {/* Messages Area */}
        <div
          className={`flex-1 p-3 space-y-3 min-h-64 ${
            isWhatsApp
              ? 'bg-[#e5ddd5]'
              : 'bg-white'
          }`}
          style={{ minHeight: '300px' }}
        >
          {sentMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-gray-400 text-xs text-center">
              <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
              <p>No messages yet.</p>
              <p>Click "Send Check-in" to simulate.</p>
            </div>
          ) : (
            sentMessages.map((msg, i) => (
              <div key={i} className="flex justify-start">
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-xs shadow-sm ${
                    isWhatsApp
                      ? 'bg-white text-gray-800 rounded-tl-none'
                      : 'bg-blue-600 text-white'
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-wrap">{msg.body}</p>
                  <div className="flex items-center justify-end gap-1 mt-1 opacity-70">
                    <span>{formatTime(msg.sent_at)}</span>
                    {isWhatsApp && (
                      msg.ticks === 2
                        ? <CheckCheck className="w-3 h-3 text-blue-400" />
                        : <Check className="w-3 h-3" />
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input bar */}
        <div
          className={`px-3 py-2 flex items-center gap-2 ${
            isWhatsApp ? 'bg-[#f0f0f0]' : 'bg-gray-100'
          }`}
        >
          <div className="flex-1 bg-white rounded-full px-3 py-1 text-xs text-gray-400 border border-gray-200">
            {isWhatsApp ? 'Type a message' : 'Reply with YES, NO, or STOP'}
          </div>
          <button className={`p-1.5 rounded-full ${isWhatsApp ? 'bg-green-600' : 'bg-blue-600'}`}>
            <Send className="w-3 h-3 text-white" />
          </button>
        </div>
      </div>

      {/* Send Button */}
      <button
        onClick={handleSendCheckIn}
        disabled={sending || !patient}
        className={`w-full max-w-xs py-2.5 px-4 rounded-lg font-medium text-white text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
          isWhatsApp
            ? 'bg-green-600 hover:bg-green-700'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {sending ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Sending...
          </>
        ) : (
          <>
            <Send className="w-4 h-4" />
            Send Check-in {isWhatsApp ? 'WhatsApp' : 'SMS'}
          </>
        )}
      </button>

      {!patient && (
        <p className="text-xs text-gray-400 text-center">Select a patient to send a check-in</p>
      )}

      <p className="text-xs text-gray-400 text-center max-w-xs">
        {isWhatsApp ? '🟢' : '📱'} Simulation mode — no real messages sent.
        Add Twilio credentials to <code className="bg-gray-100 px-1 rounded">.env</code> to send real {isWhatsApp ? 'WhatsApp' : 'SMS'}.
      </p>
    </div>
  );
};

export default SMSSimulator;
