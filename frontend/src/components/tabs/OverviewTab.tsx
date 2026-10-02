import React from 'react';
import { InfoTooltip } from '../InfoTooltip';
import type { PlantPassport } from '../../types/passport';

interface OverviewTabProps {
  passport: PlantPassport;
  onOpenQr?: () => void;
  lang?: 'en' | 'hi';
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  passport,
  lang = 'en',
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Official Government Verification Summary Card */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'संयंत्र पहचान एवं उपभोक्ता विवरण' : 'Plant Identification & Consumer Profile'}</span>
          </div>
          <span className="gov-badge gov-badge-green">
            {lang === 'hi' ? 'सत्यापित एवं सक्रिय (In Operation)' : 'Verified and in operation'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          
          {/* Column 1: Consumer & Sanction Details */}
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '10px' }}>
              {lang === 'hi' ? 'उपभोक्ता एवं कनेक्शन विवरण' : 'Consumer & DISCOM Connection Information'}
            </h4>
            <table className="gov-spec-table">
              <tbody>
                <tr>
                  <td className="label">{lang === 'hi' ? 'उपभोक्ता क्रमांक (Consumer Number)' : 'Consumer number'}</td>
                  <td className="value" style={{ fontFamily: 'var(--font-mono)' }}>012345678901</td>
                </tr>
                <tr>
                  <td className="label">{lang === 'hi' ? 'उपभोक्ता का नाम' : 'Consumer name'}</td>
                  <td className="value">Tata Motors Limited (Pimpri Pune / Bhopal Plant)</td>
                </tr>
                <tr>
                  <td className="label">{lang === 'hi' ? 'संयंत्र स्थल का पता' : 'Site address'}</td>
                  <td className="value">Plot B-24, Mandideep Industrial Area, Bhopal, MP - 462046</td>
                </tr>
                <tr>
                  <td className="label">{lang === 'hi' ? 'विद्युत वितरण वृत्त / संभाग' : 'Circle / Division'}</td>
                  <td className="value">Bhopal Central Circle • City Division West</td>
                </tr>
                <tr>
                  <td className="label">{lang === 'hi' ? 'संयोजन श्रेणी (Connection Category)' : 'Tariff category'}</td>
                  <td className="value">HT Industrial (33 kV Grid Connection)</td>
                </tr>
                <tr>
                  <td className="label">{lang === 'hi' ? 'स्वीकृति क्रमांक' : 'Sanction reference'}</td>
                  <td className="value" style={{ fontFamily: 'var(--font-mono)' }}>MPEB/BPL/SOLAR/2026/0892</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Column 2: Plant Technical Specs */}
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary-navy)', marginBottom: '10px' }}>
              {lang === 'hi' ? 'संयंत्र तकनीकी विनिर्देश' : 'Solar Plant Technical Specifications'}
            </h4>
            <table className="gov-spec-table">
              <tbody>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'स्थापित डीसी क्षमता (DC Capacity)' : 'DC capacity'}
                    <InfoTooltip term="DC Capacity" explanation="Total peak DC capacity of solar PV array measured under standard test conditions." />
                  </td>
                  <td className="value">125.4 kWp</td>
                </tr>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'अनुमोदित एसी क्षमता (AC Capacity)' : 'AC inverter capacity'}
                    <InfoTooltip term="AC Capacity" explanation="Maximum continuous alternating current output permissible into MPEB grid." />
                  </td>
                  <td className="value">100 kW</td>
                </tr>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'नेट मीटर क्रमांक (Net Meter No.)' : 'Net meter serial'}
                    <InfoTooltip term="Net Meter" explanation="Bidirectional DISCOM meter recording import from and export to utility grid." />
                  </td>
                  <td className="value" style={{ fontFamily: 'var(--font-mono)' }}>SEC-2026-99981 (Secure Meters Premier 300)</td>
                </tr>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'मॉड्यूल विन्यास एवं झुकाव' : 'Tilt and azimuth'}
                    <InfoTooltip term="Azimuth" explanation="True south orientation (180°) and module slope for maximum solar harvest." />
                  </td>
                  <td className="value">15° Tilt • 180° True South</td>
                </tr>
                <tr>
                  <td className="label">{lang === 'hi' ? 'माउंटिंग संरचना (Structure)' : 'Mounting structure'}</td>
                  <td className="value">Ballasted Elevated Hot-Dip Galvanised (HDG) Aluminium</td>
                </tr>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'वार्षिक अनुमानित उत्पादन' : 'Expected annual generation'}
                    <InfoTooltip term="Estimated Generation" explanation="Simulated P50 generation yield based on MP solar insolation data." />
                  </td>
                  <td className="value">185,000 kWh</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Grid Synchronisation & Integrity Seal Card */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'ग्रिड समकालन एवं सुरक्षा प्रमाणन' : 'Grid Synchronisation & Audit Seal'}</span>
          </div>
          <span className="gov-badge gov-badge-green">
            {lang === 'hi' ? 'डिजिटल रूप से हस्ताक्षरित' : 'Digitally sealed'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'ग्रिड समकालन दिनांक' : 'Grid synchronisation date'}
            </div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
              16 February 2026
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'सत्यापन अधिकारी' : 'Inspecting officer'}
            </div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
              Er. Rajesh Sharma, EE (O&M)
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'कार्य पूर्णता प्रतिवेदन (WCR)' : 'WCR certificate'}
            </div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
              WCR-MP-BPL-0042-V1 (Approved)
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'विनियमन अनुपालन संदर्भ' : 'Regulatory reference'}
            </div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
              MPERC Net Metering Regs 2026
            </div>
          </div>
        </div>

        {/* Cryptographic SHA-256 Record Hash */}
        <div
          style={{
            marginTop: '16px',
            padding: '10px 14px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <div>
            <strong style={{ color: 'var(--text-main)' }}>Digital Verification Hash (SHA-256): </strong>
            <span style={{ fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
              {passport.blockchainRecord?.hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
            </span>
          </div>
          <span className="gov-badge gov-badge-navy">
            {lang === 'hi' ? 'अपरिवर्तनीय लेजर' : 'Immutable block'}
          </span>
        </div>
      </div>

    </div>
  );
};
