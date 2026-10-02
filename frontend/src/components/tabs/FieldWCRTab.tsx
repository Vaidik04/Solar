import React from 'react';
import { Download, CheckCircle2 } from 'lucide-react';
import { InfoTooltip } from '../InfoTooltip';
import type { InspectionCheckItem } from '../../types/passport';

interface FieldWCRTabProps {
  checks: InspectionCheckItem[];
  lang?: 'en' | 'hi';
}

export const FieldWCRTab: React.FC<FieldWCRTabProps> = ({ checks, lang = 'en' }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Certified Work Completion Report (WCR) Government Summary Card */}
      <div className="gov-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="gov-badge gov-badge-navy">
                {lang === 'hi' ? 'कार्य पूर्णता प्रतिवेदन (WCR)' : 'Work Completion Report'}
              </span>
              <span className="gov-badge gov-badge-green">
                {lang === 'hi' ? 'अनुमोदित एवं सीलबंद' : 'Approved and synchronized'}
              </span>
            </div>

            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)' }}>
              WCR-MP-BPL-0042-V1 — {lang === 'hi' ? 'ग्रिड संयोजकता एवं कार्य पूर्णता प्रमाण पत्र' : 'Grid Interconnection & Work Completion Certificate'}
              <InfoTooltip
                term="WCR"
                explanation="Work Completion Report submitted by accredited solar EPC engineer and validated by MPEB Assistant Engineer prior to commissioning."
              />
            </h2>

            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {lang === 'hi' ? 'प्रमाणित क्षमता' : 'Capacity certified'}: <strong>125.40 kWp DC / 100.0 kW AC</strong> • {lang === 'hi' ? 'पूर्णता दिनांक' : 'Completion date'}: <strong>15 February 2026</strong>
            </div>
          </div>

          <button
            onClick={() => alert('Downloading official WCR certificate: WCR-MP-BPL-0042-V1.pdf')}
            className="gov-btn gov-btn-secondary"
          >
            <Download size={15} />
            <span>{lang === 'hi' ? 'प्रमाणित WCR डाउनलोड करें (PDF)' : 'Download Certified WCR (PDF)'}</span>
          </button>
        </div>

        {/* SHA-256 seal strip */}
        <div
          style={{
            marginTop: '16px',
            padding: '10px 14px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>WCR Document SHA-256 Digest: </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</span>
          </div>
          <span className="gov-badge gov-badge-green" style={{ fontSize: '11px' }}>
            MPEB SEALED &amp; FILED
          </span>
        </div>
      </div>

      {/* 2 Columns: Inspection Quality Checklist & Grid Metering Parameters */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        
        {/* Inspection Checklist Table */}
        <div className="gov-card" style={{ marginBottom: 0 }}>
          <div className="gov-card-header">
            <div className="gov-card-title">
              <span>{lang === 'hi' ? 'स्थल गुणवत्ता निरीक्षण सूची' : 'Pre-Commissioning Quality Checklist'}</span>
            </div>
            <span className="gov-badge gov-badge-green">
              {lang === 'hi' ? '5 में से 5 स्वीकृत' : '5 of 5 passed'}
            </span>
          </div>

          <table className="gov-table" style={{ fontSize: '13px' }}>
            <thead>
              <tr>
                <th>{lang === 'hi' ? 'जाँच बिंदु (Inspection Parameter)' : 'Check Point'}</th>
                <th>{lang === 'hi' ? 'सत्यापित मान' : 'Reading / Value'}</th>
                <th>{lang === 'hi' ? 'स्थिति' : 'Status'}</th>
              </tr>
            </thead>
            <tbody>
              {checks.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{c.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {c.code}
                    </div>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {c.value || 'Verified'}
                  </td>
                  <td>
                    {c.status === 'PASS' ? (
                      <span className="gov-badge gov-badge-green">
                        <CheckCircle2 size={12} />
                        <span>{lang === 'hi' ? 'सफल' : 'Pass'}</span>
                      </span>
                    ) : (
                      <span className="gov-badge gov-badge-amber">
                        <span>{lang === 'hi' ? 'लंबित' : 'Pending'}</span>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Grid Synchronization & Metering Details */}
        <div className="gov-card" style={{ marginBottom: 0 }}>
          <div className="gov-card-header">
            <div className="gov-card-title">
              <span>{lang === 'hi' ? 'नेट मीटरिंग एवं ग्रिड परीक्षण विवरण' : 'Net Metering & Grid Protection Calibration'}</span>
            </div>
            <span className="gov-badge gov-badge-navy">
              {lang === 'hi' ? 'कैलिब्रेटेड' : 'Calibrated'}
            </span>
          </div>

          <table className="gov-spec-table">
            <tbody>
              <tr>
                <td className="label">{lang === 'hi' ? 'मीटर मेक एवं मॉडल' : 'Meter make & model'}</td>
                <td className="value">Secure Meters Premier 300 (Bi-directional)</td>
              </tr>
              <tr>
                <td className="label">{lang === 'hi' ? 'सीरियल नंबर (Serial No.)' : 'Meter serial number'}</td>
                <td className="value" style={{ fontFamily: 'var(--font-mono)' }}>SEC-2026-99981</td>
              </tr>
              <tr>
                <td className="label">{lang === 'hi' ? 'सीटी / पीटी अनुपात' : 'CT / PT ratio'}</td>
                <td className="value">200/5 A (Class 0.2S Accuracy)</td>
              </tr>
              <tr>
                <td className="label">{lang === 'hi' ? 'प्रारंभिक निर्यात रीडिंग' : 'Initial export reading'}</td>
                <td className="value" style={{ fontFamily: 'var(--font-mono)' }}>000000.00 kWh</td>
              </tr>
              <tr>
                <td className="label">{lang === 'hi' ? 'एंटी-आइसलैंडिंग परीक्षण' : 'Anti-islanding protection'}</td>
                <td className="value">
                  <span className="gov-badge gov-badge-green">
                    Trip time: 42 ms (Limit &le; 200 ms)
                  </span>
                </td>
              </tr>
              <tr>
                <td className="label">{lang === 'hi' ? 'अर्थिंग प्रतिरोध (Earth Resistance)' : 'Combined earth resistance'}</td>
                <td className="value">2.4 Ohms (Required &le; 5.0 Ohms)</td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
};
