import React, { useState } from 'react';
import { Download, FileText, Search, Filter } from 'lucide-react';
import { InfoTooltip } from '../InfoTooltip';
import type { BOMItem } from '../../types/passport';

interface DesignBOMTabProps {
  items: BOMItem[];
  lang?: 'en' | 'hi';
}

export const DesignBOMTab: React.FC<DesignBOMTabProps> = ({ items, lang = 'en' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  const filteredItems = items.filter((item) => {
    const matchesSearch =
      item.itemCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      categoryFilter === 'all' || item.category.toLowerCase() === categoryFilter.toLowerCase();

    return matchesSearch && matchesCategory;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Design Engineering & Approval Header */}
      <div className="gov-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
          <div>
            {/* 3 Badges: 2 plain grey text badges + 1 green approved and locked */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span className="gov-badge gov-badge-grey">
                {lang === 'hi' ? 'प्रारूप संस्करण 3' : 'Design version 3'}
              </span>
              <span className="gov-badge gov-badge-grey">
                {lang === 'hi' ? 'सामग्री सूची संशोधन 2' : 'BOM revision 2'}
              </span>
              <span className="gov-badge gov-badge-green">
                {lang === 'hi' ? 'स्वीकृत एवं बंद (Locked)' : 'Approved and locked'}
              </span>
            </div>

            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)' }}>
              {lang === 'hi' ? 'संयंत्र तकनीकी प्रारूप एवं सामग्री विनिर्देश' : 'Plant Technical Design & Bill of Materials'}
            </h2>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              {lang === 'hi'
                ? 'मध्य प्रदेश विद्युत नियामक आयोग (MPERC) तकनीकी मानकों अनुसार सत्यापित।'
                : 'Verified in accordance with MPERC Grid Interactive Solar Standards.'}
            </div>
          </div>

          {/* Document Link: SLD Schematic */}
          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href="#download-sld"
              onClick={(e) => {
                e.preventDefault();
                alert('Downloading engineering single line diagram: SLD-ELEC-125KW-REV3.pdf');
              }}
              className="gov-btn gov-btn-secondary"
              style={{ textDecoration: 'none' }}
            >
              <FileText size={15} color="var(--primary-navy)" />
              <span>SLD-ELEC-125KW-REV3 Engineering Schematic (PDF)</span>
            </a>
          </div>
        </div>

        {/* Technical Specs in a Clean Two-Column Label/Value Table with Units */}
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px', color: 'var(--text-main)' }}>
            {lang === 'hi' ? 'मुख्य तकनीकी विनिर्देश (Technical Specifications)' : 'Key Electrical Specifications'}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            <table className="gov-spec-table">
              <tbody>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'डीसी व्यवस्था (DC arrangement)' : 'DC arrangement'}
                    <InfoTooltip term="DC arrangement" explanation="String sizing: number of parallel strings multiplied by series modules per string." />
                  </td>
                  <td className="value">12 strings x 19 modules</td>
                </tr>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'नाममात्र स्ट्रिंग Voc (Nominal string Voc)' : 'Nominal string Voc'}
                    <InfoTooltip term="Voc" explanation="Open-circuit voltage under standard testing conditions (25°C, 1000 W/m²)." />
                  </td>
                  <td className="value">932.9 V DC</td>
                </tr>
              </tbody>
            </table>

            <table className="gov-spec-table">
              <tbody>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'अधिकतम स्ट्रिंग करंट (Max string current)' : 'Max string current'}
                    <InfoTooltip term="String Current" explanation="Maximum short circuit current (Isc) permitted through each inverter DC string input." />
                  </td>
                  <td className="value">13.44 A</td>
                </tr>
                <tr>
                  <td className="label">
                    {lang === 'hi' ? 'इन्वर्टर एमपीपीटी उपयोग (Inverter MPPTs used)' : 'Inverter MPPTs used'}
                    <InfoTooltip term="MPPT" explanation="Maximum Power Point Tracker channels utilized on grid-tied central string inverters." />
                  </td>
                  <td className="value">10 of 10</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Bill of Materials (BOM) Table Section */}
      <div className="gov-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
              {lang === 'hi' ? 'स्वीकृत सामग्री सूची (Bill of Materials)' : 'Approved Bill of Materials (BOM)'}
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {filteredItems.length} {lang === 'hi' ? 'सामग्रियां सूचीबद्ध' : 'items recorded'}
            </span>
          </div>

          {/* Search, Filter & Export Buttons Above Table */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {/* Table Search */}
            <div style={{ position: 'relative', width: '220px' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={lang === 'hi' ? 'सामग्री खोजें...' : 'Filter items...'}
                style={{
                  width: '100%',
                  height: '36px',
                  padding: '6px 10px 6px 30px',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
            </div>

            {/* Category Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={14} color="var(--text-secondary)" />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                style={{
                  height: '36px',
                  padding: '4px 8px',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  color: 'var(--text-main)',
                  backgroundColor: '#FFFFFF',
                }}
              >
                <option value="all">{lang === 'hi' ? 'सभी श्रेणियां' : 'All categories'}</option>
                <option value="module">{lang === 'hi' ? 'सौर मॉड्यूल' : 'Solar Modules'}</option>
                <option value="inverter">{lang === 'hi' ? 'इन्वर्टर' : 'Inverters'}</option>
                <option value="structure">{lang === 'hi' ? 'माउंटिंग संरचना' : 'Mounting Structure'}</option>
                <option value="meter">{lang === 'hi' ? 'मीटर' : 'Meters'}</option>
                <option value="cable">{lang === 'hi' ? 'केबल' : 'Cables'}</option>
              </select>
            </div>

            {/* Export Buttons */}
            <button
              onClick={() => alert('Exporting Bill of Materials to Excel (.xlsx)...')}
              className="gov-btn gov-btn-secondary"
              style={{ height: '36px', minHeight: '36px', padding: '6px 12px', fontSize: '13px' }}
            >
              <Download size={14} />
              <span>Export (Excel)</span>
            </button>

            <button
              onClick={() => alert('Exporting Bill of Materials to PDF dossier...')}
              className="gov-btn gov-btn-secondary"
              style={{ height: '36px', minHeight: '36px', padding: '6px 12px', fontSize: '13px' }}
            >
              <Download size={14} />
              <span>Export (PDF)</span>
            </button>
          </div>
        </div>

        {/* Full BOM Table */}
        <div className="gov-table-container">
          <table className="gov-table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>{lang === 'hi' ? 'क्र.सं.' : 'S.No'}</th>
                <th>{lang === 'hi' ? 'सामग्री विवरण (Item)' : 'Item Description'}</th>
                <th>{lang === 'hi' ? 'निर्माता / मॉडल (Make / Model)' : 'Make / Model'}</th>
                <th style={{ textAlign: 'right' }}>{lang === 'hi' ? 'मात्रा (Quantity)' : 'Quantity'}</th>
                <th>{lang === 'hi' ? 'इकाई (Unit)' : 'Unit'}</th>
                <th>{lang === 'hi' ? 'टिप्पणी / मानक (Remarks)' : 'Remarks & Standards'}</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item, idx) => (
                <tr key={item.id}>
                  <td style={{ color: 'var(--text-secondary)' }}>{idx + 1}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{item.category}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {item.itemCode}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{item.make}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{item.model}</div>
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    {item.plannedQuantity}
                  </td>
                  <td>{item.unit}</td>
                  <td>
                    <div style={{ fontSize: '12px' }}>
                      {item.verifiedQuantity === item.plannedQuantity ? (
                        <span className="gov-badge gov-badge-green">
                          {lang === 'hi' ? 'पूर्णतः सत्यापित' : '100% Verified'}
                        </span>
                      ) : (
                        <span className="gov-badge gov-badge-amber">
                          {lang === 'hi' ? 'आंशिक' : 'Pending verification'}
                        </span>
                      )}
                      <span style={{ marginLeft: '8px', color: 'var(--text-secondary)' }}>
                        {item.category.includes('Module')
                          ? 'MNRE ALMM List-I Enlisted'
                          : item.category.includes('Inverter')
                          ? 'IEC 62109 / 61727 Certified'
                          : 'IS 2062 HDG Certified'}
                      </span>
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
