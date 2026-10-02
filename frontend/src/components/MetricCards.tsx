import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';
import type { PlantPassport } from '../types/passport';

interface MetricCardsProps {
  passport: PlantPassport;
  lang?: 'en' | 'hi';
}

export const MetricCards: React.FC<MetricCardsProps> = ({ passport, lang = 'en' }) => {
  const [showMoreDetails, setShowMoreDetails] = useState(false);

  return (
    <div style={{ marginBottom: '20px' }}>
      {/* 4 Flat Summary Cards (No Icons, High Contrast Government Style) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '16px',
        }}
      >
        {/* Card 1: Installed Capacity */}
        <div className="gov-card" style={{ padding: '16px 20px', marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
              {lang === 'hi' ? 'स्थापित क्षमता' : 'Installed capacity'}
            </span>
            <InfoTooltip
              term={lang === 'hi' ? 'डीसी/एसी क्षमता' : 'DC / AC Capacity'}
              explanation={
                lang === 'hi'
                  ? 'सौर मॉड्यूल (डीसी) तथा इन्वर्टर (एसी) की कुल स्वीकृत एवं स्थापित क्षमता।'
                  : 'Total DC peak module wattage vs rated AC inverter export capacity.'
              }
            />
          </div>
          <div style={{ marginTop: '8px', fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
            125.4 kWp <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)' }}>DC / 100 kW AC</span>
          </div>
          <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            {lang === 'hi' ? 'स्वीकृत लोड: 100 kW • 12 स्ट्रिंग्स' : 'Sanctioned load: 100 kW • 12 strings'}
          </div>
        </div>

        {/* Card 2: Today's Generation */}
        <div className="gov-card" style={{ padding: '16px 20px', marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
              {lang === 'hi' ? 'आज का विद्युत उत्पादन' : "Today's generation"}
            </span>
            <span className="gov-badge gov-badge-green">
              {lang === 'hi' ? 'सामान्य' : 'Normal'}
            </span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
            524.8 kWh
          </div>
          <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            {lang === 'hi' ? 'विशिष्ट उत्पादन: 4.18 kWh/kWp' : 'Specific yield: 4.18 kWh/kWp'}
          </div>
        </div>

        {/* Card 3: Total Generation Since Commissioning */}
        <div className="gov-card" style={{ padding: '16px 20px', marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
              {lang === 'hi' ? 'प्रारंभ से कुल उत्पादन' : 'Total generation'}
            </span>
            <InfoTooltip
              term={lang === 'hi' ? 'कुल संचयी उत्पादन' : 'Cumulative Generation'}
              explanation={
                lang === 'hi'
                  ? 'ग्रिड समकालन दिनांक (फरवरी 2026) से कुल सत्यापित निर्यात यूनिट।'
                  : 'Total cumulative units recorded by DISCOM bidirectional net meter.'
              }
            />
          </div>
          <div style={{ marginTop: '8px', fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
            148.6 MWh
          </div>
          <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            {lang === 'hi' ? 'ग्रिड समकालन: फरवरी 2026 से' : 'Since commissioning (Feb 2026)'}
          </div>
        </div>

        {/* Card 4: Compliance Status */}
        <div className="gov-card" style={{ padding: '16px 20px', marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>
              {lang === 'hi' ? 'विनियमन अनुपालन स्थिति' : 'Compliance status'}
            </span>
            <span className="gov-badge gov-badge-green">
              {lang === 'hi' ? 'पूर्णतः अनुपालित' : 'Compliant'}
            </span>
          </div>
          <div style={{ marginTop: '8px', fontSize: '16px', fontWeight: 700, color: 'var(--status-green)' }}>
            {lang === 'hi' ? 'अनुपालित (0 उल्लंघन, 1 छूट)' : 'Compliant, 0 violations, 1 waiver'}
          </div>
          <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            {lang === 'hi' ? 'एमपीईआरसी / एमएनआरई एएलएमएम मान्य' : 'MPERC net-metering & MNRE ALMM verified'}
          </div>
        </div>
      </div>

      {/* Collapsible Secondary Performance Details Accordion */}
      <div style={{ marginTop: '12px' }}>
        <button
          onClick={() => setShowMoreDetails(!showMoreDetails)}
          className="gov-btn gov-btn-secondary"
          style={{
            height: '36px',
            minHeight: '36px',
            padding: '6px 14px',
            fontSize: '13px',
            color: 'var(--primary-navy)',
            backgroundColor: '#FFFFFF',
          }}
          aria-expanded={showMoreDetails}
        >
          {showMoreDetails ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          <span>
            {showMoreDetails
              ? (lang === 'hi' ? 'अतिरिक्त तकनीकी विवरण छिपाएं' : 'Hide performance details')
              : (lang === 'hi' ? 'अतिरिक्त तकनीकी एवं कार्यक्षमता विवरण देखें' : 'More performance details (PR, CO2, DC/AC ratio)')}
          </span>
        </button>

        {showMoreDetails && (
          <div
            className="gov-card"
            style={{
              marginTop: '10px',
              padding: '16px',
              backgroundColor: '#FFFFFF',
            }}
          >
            <table className="gov-table" style={{ fontSize: '13px' }}>
              <thead>
                <tr>
                  <th>{lang === 'hi' ? 'पैरामीटर' : 'Performance Parameter'}</th>
                  <th>{lang === 'hi' ? 'सत्यापित मान' : 'Recorded Value'}</th>
                  <th>{lang === 'hi' ? 'मानक संदर्भ' : 'Benchmark / Specification'}</th>
                  <th>{lang === 'hi' ? 'स्थिति' : 'Operational Status'}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>
                    Performance Ratio (PR)
                    <InfoTooltip
                      term="Performance Ratio (PR)"
                      explanation="Actual energy delivered divided by theoretical energy calculated from solar insolation."
                    />
                  </td>
                  <td>81.4%</td>
                  <td>&ge; 75.0% (IEC 61724 Standard)</td>
                  <td><span className="gov-badge gov-badge-green">{lang === 'hi' ? 'उत्कृष्ट' : 'Normal'}</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>
                    DC to AC Overloading Ratio
                    <InfoTooltip
                      term="DC/AC Ratio"
                      explanation="Ratio of peak PV array rating to inverter continuous rated AC export capacity."
                    />
                  </td>
                  <td>1.25 : 1.0</td>
                  <td>1.20 - 1.35 (Optimal design window)</td>
                  <td><span className="gov-badge gov-badge-green">{lang === 'hi' ? 'स्वीकृत' : 'Approved'}</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>
                    Capacity Utilization Factor (CUF)
                    <InfoTooltip
                      term="CUF"
                      explanation="Ratio of actual output over a year to maximum possible output at continuous 24-hr nameplate rating."
                    />
                  </td>
                  <td>19.8%</td>
                  <td>18.0% - 21.0% (Madhya Pradesh Central Zone)</td>
                  <td><span className="gov-badge gov-badge-green">{lang === 'hi' ? 'सामान्य' : 'Normal'}</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>
                    Deemed Waiver
                    <InfoTooltip
                      term="Deemed Waiver"
                      explanation="Formal regulatory waiver granted by MPERC for non-standard cable conduit layout on historical roof."
                    />
                  </td>
                  <td>WAV-2026-MP-001</td>
                  <td>Conditionally approved with fire-barrier cladding</td>
                  <td><span className="gov-badge gov-badge-amber">{lang === 'hi' ? 'सशर्त स्वीकृत' : 'Waiver active'}</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>
                    CO2 Emissions Avoided
                  </td>
                  <td>121.8 Metric Tonnes</td>
                  <td>Offset against central grid thermal factor (0.82 kg/kWh)</td>
                  <td><span className="gov-badge gov-badge-navy">{lang === 'hi' ? 'पर्यावरणीय लाभ' : 'Verified'}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
