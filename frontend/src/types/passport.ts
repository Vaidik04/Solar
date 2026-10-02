export type PlantStage =
  | 'lead'
  | 'survey'
  | 'design'
  | 'bom'
  | 'supply'
  | 'installation'
  | 'inspection'
  | 'wcr'
  | 'commissioned'
  | 'oam';

export interface PlantPassport {
  plantId: string;
  projectName: string;
  customerName: string;
  customerType: 'Commercial' | 'Industrial' | 'Residential';
  phone: string;
  email: string;
  siteAddress: string;
  stateCode: string;
  discomName: string;
  consumerNumber: string;
  sanctionedLoadKw: number;
  capacityKwpDc: number;
  capacityKwAc: number;
  currentStage: PlantStage;
  performanceRatio: number;
  todayGenerationKwh: number;
  lifetimeGenerationMwh: number;
  co2OffsetTons: number;
  qrVerificationToken: string;
  commissionedDate: string;
  digitalFingerprintSha256: string;
}

export interface BOMItem {
  id: string;
  category: string;
  make: string;
  model: string;
  quantity: number;
  unit: string;
  itemCode: string;
  isSerialized: boolean;
  allocatedCount: number;
  installedCount: number;
}

export interface ReconciliationItem {
  key: string;
  category: string;
  plannedQty: number;
  actualQty: number;
  delta: number;
  status: 'match' | 'mismatch' | 'missing_actual' | 'waived';
  notes?: string;
}

export interface ComplianceRuleItem {
  code: string;
  title: string;
  ruleType: string;
  status: 'pass' | 'fail' | 'waived';
  reason: string;
  waiverInfo?: {
    grantedBy: string;
    reason: string;
    expiresAt: string;
  };
}

export interface InspectionCheckItem {
  code: string;
  label: string;
  result: 'pass' | 'fail';
  remarks?: string;
}

export interface ServiceTicketItem {
  id: string;
  number: string;
  title: string;
  category: 'corrective' | 'preventive' | 'emergency';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  responseDueMinutes: number;
  assignee: string;
}

export interface GenerationPoint {
  time: string;
  powerKw: number;
  irradianceWm2: number;
  expectedKw: number;
}
