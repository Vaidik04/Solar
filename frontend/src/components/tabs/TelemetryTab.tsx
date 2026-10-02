import React from 'react';
import { InfoTooltip } from '../InfoTooltip';
import type { GenerationPoint } from '../../types/passport';

interface TelemetryTabProps {
  generationData: GenerationPoint[];
  lang?: 'en' | 'hi';
}

export const TelemetryTab: React.FC<TelemetryTabProps> = ({ generationData, lang = 'en' }) => {
  const maxPower = Math.max(...generationData.map((d) => d.powerKw), 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Real-time Grid & Inverter Status Card */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'वास्तविक समय ग्रिड एवं उत्पादन टेलीमेट्री' : 'Real-Time Grid & Generation Telemetry'}</span>
            <InfoTooltip
              term="AMR Telemetry"
              explanation="Automated Meter Reading telemetry transmitting interval data to MPEB central monitoring cell."
            />
          </div>
          <span className="gov-badge gov-badge-green">
            {lang === 'hi' ? 'ऑनलाइन (सक्रिय)' : 'AMR Meter Online'}
          </span>
        </div>

        {/* 3 Electrical Measurement Parameters */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFFFF' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'ग्रिड आवृत्ति (Frequency)' : 'Grid frequency'}
            </div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              50.02 Hz
            </div>
            <div style={{ fontSize: '11px', color: 'var(--status-green)' }}>
              Nominal band (49.90 - 50.05 Hz)
            </div>
          </div>

          <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFFFF' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'एसी वोल्टेज (3-Phase Voltage)' : '3-Phase AC voltage'}
            </div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              415.4 V
            </div>
            <div style={{ fontSize: '11px', color: 'var(--status-green)' }}>
              Balanced across R-Y-B phases
            </div>
          </div>

          <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', backgroundColor: '#FFFFFF' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {lang === 'hi' ? 'पावर फैक्टर (Power Factor)' : 'Power factor'}
            </div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              0.992
            </div>
            <div style={{ fontSize: '11px', color: 'var(--status-green)' }}>
              Complies with MPERC &gt; 0.95 rule
            </div>
          </div>
        </div>

        {/* Hourly Generation Profile Visualization (Flat Light Bars) */}
        <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)' }}>
              {lang === 'hi' ? 'दैनिक विद्युत उत्पादन वक्र (Daily Generation Curve)' : 'Diurnal Generation Profile (Active Power kW)'}
            </h4>
            <div style={{ display: 'flex', gap: '14px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--primary-navy)', borderRadius: '2px' }} />
                {lang === 'hi' ? 'उत्पादित विद्युत (kW)' : 'Power (kW)'}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--status-amber)', borderRadius: '2px' }} />
                {lang === 'hi' ? 'सौर विकिरण (W/m²)' : 'Irradiance (W/m²)'}
              </span>
            </div>
          </div>

          {/* Bar Chart Container */}
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              height: '180px',
              gap: '8px',
              padding: '12px 10px 0 10px',
              backgroundColor: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
            }}
          >
            {generationData.map((pt, i) => {
              const heightPercent = Math.round((pt.powerKw / maxPower) * 100);
              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    height: '100%',
                    justifyContent: 'flex-end',
                  }}
                  title={`${pt.time}: ${pt.powerKw} kW (${pt.irradiance} W/m²)`}
                >
                  <div
                    style={{
                      width: '100%',
                      maxWidth: '32px',
                      height: `${Math.max(heightPercent, 3)}%`,
                      backgroundColor: 'var(--primary-navy)',
                      borderRadius: '2px 2px 0 0',
                    }}
                  />
                  <div
                    style={{
                      fontSize: '10px',
                      color: 'var(--text-secondary)',
                      marginTop: '6px',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {pt.time.slice(0, 2)}h
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

    </div>
  );
};
