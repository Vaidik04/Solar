import React, { useState } from 'react';
import { CheckCircle2, RotateCcw, XCircle, AlertTriangle } from 'lucide-react';

interface OfficerActionBarProps {
  plantId: string;
  lang?: 'en' | 'hi';
  onActionComplete?: (action: 'approve' | 'return' | 'reject', remarks: string) => void;
}

type ActionType = 'approve' | 'return' | 'reject' | null;

export const OfficerActionBar: React.FC<OfficerActionBarProps> = ({
  plantId,
  lang = 'en',
  onActionComplete,
}) => {
  const [remarks, setRemarks] = useState('');
  const [activeModalAction, setActiveModalAction] = useState<ActionType>(null);
  const [lastDecision, setLastDecision] = useState<{ action: string; time: string; remarks: string } | null>(null);

  const handleConfirmAction = () => {
    if (!activeModalAction) return;
    const finalRemarks = remarks.trim() || (activeModalAction === 'approve' ? 'All technical and regulatory parameters verified satisfactory.' : 'Requires correction.');
    
    setLastDecision({
      action: activeModalAction,
      time: new Date().toLocaleTimeString(),
      remarks: finalRemarks,
    });

    if (onActionComplete) {
      onActionComplete(activeModalAction, finalRemarks);
    }

    setActiveModalAction(null);
    setRemarks('');
  };

  return (
    <>
      {/* Sticky Bottom Action Bar */}
      <div className="officer-action-bar no-print">
        {/* Left: Decision note & Last status */}
        <div style={{ flex: '1 1 340px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)' }}>
            {lang === 'hi' ? 'विभागीय अधिकारी सत्यापन एवं निर्णय पटल' : 'Officer Verification & Approval Panel'}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {lastDecision ? (
              <span style={{ color: lastDecision.action === 'approve' ? 'var(--status-green)' : 'var(--status-amber)' }}>
                {lang === 'hi' ? 'अंतिम निर्णय' : 'Last action'}: {lastDecision.action.toUpperCase()} ({lastDecision.time}) — "{lastDecision.remarks}"
              </span>
            ) : (
              (lang === 'hi'
                ? 'संयंत्र आईडी: ' + plantId + ' • निरीक्षण प्रतिवेदन एवं नेट मीटर की पुष्टि उपरांत निर्णय लें।'
                : 'Plant ID: ' + plantId + ' • Record official verification decision after checking WCR & net meter.')
            )}
          </div>
        </div>

        {/* Centre: Quick Remarks Input */}
        <div style={{ flex: '2 1 380px', maxWidth: '540px' }}>
          <input
            id="officer-remarks-input"
            type="text"
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            placeholder={
              lang === 'hi'
                ? 'अधिकारी टीप / सत्यापन टिप्पणी दर्ज करें (वैकल्पिक)...'
                : 'Enter verification remarks, inspection notes or reference numbers...'
            }
            style={{
              width: '100%',
              height: '40px',
              padding: '8px 12px',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              backgroundColor: '#FFFFFF',
              color: 'var(--text-main)',
              outline: 'none',
            }}
          />
        </div>

        {/* Right: Three Decisive Government Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Approve (Green) */}
          <button
            id="btn-officer-approve"
            type="button"
            onClick={() => setActiveModalAction('approve')}
            className="gov-btn gov-btn-success"
            title={lang === 'hi' ? 'संयंत्र स्वीकृत करें' : 'Approve plant verification'}
          >
            <CheckCircle2 size={16} />
            <span>{lang === 'hi' ? 'स्वीकृत करें (Approve)' : 'Approve'}</span>
          </button>

          {/* Return for Correction (Amber) */}
          <button
            id="btn-officer-return"
            type="button"
            onClick={() => setActiveModalAction('return')}
            className="gov-btn gov-btn-amber"
            title={lang === 'hi' ? 'संशोधन हेतु वापस करें' : 'Return for correction'}
          >
            <RotateCcw size={16} />
            <span>{lang === 'hi' ? 'संशोधन हेतु भेजें (Return)' : 'Return for correction'}</span>
          </button>

          {/* Reject (Red) */}
          <button
            id="btn-officer-reject"
            type="button"
            onClick={() => setActiveModalAction('reject')}
            className="gov-btn gov-btn-danger"
            title={lang === 'hi' ? 'आवेदन निरस्त करें' : 'Reject plant application'}
          >
            <XCircle size={16} />
            <span>{lang === 'hi' ? 'अस्वीकृत करें (Reject)' : 'Reject'}</span>
          </button>
        </div>
      </div>

      {/* Confirmation Modal Dialog Before Action Execution */}
      {activeModalAction && (
        <div className="gov-modal-overlay">
          <div className="gov-modal" role="dialog" aria-modal="true">
            <div className="gov-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px', fontWeight: 700 }}>
                <AlertTriangle
                  size={18}
                  color={
                    activeModalAction === 'approve'
                      ? 'var(--status-green)'
                      : activeModalAction === 'return'
                      ? 'var(--status-amber)'
                      : 'var(--status-red)'
                  }
                />
                <span>
                  {activeModalAction === 'approve' && (lang === 'hi' ? 'संयंत्र स्वीकृति की पुष्टि' : 'Confirm Plant Approval')}
                  {activeModalAction === 'return' && (lang === 'hi' ? 'संशोधन हेतु वापसी की पुष्टि' : 'Confirm Return for Correction')}
                  {activeModalAction === 'reject' && (lang === 'hi' ? 'आवेदन निरस्त करने की पुष्टि' : 'Confirm Plant Rejection')}
                </span>
              </div>
              <button
                onClick={() => setActiveModalAction(null)}
                className="gov-btn gov-btn-secondary"
                style={{ height: '30px', minHeight: '30px', padding: '2px 8px' }}
              >
                ✕
              </button>
            </div>

            <div className="gov-modal-body">
              <p style={{ fontSize: '14px', color: 'var(--text-main)', marginBottom: '14px' }}>
                {activeModalAction === 'approve' &&
                  (lang === 'hi'
                    ? `क्या आप संयंत्र ID ${plantId} के तकनीकी परीक्षण, नेट मीटर तथा कार्य पूर्णता प्रतिवेदन (WCR) को विधिवत अनुमोदित करना चाहते हैं?`
                    : `Are you sure you want to approve plant ${plantId}? This seals the technical inspection, net meter calibration, and certifies grid synchronisation.`)}

                {activeModalAction === 'return' &&
                  (lang === 'hi'
                    ? `क्या आप संयंत्र ID ${plantId} को सुधार एवं दस्तावेजी पूर्ति हेतु उपभोक्ता/संस्थापक को वापस लौटाना चाहते हैं?`
                    : `Are you sure you want to return plant ${plantId} for correction? The installer and consumer will be notified to rectify indicated deficiencies.`)}

                {activeModalAction === 'reject' &&
                  (lang === 'hi'
                    ? `सावधानी: संयंत्र ID ${plantId} को औपचारिक रूप से निरस्त किया जा रहा है। यह क्रिया अपरिवर्तनीय होगी।`
                    : `Warning: You are about to officially reject plant ${plantId}. This action terminates current approval workflow.`)}
              </p>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                  {lang === 'hi' ? 'आधिकारिक आदेश / टीप:' : 'Official Officer Remarks & Order Reference:'}
                </label>
                <textarea
                  rows={3}
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder={
                    activeModalAction === 'approve'
                      ? 'Approved in accordance with MPERC Net Metering Regulations 2026.'
                      : 'Specify reasons for return or rejection...'
                  }
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '13px',
                    color: 'var(--text-main)',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </div>

            <div className="gov-modal-footer">
              <button
                type="button"
                onClick={() => setActiveModalAction(null)}
                className="gov-btn gov-btn-secondary"
              >
                {lang === 'hi' ? 'रद्द करें (Cancel)' : 'Cancel'}
              </button>

              <button
                type="button"
                onClick={handleConfirmAction}
                className={`gov-btn ${
                  activeModalAction === 'approve'
                    ? 'gov-btn-success'
                    : activeModalAction === 'return'
                    ? 'gov-btn-amber'
                    : 'gov-btn-danger'
                }`}
              >
                {activeModalAction === 'approve' && (lang === 'hi' ? 'हाँ, स्वीकृत करें' : 'Confirm Approval')}
                {activeModalAction === 'return' && (lang === 'hi' ? 'हाँ, वापस भेजें' : 'Confirm Return')}
                {activeModalAction === 'reject' && (lang === 'hi' ? 'हाँ, निरस्त करें' : 'Confirm Rejection')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
