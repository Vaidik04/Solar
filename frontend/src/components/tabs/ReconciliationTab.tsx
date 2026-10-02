import React, { useState } from 'react';
import { RefreshCw, CheckCircle2 } from 'lucide-react';
import { InfoTooltip } from '../InfoTooltip';
import type { ReconciliationItem } from '../../types/passport';

interface ReconciliationTabProps {
  items: ReconciliationItem[];
  lang?: 'en' | 'hi';
}

export const ReconciliationTab: React.FC<ReconciliationTabProps> = ({ items, lang = 'en' }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [lastRunTime, setLastRunTime] = useState('2 minutes ago');

  const handleRunRecon = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setLastRunTime('Just now');
    }, 800);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Verification Header Card */}
      <div className="gov-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="gov-badge gov-badge-navy">
                {lang === 'hi' ? '3-मार्गीय सामग्री मिलान' : '3-Way Reconciliation'}
              </span>
              <span className="gov-badge gov-badge-green">
                {lang === 'hi' ? 'शून्य विचलन (0 Discrepancy)' : 'Zero Discrepancies'}
              </span>
            </div>

            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)' }}>
              {lang === 'hi'
                ? 'प्रारूप सामग्री बनाम आपूर्ति चालान बनाम स्थल पर स्थापित उपकरण मिलान'
                : 'Approved BOM vs. Warehouse Supply vs. Site Installed Assets'}
              <InfoTooltip
                term="3-Way Reconciliation"
                explanation="Cross-verification ensuring physical equipment installed on site matches both approved engineering design and purchase invoices."
              />
            </h2>

            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {lang === 'hi' ? 'अंतिम मिलान सत्यापन' : 'Last verified'}: <strong>{lastRunTime}</strong> • {lang === 'hi' ? 'ऑडिट रन संदर्भ' : 'Run reference'}: <span style={{ fontFamily: 'var(--font-mono)' }}>RECON-MP-2026-00491</span>
            </div>
          </div>

          <button
            onClick={handleRunRecon}
            disabled={isRunning}
            className="gov-btn gov-btn-primary"
          >
            <RefreshCw size={15} className={isRunning ? 'animate-spin' : ''} />
            <span>{isRunning ? (lang === 'hi' ? 'सत्यापित हो रहा है...' : 'Reconciling...') : (lang === 'hi' ? 'पुनः मिलान चलाएं' : 'Run 3-Way Reconciliation')}</span>
          </button>
        </div>

        {/* Snapshot Hashes in clean table */}
        <div style={{ marginTop: '16px', borderTop: '1px solid var(--border-light)', paddingTop: '12px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            <strong>{lang === 'hi' ? 'डिजिटल स्नैपशॉट अखंडता प्रमाण' : 'Cryptographic Verification Snapshots'}:</strong>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', fontSize: '12px' }}>
            <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Approved BOM SHA-256: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>a8f9c2...410b</span>
            </div>
            <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Allocated Serials SHA-256: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>3b8d11...99ef</span>
            </div>
            <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Site Scanned Assets SHA-256: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>3b8d11...99ef</span>
            </div>
          </div>
        </div>
      </div>

      {/* Reconciliation Line Items Table */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'घटक-वार मिलान रिपोर्ट' : 'Component-Level Reconciliation Report'}</span>
          </div>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            {items.length} {lang === 'hi' ? 'श्रेणियां सत्यापित' : 'categories checked'}
          </span>
        </div>

        <div className="gov-table-container">
          <table className="gov-table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>{lang === 'hi' ? 'क्र.सं.' : 'S.No'}</th>
                <th>{lang === 'hi' ? 'घटक विवरण (Component)' : 'Component'}</th>
                <th style={{ textAlign: 'right' }}>{lang === 'hi' ? 'प्रारूप मात्रा (Planned)' : 'Planned Qty'}</th>
                <th style={{ textAlign: 'right' }}>{lang === 'hi' ? 'आपूर्ति मात्रा (Allocated)' : 'Allocated Qty'}</th>
                <th style={{ textAlign: 'right' }}>{lang === 'hi' ? 'स्थल सत्यापित (Site Installed)' : 'Site Verified'}</th>
                <th style={{ textAlign: 'right' }}>{lang === 'hi' ? 'विचलन (Variance)' : 'Variance'}</th>
                <th>{lang === 'hi' ? 'सत्यापन स्थिति (Status)' : 'Status'}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => {
                const variance = item.installedCount - item.plannedCount;
                const isMatch = item.status === 'MATCH';

                return (
                  <tr key={item.id}>
                    <td style={{ color: 'var(--text-secondary)' }}>{idx + 1}</td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{item.componentName}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {item.serialsMatched ? `${item.installedCount} serial numbers logged` : 'Bulk component'}
                      </div>
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {item.plannedCount}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {item.allocatedCount}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--primary-navy)' }}>
                      {item.installedCount}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {variance === 0 ? '0' : variance > 0 ? `+${variance}` : `${variance}`}
                    </td>
                    <td>
                      {isMatch ? (
                        <span className="gov-badge gov-badge-green">
                          <CheckCircle2 size={12} />
                          <span>{lang === 'hi' ? 'शत-प्रतिशत मिलान (100% Match)' : 'Match'}</span>
                        </span>
                      ) : (
                        <span className="gov-badge gov-badge-amber">
                          <span>{lang === 'hi' ? 'विचलन समीक्षार्थ' : 'Discrepancy'}</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
