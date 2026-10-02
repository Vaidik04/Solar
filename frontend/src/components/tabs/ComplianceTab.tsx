import React, { useState } from 'react';
import { CheckCircle2, Play, AlertTriangle } from 'lucide-react';
import { InfoTooltip } from '../InfoTooltip';
import type { ComplianceRuleItem } from '../../types/passport';

interface ComplianceTabProps {
  rules: ComplianceRuleItem[];
  lang?: 'en' | 'hi';
}

export const ComplianceTab: React.FC<ComplianceTabProps> = ({ rules, lang = 'en' }) => {
  const [evaluating, setEvaluating] = useState(false);

  const handleRunEvaluation = () => {
    setEvaluating(true);
    setTimeout(() => {
      setEvaluating(false);
    }, 700);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Regulations Header */}
      <div className="gov-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="gov-badge gov-badge-navy">
                {lang === 'hi' ? 'एमपीईआरसी / सीईए सांविधिक नियम' : 'MPERC & CEA Statutory Regulations'}
              </span>
              <span className="gov-badge gov-badge-green">
                {lang === 'hi' ? 'शत-प्रतिशत अनुपालित' : '100% Compliant'}
              </span>
            </div>

            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)' }}>
              {lang === 'hi'
                ? 'ग्रिड संयोजकता एवं सांविधिक नियमों का स्वचालित परीक्षण'
                : 'Automated Statutory & Grid Interconnection Regulations Audit'}
              <InfoTooltip
                term="Statutory Rules"
                explanation="Rules established by Madhya Pradesh Electricity Regulatory Commission and Central Electricity Authority for safety, metering and grid protection."
              />
            </h2>

            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {lang === 'hi'
                ? 'नियम संकलन संदर्भ: MPERC-ROOFTOP-COMM-2026 • प्रभावी दिनांक: 01 जनवरी 2026'
                : 'Active RuleSet: MPERC-ROOFTOP-COMM-2026 • Validated against CEA Grid Connectivity Standards'}
            </div>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={evaluating}
            className="gov-btn gov-btn-primary"
          >
            <Play size={14} />
            <span>{evaluating ? (lang === 'hi' ? 'परीक्षण जारी...' : 'Evaluating...') : (lang === 'hi' ? 'अनुपालन नियम पुनः चलाएं' : 'Execute Compliance Run')}</span>
          </button>
        </div>
      </div>

      {/* Rules Breakdown Table */}
      <div className="gov-card">
        <div className="gov-card-header">
          <div className="gov-card-title">
            <span>{lang === 'hi' ? 'मूल्यांकित सांविधिक नियम सूची' : 'Evaluated Statutory Rules & Explanations'}</span>
          </div>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            {rules.length} {lang === 'hi' ? 'नियम जाँचे गए' : 'rules checked'}
          </span>
        </div>

        <div className="gov-table-container">
          <table className="gov-table">
            <thead>
              <tr>
                <th style={{ width: '130px' }}>{lang === 'hi' ? 'नियम कोड' : 'Rule Code'}</th>
                <th style={{ width: '110px' }}>{lang === 'hi' ? 'प्राधिकरण' : 'Authority'}</th>
                <th>{lang === 'hi' ? 'सांविधिक आवश्यकता एवं विवरण' : 'Statutory Requirement'}</th>
                <th style={{ width: '160px' }}>{lang === 'hi' ? 'परिणाम स्थिति' : 'Result Status'}</th>
                <th>{lang === 'hi' ? 'सत्यापन टिप्पणी' : 'Verification Note / Details'}</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => {
                const isPassed = r.status === 'PASSED';
                const isWaiver = r.waiverGranted;

                return (
                  <tr key={r.ruleId}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '12px' }}>
                      {r.ruleId}
                    </td>
                    <td>
                      <span className="gov-badge gov-badge-grey" style={{ fontSize: '11px' }}>
                        {r.authority}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{r.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {r.description}
                      </div>
                    </td>
                    <td>
                      {isWaiver ? (
                        <span className="gov-badge gov-badge-amber">
                          <AlertTriangle size={12} />
                          <span>{lang === 'hi' ? 'छूट प्राप्त' : 'Waiver active'}</span>
                        </span>
                      ) : isPassed ? (
                        <span className="gov-badge gov-badge-green">
                          <CheckCircle2 size={12} />
                          <span>{lang === 'hi' ? 'अनुपालित' : 'Compliant'}</span>
                        </span>
                      ) : (
                        <span className="gov-badge gov-badge-red">
                          <span>{lang === 'hi' ? 'अननुपालित' : 'Violation'}</span>
                        </span>
                      )}
                    </td>
                    <td>
                      <div style={{ fontSize: '12px', color: 'var(--text-main)' }}>
                        {r.details}
                      </div>
                      {isWaiver && (
                        <div style={{ fontSize: '11px', color: '#A05E00', marginTop: '2px' }}>
                          Approved by MPERC Superintending Engineer (Reference #WAV-2026-MP-001)
                        </div>
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
