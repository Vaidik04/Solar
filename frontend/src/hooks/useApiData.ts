/**
 * Solar Operations OS — Data Hooks
 *
 * React hooks for fetching live data from the backend.
 * Each hook returns { data, isLoading, error, refetch }.
 *
 * Falls back gracefully if the backend is offline — the mock data
 * remains available as the default initialState.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ApiError,
  complianceApi,
  crmApi,
  oamApi,
  projectApi,
  telemetryApi,
} from '../lib/api';
import type {
  ComplianceRunOut,
  CustomerRead,
  GenerationRecordOut,
  GenerationSummaryOut,
  ProjectRead,
  ServiceTicketOut,
  SiteRead,
  TelemetryAlarmOut,
} from '../lib/api';

// ── Generic fetch hook ─────────────────────────────────────────────────────────
interface FetchState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

function useFetch<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
): FetchState<T> & { refetch: () => void } {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    isLoading: true,
    error: null,
  });
  const mountedRef = useRef(true);

  const run = useCallback(async () => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const data = await fetcher();
      if (mountedRef.current) {
        setState({ data, isLoading: false, error: null });
      }
    } catch (err) {
      if (mountedRef.current) {
        const msg = err instanceof ApiError ? err.detail : 'Failed to load data';
        setState({ data: null, isLoading: false, error: msg });
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mountedRef.current = true;
    void run();
    return () => {
      mountedRef.current = false;
    };
  }, [run]);

  return { ...state, refetch: run };
}

// ── Projects ───────────────────────────────────────────────────────────────────
export function useProjects(stage?: string) {
  return useFetch<ProjectRead[]>(
    () => projectApi.list(stage),
    [stage],
  );
}

export function useProject(id: string | null) {
  return useFetch<ProjectRead>(
    () => projectApi.get(id!),
    [id],
  );
}

// ── Customers ─────────────────────────────────────────────────────────────────
export function useCustomers(query?: string) {
  return useFetch<CustomerRead[]>(
    () => crmApi.listCustomers(50, query),
    [query],
  );
}

export function useCustomer(id: string | null) {
  return useFetch<CustomerRead>(
    () => crmApi.getCustomer(id!),
    [id],
  );
}

// ── Sites ─────────────────────────────────────────────────────────────────────
export function useSites(customerId?: string) {
  return useFetch<SiteRead[]>(
    () => crmApi.listSites(customerId),
    [customerId],
  );
}

// ── Telemetry — Generation ────────────────────────────────────────────────────
export function useGenerationSummary(plantId: string | null) {
  return useFetch<GenerationSummaryOut>(
    () => telemetryApi.getGenerationSummary(plantId!),
    [plantId],
  );
}

export function useGenerationRecords(plantId: string | null, limit = 100) {
  return useFetch<GenerationRecordOut[]>(
    () => telemetryApi.listGenerationRecords(plantId!, limit),
    [plantId, limit],
  );
}

// ── Telemetry — Alarms ────────────────────────────────────────────────────────
export function useAlarms(plantId?: string, status?: string) {
  return useFetch<TelemetryAlarmOut[]>(
    () => telemetryApi.listAlarms(plantId, status),
    [plantId, status],
  );
}

// ── Compliance ────────────────────────────────────────────────────────────────
export function useComplianceRuns(projectId: string | null) {
  return useFetch<ComplianceRunOut[]>(
    () => complianceApi.listRuns(projectId!),
    [projectId],
  );
}

// ── O&M Tickets ───────────────────────────────────────────────────────────────
export function useServiceTickets(plantId?: string, status?: string) {
  return useFetch<ServiceTicketOut[]>(
    () => oamApi.listTickets(plantId, status),
    [plantId, status],
  );
}

// ── Active alarms count badge (polled every 30s) ──────────────────────────────
export function useActiveAlarmsCount(plantId?: string): number {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const alarms = await telemetryApi.listAlarms(plantId, 'active');
        setCount(alarms.length);
      } catch {
        // silently ignore — count stays at last known value
      }
    };
    void fetchCount();
    const timer = setInterval(() => void fetchCount(), 30_000);
    return () => clearInterval(timer);
  }, [plantId]);

  return count;
}
