import React from 'react';
import { Search, LogOut, Globe, User } from 'lucide-react';
import type { CurrentUser } from '../contexts/AuthContext';

interface HeaderProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  currentUser?: CurrentUser | null;
  onLogout?: () => void;
  lang: 'en' | 'hi';
  onToggleLang: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  searchTerm,
  onSearchChange,
  currentUser,
  onLogout,
  lang,
  onToggleLang,
}) => {
  return (
    <header
      className="no-print"
      style={{
        backgroundColor: 'var(--bg-header)',
        color: '#FFFFFF',
        borderBottom: '3px solid #0E1F58',
        boxShadow: '0 2px 6px rgba(0,0,0,0.12)',
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '20px',
          flexWrap: 'wrap',
        }}
      >
        {/* Left: Official MPEB Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: '320px' }}>
          {/* MPEB Official Insignia (SVG) */}
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              backgroundColor: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px solid #E4E7EB',
              flexShrink: 0,
            }}
          >
            <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" fill="#1F3A93" />
              <circle cx="20" cy="20" r="15" fill="#FFFFFF" />
              {/* Sun & Power Bolt Symbol */}
              <circle cx="20" cy="20" r="8" fill="#ED8F00" />
              <polygon points="19,10 23,10 17,21 22,21 16,30 25,18 20,18" fill="#1F3A93" />
            </svg>
          </div>

          <div>
            <div style={{ fontSize: '17px', fontWeight: 700, letterSpacing: '-0.01em', lineHeight: '1.2' }}>
              {lang === 'hi' ? 'म.प्र.वि.मं. सौर संयंत्र सत्यापन पोर्टल' : 'MPEB Solar Plant Verification Portal'}
            </div>
            <div style={{ fontSize: '12px', color: '#DCE4F5', marginTop: '2px' }}>
              {lang === 'hi'
                ? 'मध्य प्रदेश पूर्व/मध्य/पश्चिम क्षेत्र विद्युत वितरण कंपनी • भोपाल केंद्रीय वृत्त'
                : 'Government of Madhya Pradesh • Bhopal Central Circle, City Division West'}
            </div>
          </div>
        </div>

        {/* Centre: Plain Search Box */}
        <div className="gov-header-search" style={{ flex: '1 1 360px', maxWidth: '520px', position: 'relative' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-secondary)',
            }}
          />
          <input
            id="global-plant-search"
            type="text"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={
              lang === 'hi'
                ? 'संयंत्र आईडी, उपभोक्ता क्रमांक अथवा क्रम संख्या से खोजें...'
                : 'Search by plant ID, consumer number or serial number'
            }
            style={{
              width: '100%',
              height: '40px',
              padding: '8px 14px 8px 36px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #C4D2EE',
              backgroundColor: '#FFFFFF',
              color: 'var(--text-main)',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>

        {/* Right: Officer Profile, Designation, Hindi Toggle & Logout */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
          {/* Language Toggle (English / Hindi) */}
          <button
            onClick={onToggleLang}
            className="gov-btn"
            style={{
              height: '36px',
              minHeight: '36px',
              padding: '4px 10px',
              backgroundColor: 'rgba(255,255,255,0.12)',
              color: '#FFFFFF',
              border: '1px solid rgba(255,255,255,0.25)',
              fontSize: '12px',
              fontWeight: 600,
            }}
            title={lang === 'hi' ? 'Switch to English' : 'हिंदी में देखें'}
          >
            <Globe size={14} />
            <span>{lang === 'hi' ? 'English' : 'हिंदी'}</span>
          </button>

          {/* Officer Details */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              borderLeft: '1px solid rgba(255, 255, 255, 0.25)',
              paddingLeft: '16px',
            }}
          >
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid rgba(255,255,255,0.3)',
              }}
            >
              <User size={18} color="#FFFFFF" />
            </div>

            <div style={{ textAlign: 'left', lineHeight: '1.25' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#FFFFFF' }}>
                {currentUser?.email?.includes('tatapower')
                  ? 'Er. Rajesh Sharma'
                  : currentUser?.email?.split('@')[0] || 'Er. Rajesh Sharma'}
              </div>
              <div style={{ fontSize: '11px', color: '#DCE4F5' }}>
                {lang === 'hi'
                  ? 'कार्यपालन यंत्री (संचा. एवं संधा.), संभाग पश्चिम'
                  : 'Executive Engineer (O&M), Bhopal West'}
              </div>
            </div>

            {onLogout && (
              <button
                onClick={onLogout}
                className="gov-btn"
                style={{
                  height: '36px',
                  minHeight: '36px',
                  padding: '4px 10px',
                  marginLeft: '8px',
                  backgroundColor: 'rgba(198, 40, 40, 0.85)',
                  color: '#FFFFFF',
                  fontSize: '12px',
                }}
                title={lang === 'hi' ? 'लॉगआउट करें' : 'Sign out'}
              >
                <LogOut size={13} />
                <span>{lang === 'hi' ? 'लॉगआउट' : 'Logout'}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
