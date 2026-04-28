import React from 'react';

/**
 * StatusBadge — shows green/yellow/red health status with label.
 * Used throughout the dashboard and patient lists.
 */
const StatusBadge = ({ status, size = 'md', showDot = true }) => {
  const config = {
    green: {
      label: 'Low Risk',
      dotColor: 'bg-green-500',
      badgeClass: 'bg-green-100 text-green-800 border-green-200',
    },
    yellow: {
      label: 'Moderate Risk',
      dotColor: 'bg-yellow-500',
      badgeClass: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    },
    red: {
      label: 'High Risk',
      dotColor: 'bg-red-500',
      badgeClass: 'bg-red-100 text-red-800 border-red-200',
    },
  };

  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-3 py-1';
  const dotSize = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2';

  const conf = config[status] || config.green;

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold rounded-full border ${sizeClass} ${conf.badgeClass}`}
    >
      {showDot && (
        <span className={`${dotSize} rounded-full ${conf.dotColor} flex-shrink-0`} />
      )}
      {conf.label}
    </span>
  );
};

export default StatusBadge;
