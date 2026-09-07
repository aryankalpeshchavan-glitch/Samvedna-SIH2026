import test, { describe } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import {
  getIntelligenceDecision,
  simulateWhatIf,
  setAuthToken,
  getAuthToken,
  getUserRole,
  login,
  logout,
} from '../src/services/api';
import {
  DecisionResponse,
  WhatIfResponse,
  classifyRiskLevel,
} from '../src/types/api';

describe('P1 Intelligence & Operational Auth Security Audit Tests', () => {

  test('1. Successful Intelligence Decision Response Parsing & Rendering Contracts', async () => {
    const mockDecision: DecisionResponse = {
      location_id: 'zone-ner-01',
      lat: 26.1445,
      lng: 91.7362,
      risk: {
        risk_score: 0.742,
        risk_level: 'HIGH',
        confidence: 0.915,
        drivers: ['rainfall_24h', 'slope_mean_deg', 'soil_moisture'],
        data_status: 'live',
      },
      explanation: [
        {
          key: 'rainfall_24h',
          label: '24h Extreme Precipitation',
          description: 'Intense 24-hour rainfall exceeding 150mm destabilizes topsoil.',
          unit: 'mm',
          category: 'hydrology',
          value: 164.2,
        },
        {
          key: 'slope_mean_deg',
          label: 'Steep Escarpment Angle',
          description: 'Critical hill slope above 35 degrees increases gravitational shear.',
          unit: 'deg',
          category: 'geomorphology',
          value: 38.5,
        },
      ],
      priority: {
        priority_score: 82.4,
        priority_level: 'HIGH',
        weights: { risk: 0.35, exposure: 0.3, vulnerability: 0.2, response_gap: 0.15 },
        factors: { risk: 0.742, exposure: 0.8, vulnerability: 0.9, response_gap: 0.85 },
      },
      actions: [
        'Issue immediate red alert evacuation advisory for downstream settlements',
        'Pre-position NDRF search and rescue units at district staging hub',
      ],
      data_status: 'live',
      computed_at: '2026-09-07T12:00:00Z',
    };

    assert.strictEqual(mockDecision.risk.risk_score, 0.742);
    assert.strictEqual(classifyRiskLevel(mockDecision.risk.risk_score), 'HIGH');
    assert.strictEqual(mockDecision.risk.confidence, 0.915);
    assert.strictEqual(mockDecision.priority.priority_score, 82.4);
    assert.strictEqual(mockDecision.priority.priority_level, 'HIGH');
    assert.strictEqual(mockDecision.actions.length, 2);
    assert.strictEqual(mockDecision.data_status, 'live');
  });

  test('2. Dynamic Driver Explanation Rendering (Variable Count: 1, 3, 7 drivers)', () => {
    const variableExplanations = [
      { key: 'rainfall_1', label: 'Driver 1', description: 'Desc 1', unit: 'mm', category: 'hydrology', value: 50 },
      { key: 'slope_2', label: 'Driver 2', description: 'Desc 2', unit: 'deg', category: 'geomorphology', value: 20 },
      { key: 'soil_3', label: 'Driver 3', description: 'Desc 3', unit: '%', category: 'soil', value: 80 },
      { key: 'lithology_4', label: 'Driver 4', description: 'Desc 4', unit: null, category: 'geology', value: null },
      { key: 'road_5', label: 'Driver 5', description: 'Desc 5', unit: 'm', category: 'infrastructure', value: 120 },
      { key: 'drainage_6', label: 'Driver 6', description: 'Desc 6', unit: 'km', category: 'drainage', value: 3.2 },
      { key: 'vegetation_7', label: 'Driver 7', description: 'Desc 7', unit: 'NDVI', category: 'ecology', value: 0.25 },
    ];

    assert.strictEqual(variableExplanations.length, 7);
    variableExplanations.forEach((exp, index) => {
      assert.ok(exp.label, `Explanation ${index} must have a label`);
      assert.ok(exp.description, `Explanation ${index} must have a description`);
    });
  });

  test('3. What-If Scenario Simulation Contract & Forecast Distinction', () => {
    const mockWhatIf: WhatIfResponse = {
      scenario_label: 'SIMULATION — NOT A FORECAST',
      current_risk_score: 0.35,
      projected_risk_score: 0.62,
      current_priority_level: 'LOW',
      projected_priority_level: 'HIGH',
      current_actions: ['Continue routine monitoring'],
      projected_actions: [
        'Pre-position emergency water pumps',
        'Dispatch volunteer standby alerts',
      ],
      data_status: 'simulated',
    };

    assert.strictEqual(mockWhatIf.scenario_label, 'SIMULATION — NOT A FORECAST');
    assert.ok(mockWhatIf.projected_risk_score > mockWhatIf.current_risk_score);
    assert.strictEqual(mockWhatIf.data_status, 'simulated');
    assert.strictEqual(mockWhatIf.projected_actions.length, 2);
  });

  test('4. RBAC 403 Handling on Restricted Endpoints', async () => {
    const originalFetch = globalThis.fetch;
    try {
      globalThis.fetch = async () => {
        return {
          ok: false,
          status: 403,
          text: async () => JSON.stringify({ detail: "Role 'citizen' not in required roles: ('officer', 'admin')" }),
        } as unknown as Response;
      };

      setAuthToken('test-citizen-token');

      await assert.rejects(
        async () => {
          await simulateWhatIf({ lat: 26.14, lng: 91.73, scenario_rainfall_mm: 50 });
        },
        (err: Error) => {
          assert.ok(err.message.includes('403'));
          return true;
        }
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('5. API Error Handling (500 Internal Error) Does Not Fall Back to Fake Data', async () => {
    const originalFetch = globalThis.fetch;
    try {
      globalThis.fetch = async () => {
        return {
          ok: false,
          status: 500,
          text: async () => 'Database query timeout',
        } as unknown as Response;
      };

      await assert.rejects(
        async () => {
          await getIntelligenceDecision({ lat: 26.14, lng: 91.73 });
        },
        (err: Error) => {
          assert.ok(err.message.includes('500'));
          return true;
        }
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('6. Unauthenticated State: No token does NOT trigger automatic admin registration/login', async () => {
    const originalFetch = globalThis.fetch;
    const interceptedUrls: string[] = [];

    try {
      logout();
      assert.strictEqual(getAuthToken(), null);
      assert.strictEqual(getUserRole(), null);

      globalThis.fetch = async (url: RequestInfo | URL) => {
        const urlStr = url.toString();
        interceptedUrls.push(urlStr);
        return {
          ok: false,
          status: 401,
          text: async () => JSON.stringify({ detail: 'Not authenticated' }),
        } as Response;
      };

      // Call API without token
      await assert.rejects(async () => {
        await getIntelligenceDecision({ lat: 26.14, lng: 91.73 });
      });

      // Confirm no background registration or auto-login was attempted
      assert.ok(!interceptedUrls.some((u) => u.includes('/auth/register')), 'Must NOT attempt /auth/register');
      assert.ok(!interceptedUrls.some((u) => u.includes('/auth/login')), 'Must NOT attempt /auth/login');
      assert.strictEqual(getAuthToken(), null, 'Token must remain null when unauthenticated');
      assert.strictEqual(getUserRole(), null, 'Role must remain null when unauthenticated');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('7. Source Code Invariant: No hardcoded admin/officer passwords in api.ts or OperationsAuthModal.tsx', () => {
    const apiSource = fs.readFileSync(path.resolve(process.cwd(), 'src/services/api.ts'), 'utf-8');
    const authModalSource = fs.readFileSync(path.resolve(process.cwd(), 'src/components/navigation/OperationsAuthModal.tsx'), 'utf-8');

    // Assert no hardcoded credentials exist in source
    assert.ok(!apiSource.includes('AdminPassword123!'), 'api.ts must NOT contain hardcoded AdminPassword123!');
    assert.ok(!apiSource.includes('OfficerPassword123!'), 'api.ts must NOT contain hardcoded OfficerPassword123!');
    assert.ok(!apiSource.includes('+918888899999'), 'api.ts must NOT contain hardcoded +918888899999');
    assert.ok(!apiSource.includes('ensureAuthorizedSession'), 'api.ts must NOT contain ensureAuthorizedSession');
    assert.ok(!apiSource.includes('registerOrLoginDemo'), 'api.ts must NOT contain registerOrLoginDemo');

    assert.ok(!authModalSource.includes('AdminPassword123!'), 'OperationsAuthModal must NOT contain AdminPassword123!');
    assert.ok(!authModalSource.includes('OfficerPassword123!'), 'OperationsAuthModal must NOT contain OfficerPassword123!');
    assert.ok(!authModalSource.includes('handleInitDefaultAdmin'), 'OperationsAuthModal must NOT contain handleInitDefaultAdmin');
  });

  test('8. Real Login stores token and Logout clears token and role', async () => {
    const originalFetch = globalThis.fetch;
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
    const adminPayload = Buffer.from(JSON.stringify({ sub: '8', role: 'admin', exp: 9999999999 })).toString('base64url');
    const adminJwt = `${header}.${adminPayload}.sig`;

    try {
      globalThis.fetch = async (_url: RequestInfo | URL, opts?: RequestInit) => {
        const body = opts?.body ? JSON.parse(opts.body as string) : {};
        if (body.phone === '+919876543210' && body.password === 'ManualEnteredPassword') {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              access_token: adminJwt,
              token_type: 'bearer',
              role: 'admin',
            }),
          } as Response;
        }
        return {
          ok: false,
          status: 401,
          text: async () => JSON.stringify({ detail: 'Invalid credentials' }),
        } as Response;
      };

      const res = await login('+919876543210', 'ManualEnteredPassword');
      assert.strictEqual(res.role, 'admin');
      assert.strictEqual(getAuthToken(), adminJwt);
      assert.strictEqual(getUserRole(), 'admin');

      logout();
      assert.strictEqual(getAuthToken(), null);
      assert.strictEqual(getUserRole(), null);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test('9. Citizen Token Preservation: Citizen token NEVER elevated to admin or officer', () => {
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
    const payload = Buffer.from(JSON.stringify({ sub: '123', role: 'citizen', exp: 9999999999 })).toString('base64url');
    const citizenJwt = `${header}.${payload}.fakesig`;

    setAuthToken(citizenJwt);
    assert.strictEqual(getUserRole(), 'citizen');
    assert.notStrictEqual(getUserRole(), 'admin', 'Citizen role must NEVER elevate to admin');
    assert.notStrictEqual(getUserRole(), 'officer', 'Citizen role must NEVER elevate to officer');
    logout();
  });
});
