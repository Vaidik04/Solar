/**
 * MPEB Solar Plant Verification Portal — Officer Login Page
 * Government Light Theme with WCAG AA compliance
 */
import React, { useState } from 'react';
import { Eye, EyeOff, Loader2, ShieldCheck, Lock, User, Building2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ApiError } from '../lib/api';

type LoginStep = 'credentials' | 'totp';

export const LoginPage: React.FC = () => {
  const { login, verifyTotp, loginAsDemo } = useAuth();
  const [step, setStep] = useState<LoginStep>('credentials');

  // Credentials form
  const [email, setEmail] = useState('rajesh.sharma@mpeb.mp.gov.in');
  const [password, setPassword] = useState('MPEB@Bhopal2026');
  const [orgSlug, setOrgSlug] = useState('mpeb-bhopal-circle');
  const [showPassword, setShowPassword] = useState(false);

  // TOTP form
  const [totpCode, setTotpCode] = useState('');

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCredentialSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !orgSlug) return;
    setError('');
    setIsLoading(true);
    try {
      const result = await login({ email, password, organization_slug: orgSlug });
      if (result.requiresTotp) {
        setStep('totp');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('Unable to authenticate with central MPEB server. Use demo access below.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleTotpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (totpCode.length !== 6) return;
    setError('');
    setIsLoading(true);
    try {
      await verifyTotp(totpCode);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('Security code verification failed.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
      }}
    >
      {/* Government Emblem & Header */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: '#FFFFFF',
            border: '2px solid #D9DEE5',
            boxShadow: 'var(--shadow-card)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px auto',
          }}
        >
          <svg width="46" height="46" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="18" fill="#1F3A93" />
            <circle cx="20" cy="20" r="15" fill="#FFFFFF" />
            <circle cx="20" cy="20" r="8" fill="#ED8F00" />
            <polygon points="19,10 23,10 17,21 22,21 16,30 25,18 20,18" fill="#1F3A93" />
          </svg>
        </div>

        <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--primary-navy)' }}>
          MPEB Solar Plant Verification Portal
        </h1>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          मध्य प्रदेश विद्युत मंडल • रूफटॉप एवं ग्रिड संयोजित सौर संयंत्र सत्यापन प्रणाली
        </p>
      </div>

      {/* Main Login Card */}
      <div
        className="gov-card"
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '28px',
          boxShadow: 'var(--shadow-card)',
        }}
      >
        {step === 'credentials' ? (
          <>
            <div style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-light)', paddingBottom: '12px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
                विभागीय अधिकारी लॉगिन (Officer Sign In)
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Enter your authorized MPEB energy department credentials
              </p>
            </div>

            <form onSubmit={handleCredentialSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {/* Circle / Division */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                  वृत्त / संभाग (Circle / Division)
                </label>
                <div style={{ position: 'relative' }}>
                  <Building2 size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                  <input
                    type="text"
                    required
                    value={orgSlug}
                    onChange={(e) => setOrgSlug(e.target.value)}
                    style={{
                      width: '100%',
                      height: '40px',
                      padding: '8px 12px 8px 36px',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '13px',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              {/* Officer Email */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                  अधिकारी ईमेल आईडी (Officer Email ID)
                </label>
                <div style={{ position: 'relative' }}>
                  <User size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{
                      width: '100%',
                      height: '40px',
                      padding: '8px 12px 8px 36px',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '13px',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                  पासवर्ड (Password)
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{
                      width: '100%',
                      height: '40px',
                      padding: '8px 38px 8px 36px',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '13px',
                      outline: 'none',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '12px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {error && (
                <div
                  style={{
                    padding: '8px 12px',
                    backgroundColor: 'var(--status-red-bg)',
                    border: '1px solid var(--status-red-border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px',
                    color: 'var(--status-red)',
                  }}
                >
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="gov-btn gov-btn-primary"
                style={{ width: '100%', marginTop: '6px' }}
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>सत्यापन जारी (Verifying)...</span>
                  </>
                ) : (
                  <span>सुरक्षित लॉगिन करें (Sign In as Officer)</span>
                )}
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '4px 0' }}>
                <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border-light)' }} />
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>या (or)</span>
                <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border-light)' }} />
              </div>

              {/* Demo Officer One-Click Access Button */}
              <button
                id="demo-login-btn"
                type="button"
                onClick={loginAsDemo}
                className="gov-btn gov-btn-secondary"
                style={{
                  width: '100%',
                  borderColor: 'var(--primary-navy)',
                  color: 'var(--primary-navy)',
                  fontWeight: 600,
                }}
              >
                <ShieldCheck size={16} color="var(--primary-navy)" />
                <span>अधिकारी डेमो मोड (Enter as Er. Rajesh Sharma, EE)</span>
              </button>

            </form>
          </>
        ) : (
          /* Step: 2FA / TOTP */
          <>
            <div style={{ marginBottom: '20px', textAlign: 'center' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
                सुरक्षा कोड सत्यापन (Two-Factor Verification)
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Enter the 6-digit one-time authorization code sent to your MPEB mobile number
              </p>
            </div>

            <form onSubmit={handleTotpSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <input
                type="text"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                style={{
                  height: '48px',
                  fontSize: '22px',
                  fontFamily: 'var(--font-mono)',
                  letterSpacing: '0.3em',
                  textAlign: 'center',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  outline: 'none',
                }}
              />

              <button
                type="submit"
                disabled={isLoading || totpCode.length !== 6}
                className="gov-btn gov-btn-primary"
              >
                {isLoading ? 'Verifying...' : 'पुष्टि करें एवं प्रवेश करें (Verify & Access)'}
              </button>
            </form>
          </>
        )}
      </div>

      {/* Official Government Footnote */}
      <div style={{ marginTop: '20px', fontSize: '11px', color: 'var(--text-secondary)', textAlign: 'center' }}>
        Government of Madhya Pradesh • Energy Department • MPERC Regulatory Standards 2026
      </div>
    </div>
  );
};
