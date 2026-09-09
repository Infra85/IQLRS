export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Gate = {
  type: string;
  qubit?: number | null;
  control?: number | null;
  target?: number | null;
};

export type CircuitRequest = {
  gates: Gate[];
  num_qubits: number;
  shots?: number;
  backend?: string;
};

export type CircuitResult = {
  counts: Record<string, number>;
  statevector: number[][] | null;
  circuit_diagram: string | null;
};

export async function apiFetch(path: string, options?: RequestInit) {
  const { headers, ...rest } = options ?? {};
  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: { "Content-Type": "application/json", ...headers },
  });
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
