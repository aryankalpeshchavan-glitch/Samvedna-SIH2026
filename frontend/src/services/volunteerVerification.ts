export interface VolunteerRecord {
  id: string;
  name: string;
  organization: string;
  role: string;
  certifications: string;
  phone: string;
  status: 'VERIFIED_ACTIVE' | 'REVOKED' | 'EXPIRED';
  photoUrl?: string;
  issueDate: string;
}

export const MOCK_VOLUNTEER_DATABASE: Record<string, VolunteerRecord> = {
  'NDRF-VOL-7842': {
    id: 'NDRF-VOL-7842',
    name: 'Ramesh Gogoi',
    organization: 'NDRF 1st Battalion (Guwahati)',
    role: 'Lead Search & Rescue Specialist',
    certifications: 'High-Altitude Rescue, Advanced First Aid',
    phone: '+91 98640 12345',
    status: 'VERIFIED_ACTIVE',
    issueDate: '2025-04-10',
  },
  'SDRF-VOL-3091': {
    id: 'SDRF-VOL-3091',
    name: 'Ananya Hazarika',
    organization: 'Assam SDRF Unit 4',
    role: 'Medical Evacuation Corps',
    certifications: 'Triage & Emergency Life Support',
    phone: '+91 94350 98765',
    status: 'VERIFIED_ACTIVE',
    issueDate: '2025-06-18',
  },
  'MDoNER-CERT-019': {
    id: 'MDoNER-CERT-019',
    name: 'Bikram Thapa',
    organization: 'MDoNER Field Response Mesh',
    role: 'Community Shelter Coordinator',
    certifications: 'Geospatial Field Survey',
    phone: '+91 97060 54321',
    status: 'VERIFIED_ACTIVE',
    issueDate: '2025-08-01',
  },
};

export function verifyVolunteerQrCode(scannedText: string): {
  isValid: boolean;
  volunteer?: VolunteerRecord;
  scannedCode: string;
} {
  const cleanCode = scannedText.trim().toUpperCase();
  const found = MOCK_VOLUNTEER_DATABASE[cleanCode];

  if (found) {
    return {
      isValid: true,
      volunteer: found,
      scannedCode: cleanCode,
    };
  }

  return {
    isValid: false,
    scannedCode: cleanCode,
  };
}
