import React, { useState } from 'react';
import { Copy, Check, Printer, ShieldCheck } from 'lucide-react';
import type { PlantPassport } from '../types/passport';

interface PassportQrModalProps {
  passport: PlantPassport;
  onClose: () => void;
  lang?: 'en' | 'hi';
}

export const PassportQrModal: React.FC<PassportQrModalProps> = ({
  passport,
  onClose,
  lang = 'en',
}) => {
  const [copied, setCopied] = useState(false);

  const verificationUrl = `https://mpeb.mp.gov.in/solar/verify/${passport.plantId}?token=${passport.qrVerificationToken}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(verificationUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="gov-modal-overlay" onClick={onClose}>
      <div
        className="gov-modal"
        style={{ maxWidth: '480px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="gov-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} color="var(--primary-navy)" />
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
              {lang === 'hi' ? 'डिजिटल संयंत्र सत्यापन क्यूआर (QR)' : 'Digital Plant Passport Verification QR'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="gov-btn gov-btn-secondary"
            style={{ minHeight: '32px', height: '32px', padding: '2px 8px' }}
          >
            ✕
          </button>
        </div>

        <div className="gov-modal-body" style={{ textAlign: 'center' }}>
          {/* MPEB Official Verification Heading */}
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Madhya Pradesh Electricity Board • Net Metering Certificate
          </div>
          <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px' }}>
            {passport.projectName}
          </div>

          {/* QR Code Container */}
          <div
            style={{
              padding: '16px',
              backgroundColor: '#FFFFFF',
              border: '2px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              display: 'inline-block',
              margin: '0 auto 16px auto',
            }}
          >
            {/* SVG Crisp High-Resolution QR Representation */}
            <svg width="180" height="180" viewBox="0 0 180 180" fill="#000000">
              <rect width="180" height="180" fill="#FFFFFF" />
              {/* Corner 1 */}
              <rect x="10" y="10" width="40" height="40" fill="#1F3A93" />
              <rect x="16" y="16" width="28" height="28" fill="#FFFFFF" />
              <rect x="22" y="22" width="16" height="16" fill="#1F3A93" />
              {/* Corner 2 */}
              <rect x="130" y="10" width="40" height="40" fill="#1F3A93" />
              <rect x="136" y="16" width="28" height="28" fill="#FFFFFF" />
              <rect x="142" y="22" width="16" height="16" fill="#1F3A93" />
              {/* Corner 3 */}
              <rect x="10" y="130" width="40" height="40" fill="#1F3A93" />
              <rect x="16" y="136" width="28" height="28" fill="#FFFFFF" />
              <rect x="22" y="142" width="16" height="16" fill="#1F3A93" />
              {/* Sample Pattern Grid */}
              <rect x="60" y="20" width="10" height="10" />
              <rect x="80" y="20" width="10" height="10" />
              <rect x="100" y="20" width="10" height="10" />
              <rect x="60" y="40" width="20" height="10" />
              <rect x="90" y="40" width="10" height="20" />
              <rect x="20" y="60" width="10" height="20" />
              <rect x="40" y="70" width="10" height="10" />
              <rect x="60" y="70" width="20" height="20" />
              <rect x="90" y="70" width="20" height="10" />
              <rect x="120" y="70" width="10" height="30" />
              <rect x="140" y="70" width="20" height="10" />
              <rect x="20" y="100" width="20" height="10" />
              <rect x="50" y="100" width="10" height="10" />
              <rect x="80" y="100" width="20" height="20" />
              <rect x="110" y="110" width="10" height="20" />
              <rect x="140" y="100" width="20" height="20" />
              <rect x="60" y="140" width="10" height="20" />
              <rect x="80" y="130" width="30" height="10" />
              <rect x="90" y="150" width="20" height="10" />
              <rect x="120" y="140" width="20" height="20" />
              <rect x="150" y="140" width="10" height="20" />
            </svg>
          </div>

          {/* Key Plant Credentials */}
          <div style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.6', marginBottom: '14px' }}>
            <div>
              <strong>Plant ID: </strong>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{passport.plantId}</span>
            </div>
            <div>
              <strong>Consumer No: </strong>
              <span style={{ fontFamily: 'var(--font-mono)' }}>012345678901</span> • 125.4 kWp DC
            </div>
            <div style={{ color: 'var(--status-green)', fontWeight: 600 }}>
              Status: Verified &amp; Commissioned
            </div>
          </div>

          {/* Copy Verification Link */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <input
              type="text"
              readOnly
              value={verificationUrl}
              style={{
                flex: 1,
                padding: '8px 10px',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'var(--bg-subtle)',
                color: 'var(--text-secondary)',
              }}
            />
            <button
              onClick={handleCopy}
              className="gov-btn gov-btn-secondary"
              style={{ minHeight: '36px', height: '36px', padding: '4px 12px', fontSize: '12px' }}
            >
              {copied ? <Check size={14} color="var(--status-green)" /> : <Copy size={14} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        </div>

        <div className="gov-modal-footer">
          <button
            type="button"
            onClick={() => window.print()}
            className="gov-btn gov-btn-secondary"
          >
            <Printer size={15} />
            <span>Print QR Card</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="gov-btn gov-btn-primary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
