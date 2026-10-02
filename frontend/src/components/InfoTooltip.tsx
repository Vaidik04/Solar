import React from 'react';

interface InfoTooltipProps {
  term: string;
  explanation: string;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({ term, explanation }) => {
  return (
    <span className="tooltip-wrapper" title={`${term}: ${explanation}`}>
      <span className="info-tooltip-btn" aria-label={`Explanation for ${term}`}>
        i
      </span>
      <span className="tooltip-bubble" role="tooltip">
        <strong>{term}</strong>
        <div style={{ marginTop: '4px', fontSize: '12px' }}>{explanation}</div>
      </span>
    </span>
  );
};
