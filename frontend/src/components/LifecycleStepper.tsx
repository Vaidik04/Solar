import React from 'react';
import { Check } from 'lucide-react';
import type { LifecycleStage } from '../types/passport';

interface LifecycleStepperProps {
  currentStage: LifecycleStage;
  onSelectStage?: (stage: LifecycleStage) => void;
  lang?: 'en' | 'hi';
}

interface StageStep {
  key: LifecycleStage | 'bom' | 'supply' | 'grid_sync';
  labelEn: string;
  labelHi: string;
  stepNumber: number;
}

const STEPS: StageStep[] = [
  { key: 'lead', labelEn: 'Application', labelHi: 'आवेदन', stepNumber: 1 },
  { key: 'survey', labelEn: 'Site survey', labelHi: 'स्थल सर्वेक्षण', stepNumber: 2 },
  { key: 'design', labelEn: 'Design approval', labelHi: 'प्रारूप स्वीकृति', stepNumber: 3 },
  { key: 'bom', labelEn: 'Bill of materials', labelHi: 'सामग्री सूची', stepNumber: 4 },
  { key: 'supply', labelEn: 'Material supply', labelHi: 'सामग्री आपूर्ति', stepNumber: 5 },
  { key: 'installation', labelEn: 'Installation', labelHi: 'संयंत्र स्थापना', stepNumber: 6 },
  { key: 'inspection', labelEn: 'Inspection', labelHi: 'गुणवत्ता निरीक्षण', stepNumber: 7 },
  { key: 'wcr', labelEn: 'Work completion report', labelHi: 'कार्य पूर्णता प्रतिवेदन', stepNumber: 8 },
  { key: 'grid_sync', labelEn: 'Grid synchronisation', labelHi: 'ग्रिड समकालन', stepNumber: 9 },
  { key: 'oam', labelEn: 'Operation & maintenance', labelHi: 'संचालन एवं संधारण', stepNumber: 10 },
];

export const LifecycleStepper: React.FC<LifecycleStepperProps> = ({
  currentStage,
  onSelectStage,
  lang = 'en',
}) => {
  // Determine index of current stage
  const getStageIndex = (stage: LifecycleStage): number => {
    switch (stage) {
      case 'lead': return 0;
      case 'survey': return 1;
      case 'design': return 2;
      case 'procurement': return 4;
      case 'installation': return 5;
      case 'inspection': return 6;
      case 'wcr': return 7;
      case 'commissioned': return 8;
      case 'oam': return 9;
      default: return 9;
    }
  };

  const currentIndex = getStageIndex(currentStage);

  return (
    <div
      className="gov-card"
      style={{
        padding: '16px 20px',
        marginBottom: '20px',
        overflowX: 'auto',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)' }}>
          {lang === 'hi' ? 'संयंत्र सत्यापन एवं प्रगति चरण' : 'Plant Verification & Lifecycle Progress'}
        </h3>
        <span className="gov-badge gov-badge-navy">
          {lang === 'hi' ? 'चरण 10 में से 10 पूर्ण' : 'Stage 10 of 10: In Operation'}
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          minWidth: '920px',
          position: 'relative',
          padding: '8px 4px',
        }}
      >
        {STEPS.map((step, idx) => {
          const isCompleted = idx < currentIndex || currentStage === 'oam' || currentStage === 'commissioned';
          const isCurrent = idx === currentIndex && currentStage !== 'oam';

          return (
            <React.Fragment key={step.key}>
              {/* Connector line between steps */}
              {idx > 0 && (
                <div
                  style={{
                    flex: 1,
                    height: '2px',
                    backgroundColor: isCompleted ? 'var(--status-green)' : 'var(--border-color)',
                    marginTop: '15px',
                    marginLeft: '-4px',
                    marginRight: '-4px',
                    zIndex: 1,
                  }}
                />
              )}

              {/* Step indicator node */}
              <div
                onClick={() => {
                  if (onSelectStage) {
                    if (step.key === 'lead') onSelectStage('lead');
                    else if (step.key === 'survey') onSelectStage('survey');
                    else if (step.key === 'design' || step.key === 'bom') onSelectStage('design');
                    else if (step.key === 'supply') onSelectStage('procurement');
                    else if (step.key === 'installation') onSelectStage('installation');
                    else if (step.key === 'inspection') onSelectStage('inspection');
                    else if (step.key === 'wcr') onSelectStage('wcr');
                    else if (step.key === 'grid_sync') onSelectStage('commissioned');
                    else onSelectStage('oam');
                  }
                }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  width: '90px',
                  cursor: onSelectStage ? 'pointer' : 'default',
                  zIndex: 2,
                }}
              >
                {/* Circle Icon */}
                <div
                  style={{
                    width: '30px',
                    height: '30px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontWeight: 700,
                    backgroundColor: isCompleted
                      ? 'var(--status-green-bg)'
                      : isCurrent
                      ? 'var(--primary-navy)'
                      : '#FFFFFF',
                    color: isCompleted
                      ? 'var(--status-green)'
                      : isCurrent
                      ? '#FFFFFF'
                      : 'var(--text-muted)',
                    border: `2px solid ${
                      isCompleted
                        ? 'var(--status-green)'
                        : isCurrent
                        ? 'var(--primary-navy)'
                        : 'var(--border-color)'
                    }`,
                  }}
                >
                  {isCompleted ? <Check size={16} strokeWidth={3} /> : step.stepNumber}
                </div>

                {/* Step Label */}
                <div
                  style={{
                    marginTop: '8px',
                    fontSize: '11px',
                    lineHeight: '1.25',
                    textAlign: 'center',
                    fontWeight: isCurrent || isCompleted ? 600 : 400,
                    color: isCurrent
                      ? 'var(--primary-navy)'
                      : isCompleted
                      ? 'var(--text-main)'
                      : 'var(--text-muted)',
                  }}
                >
                  {lang === 'hi' ? step.labelHi : step.labelEn}
                </div>

                {/* Current Stage Text Badge */}
                {isCurrent && (
                  <span
                    style={{
                      marginTop: '4px',
                      fontSize: '9px',
                      fontWeight: 700,
                      backgroundColor: 'var(--primary-navy)',
                      color: '#FFFFFF',
                      padding: '1px 5px',
                      borderRadius: '2px',
                      textTransform: 'uppercase',
                    }}
                  >
                    {lang === 'hi' ? 'वर्तमान चरण' : 'Current stage'}
                  </span>
                )}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
