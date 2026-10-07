export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "";

export type Gate = {
  type: string;
  qubit?: number | null;
  control?: number | null;
  target?: number | null;
  targets?: number[];
  controls?: number[];
  params?: { theta: number };
};

export type CircuitRequest = {
  gates: Gate[];
  num_qubits: number;
  shots?: number;
  backend?: string;
};

export type CircuitResult = {
  simulation_id: string | null;
  counts: Record<string, number>;
  statevector: number[][] | null;
  circuit_diagram: string | null;
  measurements?: { operation: number; qubits: number[]; bits: string }[];
  measurement_counts?: Record<string, Record<string, number>>;
  metadata?: { statevector_scope: string; bit_order: string; shots: number };
};

export async function apiFetch(path: string, options?: RequestInit) {
  const { headers, ...rest } = options ?? {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const requestHeaders = new Headers({ "Content-Type": "application/json" });
  if (token) requestHeaders.set("Authorization", `Bearer ${token}`);
  new Headers(headers).forEach((value, key) => requestHeaders.set(key, value));
  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
  });
  if (res.status === 401 && token && requestHeaders.get("Authorization") === `Bearer ${token}`) {
    // A pending request must not clear a newer session established by another tab.
    if (localStorage.getItem("access_token") === token) {
      localStorage.removeItem("access_token");
    }
    throw new Error("Your session has expired or is no longer valid. Please sign in again.");
  }
  if (!res.ok) {
    let message = `API error: ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") {
        message = data.detail;
      } else if (data?.detail) {
        message = JSON.stringify(data.detail);
      }
    } catch {
      // keep the status message
    }
    throw new Error(message);
  }
  return res.json();
}

export async function simulateCircuit(
  circuit: CircuitRequest
): Promise<CircuitResult> {
  return apiFetch("/api/circuits/simulate", {
    method: "POST",
    body: JSON.stringify(circuit),
  });
}
