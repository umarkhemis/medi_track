import React from 'react';
import Layout from '../../components/layout/Layout';
import { MessageSquare, Send } from 'lucide-react';

const MessagesPage = () => {
  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
          <p className="text-gray-600 mt-1">Communicate with your patients</p>
        </div>

        {/* Coming Soon */}
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Messaging Feature</h2>
          <p className="text-gray-500 mb-4">
            SMS and WhatsApp messaging integration coming soon
          </p>
          <p className="text-sm text-gray-400">
            This feature will allow you to send check-in reminders and communicate with patients via SMS and WhatsApp
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default MessagesPage;
