import React from 'react';
import { InfoTooltip } from '../InfoTooltip';
import type { ServiceTicketItem } from '../../types/passport';

interface WarrantyOamTabProps {
  tickets: ServiceTicketItem[];
  lang?: 'en' | 'hi';
}

export const WarrantyOamTab: React.FC<WarrantyOamTabProps> = ({ tickets, lang = 'en' }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Warranties Overview Card */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'सक्रिय उपकरण वारंटी एवं गारंटी विवरण' : 'Active Asset Warranties & OEM Guarantees'}</span>
          </div>
          <span className="gov-badge gov-badge-green">
            {lang === 'hi' ? 'सभी वैध' : 'All warranties valid'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          
          {/* Module 25-Year Warranty */}
          <div style={{ padding: '14px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFFFF' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="gov-badge gov-badge-navy">
                {lang === 'hi' ? '25-वर्षीय कार्यक्षमता' : '25-Year Performance'}
              </span>
              <span className="gov-badge gov-badge-green">
                2026 – 2051
              </span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>
              Tata Power Solar 545W Mono PERC
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Provider: Tata Power Solar Systems Ltd.
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px' }}>
              Terms: Max 0.55% annual degradation; &ge; 84.8% output at year 25.
            </div>
          </div>

          {/* Inverter 5-Year Replacement Warranty */}
          <div style={{ padding: '14px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFFFF' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="gov-badge gov-badge-navy">
                {lang === 'hi' ? '5-वर्षीय विनिर्माण वारंटी' : '5-Year Product'}
              </span>
              <span className="gov-badge gov-badge-green">
                2026 – 2031
              </span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>
              Sungrow SG110CX Inverters (x5)
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Provider: Sungrow Power India Pvt Ltd.
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px' }}>
              Terms: Advance component replacement; on-site repair SLA 48 hrs.
            </div>
          </div>

          {/* System Workmanship 5-Year Guarantee */}
          <div style={{ padding: '14px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFFFF' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="gov-badge gov-badge-navy">
                {lang === 'hi' ? '5-वर्षीय ईपीसी संधारण' : '5-Year EPC Workmanship'}
              </span>
              <span className="gov-badge gov-badge-green">
                2026 – 2031
              </span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>
              Structure &amp; Electrical Balance of Plant
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Installer: Tata Power Solar Systems Ltd.
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px' }}>
              Covers roof waterproofing, DC cabling, civil ballasts, and earthing pits.
            </div>
          </div>

        </div>
      </div>

      {/* Service Tickets & Maintenance Log */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'संचालन एवं संधारण सेवा टिकट' : 'Operations & Maintenance Service Tickets'}</span>
            <InfoTooltip
              term="O&M Tickets"
              explanation="Recorded maintenance events, service visits, and component faults with SLA clock tracking."
            />
          </div>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            {tickets.length} {lang === 'hi' ? 'रिकॉर्ड उपलब्ध' : 'tickets logged'}
          </span>
        </div>

        <div className="gov-table-container">
          <table className="gov-table">
            <thead>
              <tr>
                <th style={{ width: '130px' }}>{lang === 'hi' ? 'टिकट क्रमांक' : 'Ticket ID'}</th>
                <th>{lang === 'hi' ? 'शिकायत / रखरखाव विषय' : 'Issue Description'}</th>
                <th style={{ width: '110px' }}>{lang === 'hi' ? 'प्राथमिकता' : 'Priority'}</th>
                <th style={{ width: '130px' }}>{lang === 'hi' ? 'स्थिति' : 'Status'}</th>
                <th style={{ width: '160px' }}>{lang === 'hi' ? 'एसएलए अनुपालन' : 'SLA Compliance'}</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    {t.id}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{t.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Asset: {t.assetTag || 'Inverter Array'} • Logged: {t.createdAt}
                    </div>
                  </td>
                  <td>
                    {t.priority === 'CRITICAL' ? (
                      <span className="gov-badge gov-badge-red">{t.priority}</span>
                    ) : t.priority === 'HIGH' ? (
                      <span className="gov-badge gov-badge-amber">{t.priority}</span>
                    ) : (
                      <span className="gov-badge gov-badge-grey">{t.priority}</span>
                    )}
                  </td>
                  <td>
                    {t.status === 'RESOLVED' || t.status === 'CLOSED' ? (
                      <span className="gov-badge gov-badge-green">{t.status}</span>
                    ) : (
                      <span className="gov-badge gov-badge-amber">{t.status}</span>
                    )}
                  </td>
                  <td>
                    <div style={{ fontSize: '12px', color: 'var(--text-main)', fontWeight: 600 }}>
                      SLA Met (1.2 hrs)
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      Deadline: 4.0 hrs
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
