import React, { useState } from 'react';
import {
  Download,
  Printer,
  QrCode,
  ChevronDown,
} from 'lucide-react';

import { Header } from './components/Header';
import { MetricCards } from './components/MetricCards';
import { LifecycleStepper } from './components/LifecycleStepper';
import { PassportQrModal } from './components/PassportQrModal';
import { OfficerActionBar } from './components/OfficerActionBar';

import { OverviewTab } from './components/tabs/OverviewTab';
import { DesignBOMTab } from './components/tabs/DesignBOMTab';
import { ReconciliationTab } from './components/tabs/ReconciliationTab';
import { ComplianceTab } from './components/tabs/ComplianceTab';
import { FieldWCRTab } from './components/tabs/FieldWCRTab';
import { WarrantyOamTab } from './components/tabs/WarrantyOamTab';
import { TelemetryTab } from './components/tabs/TelemetryTab';

import { useAuth } from './contexts/AuthContext';
import { LoginPage } from './components/LoginPage';

import {
  initialPlantPassport,
  mockBOMItems,
  mockReconciliationItems,
  mockComplianceRules,
  mockInspectionChecks,
  mockServiceTickets,
  mockGenerationData,
} from './data/mockPlantData';

type TabId =
  | 'overview'
  | 'design_bom'
  | 'reconciliation'
  | 'compliance'
  | 'field_wcr'
  | 'warranty_oam'
  | 'telemetry';

interface TabDefinition {
  id: TabId;
  labelEn: string;
  labelHi: string;
  count?: number;
}

export const App: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [passport] = useState(initialPlantPassport);
  const [isQrModalOpen, setIsQrModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);

  // Authentication Loading State
  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#F5F7FA',
          color: '#52606D',
          gap: '12px',
        }}
      >
        <div style={{ fontSize: '15px', fontWeight: 600 }}>
          {lang === 'hi' ? 'म.प्र.वि.मं. पोर्टल लोड हो रहा है...' : 'Loading MPEB Verification Portal...'}
        </div>
      </div>
    );
  }

  // Authentication Gate: Render Official Login Portal if not logged in
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Primary 6 Tabs + Overflow Tab
  const primaryTabs: TabDefinition[] = [
    { id: 'overview', labelEn: 'Overview', labelHi: 'संक्षिप्त विवरण' },
    { id: 'design_bom', labelEn: 'Design & BOM', labelHi: 'प्रारूप एवं सामग्री सूची', count: mockBOMItems.length },
    { id: 'reconciliation', labelEn: 'Reconciliation', labelHi: 'सामग्री मिलान', count: mockReconciliationItems.length },
    { id: 'compliance', labelEn: 'Compliance', labelHi: 'विनियमन अनुपालन', count: mockComplianceRules.length },
    { id: 'field_wcr', labelEn: 'Inspection & completion report', labelHi: 'निरीक्षण एवं WCR प्रतिवेदन' },
    { id: 'warranty_oam', labelEn: 'Warranty & O&M', labelHi: 'वारंटी एवं संधारण' },
  ];

  const overflowTabs: TabDefinition[] = [
    { id: 'telemetry', labelEn: 'Live Telemetry & Generation', labelHi: 'वास्तविक समय उत्पादन टेलीमेट्री' },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-page)' }}>
      
      {/* Print-Only Official Document Header */}
      <div className="print-only-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '18pt', fontWeight: 'bold' }}>Madhya Pradesh Electricity Board (MPEB)</h2>
            <div style={{ fontSize: '11pt' }}>Solar Rooftop / Grid-Connected Verification Inspection Dossier</div>
            <div style={{ fontSize: '10pt', color: '#555' }}>Bhopal Central Circle • City Division West</div>
          </div>
          <div style={{ textAlign: 'right', fontSize: '10pt' }}>
            <div><strong>Date:</strong> {new Date().toLocaleDateString('en-IN')}</div>
            <div><strong>Plant ID:</strong> {passport.plantId}</div>
            <div><strong>Officer:</strong> Er. Rajesh Sharma, EE (O&M)</div>
          </div>
        </div>
      </div>

      {/* Top Government Application Header */}
      <Header
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        currentUser={user}
        onLogout={logout}
        lang={lang}
        onToggleLang={() => setLang(lang === 'en' ? 'hi' : 'en')}
      />

      {/* Main Content Workspace Container */}
      <main style={{ flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '16px 24px 60px 24px' }}>
        
        {/* Breadcrumb Navigation */}
        <nav className="gov-breadcrumb no-print" aria-label="Breadcrumb">
          <a href="#home">{lang === 'hi' ? 'मुख्य पृष्ठ (Home)' : 'Home'}</a>
          <span className="divider">&gt;</span>
          <a href="#plants">{lang === 'hi' ? 'सौर संयंत्र सूची' : 'Plants'}</a>
          <span className="divider">&gt;</span>
          <span className="current">{passport.plantId}</span>
        </nav>

        {/* Page Top Title & Official Toolbar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
            marginBottom: '18px',
          }}
        >
          {/* Title with Plant Name and ONE Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              {passport.projectName}{' '}
              <span style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-secondary)' }}>
                ({passport.plantId})
              </span>
            </h1>

            {/* ONE clear text status badge */}
            <span className="gov-badge gov-badge-green" style={{ fontSize: '13px', padding: '4px 10px' }}>
              {lang === 'hi' ? 'सक्रिय एवं ग्रिड संयोजित' : 'In operation'}
            </span>
          </div>

          {/* Toolbar Buttons: Export Dossier (PDF), Print, View QR */}
          <div className="no-print" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => alert(`Exporting official audit dossier for ${passport.plantId} (PDF)...`)}
              className="gov-btn gov-btn-secondary"
              title="Download official PDF audit dossier"
            >
              <Download size={15} />
              <span>{lang === 'hi' ? 'प्रतिवेदन डाउनलोड (PDF)' : 'Export Dossier (PDF)'}</span>
            </button>

            <button
              onClick={() => window.print()}
              className="gov-btn gov-btn-secondary print-keep"
              title="Print official verification sheet"
            >
              <Printer size={15} />
              <span>{lang === 'hi' ? 'प्रिंट करें (Print)' : 'Print'}</span>
            </button>

            <button
              onClick={() => setIsQrModalOpen(true)}
              className="gov-btn gov-btn-primary"
              title="View verification QR certificate"
            >
              <QrCode size={15} />
              <span>{lang === 'hi' ? 'सत्यापन क्यूआर (View QR)' : 'View QR'}</span>
            </button>
          </div>
        </div>

        {/* 4 Summary Cards (Flat, No Icons, Collapsible Performance Table) */}
        <MetricCards passport={passport} lang={lang} />

        {/* 10-Stage Plant Progress Stepper with Full Labels */}
        <LifecycleStepper
          currentStage={passport.currentStage}
          lang={lang}
          onSelectStage={(stage) => {
            if (stage === 'lead' || stage === 'survey') setActiveTab('overview');
            else if (stage === 'design') setActiveTab('design_bom');
            else if (stage === 'procurement') setActiveTab('reconciliation');
            else if (stage === 'inspection' || stage === 'wcr') setActiveTab('field_wcr');
            else if (stage === 'commissioned') setActiveTab('field_wcr');
            else if (stage === 'oam') setActiveTab('warranty_oam');
          }}
        />

        {/* Government Navigation Tabs Bar (With Plain Numbers & Overflow More Menu) */}
        <div className="gov-nav-tabs no-print" role="tablist">
          {primaryTabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                className={`gov-nav-tab ${isActive ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(tab.id);
                  setIsMoreMenuOpen(false);
                }}
              >
                <span>{lang === 'hi' ? tab.labelHi : tab.labelEn}</span>
                {tab.count !== undefined && (
                  <span className="tab-count">({tab.count})</span>
                )}
              </button>
            );
          })}

          {/* Overflow "More" Menu Dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              className={`gov-nav-tab ${overflowTabs.some((t) => t.id === activeTab) ? 'active' : ''}`}
              onClick={() => setIsMoreMenuOpen(!isMoreMenuOpen)}
              style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
              aria-haspopup="true"
              aria-expanded={isMoreMenuOpen}
            >
              <span>{lang === 'hi' ? 'अतिरिक्त (More)' : 'More'}</span>
              <ChevronDown size={14} />
            </button>

            {isMoreMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  backgroundColor: '#FFFFFF',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: 'var(--shadow-modal)',
                  minWidth: '220px',
                  zIndex: 950,
                  marginTop: '4px',
                }}
              >
                {overflowTabs.map((otab) => (
                  <button
                    key={otab.id}
                    onClick={() => {
                      setActiveTab(otab.id);
                      setIsMoreMenuOpen(false);
                    }}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      textAlign: 'left',
                      background: activeTab === otab.id ? 'var(--primary-navy-light)' : 'none',
                      color: activeTab === otab.id ? 'var(--primary-navy)' : 'var(--text-main)',
                      fontWeight: activeTab === otab.id ? 700 : 500,
                      border: 'none',
                      borderBottom: '1px solid var(--border-light)',
                      fontSize: '13px',
                      cursor: 'pointer',
                    }}
                  >
                    {lang === 'hi' ? otab.labelHi : otab.labelEn}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Active Tab View Body */}
        {activeTab === 'overview' && (
          <OverviewTab passport={passport} onOpenQr={() => setIsQrModalOpen(true)} lang={lang} />
        )}

        {activeTab === 'design_bom' && (
          <DesignBOMTab items={mockBOMItems} lang={lang} />
        )}

        {activeTab === 'reconciliation' && (
          <ReconciliationTab items={mockReconciliationItems} lang={lang} />
        )}

        {activeTab === 'compliance' && (
          <ComplianceTab rules={mockComplianceRules} lang={lang} />
        )}

        {activeTab === 'field_wcr' && (
          <FieldWCRTab checks={mockInspectionChecks} lang={lang} />
        )}

        {activeTab === 'warranty_oam' && (
          <WarrantyOamTab tickets={mockServiceTickets} lang={lang} />
        )}

        {activeTab === 'telemetry' && (
          <TelemetryTab generationData={mockGenerationData} lang={lang} />
        )}

      </main>

      {/* Sticky Officer Action Bar at Bottom of Page */}
      <OfficerActionBar plantId={passport.plantId} lang={lang} />

      {/* Digital Passport QR Verification Modal */}
      {isQrModalOpen && (
        <PassportQrModal
          passport={passport}
          onClose={() => setIsQrModalOpen(false)}
          lang={lang}
        />
      )}

      {/* Official Government Portal Footer */}
      <footer
        className="no-print"
        style={{
          borderTop: '1px solid var(--border-color)',
          padding: '16px 24px',
          fontSize: '12px',
          color: 'var(--text-secondary)',
          backgroundColor: '#FFFFFF',
          marginTop: 'auto',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            maxWidth: '1440px',
            margin: '0 auto',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div>
            <strong>MPEB Solar Plant Verification Portal</strong> • Government of Madhya Pradesh Energy Department
          </div>
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <span>MPERC Net Metering Regs 2026</span>
            <span>•</span>
            <span>MNRE ALMM Enlistment</span>
            <span>•</span>
            <span>CEA Technical Standards for Grid Connectivity</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
