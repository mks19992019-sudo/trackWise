const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ChatPayload {
  message: string;
  thread_id: string;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/`, {
      method: "GET",
      signal: AbortSignal.timeout(4000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function sendMessage(payload: ChatPayload): Promise<string> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Server error ${res.status}: ${text}`);
  }

  // Backend returns the raw string content of the last AI message
  const data = await res.json();
  // data could be a string directly or an object with content
  if (typeof data === "string") return data;
  if (typeof data === "object" && data !== null) {
    return data.content ?? data.response ?? data.message ?? JSON.stringify(data);
  }
  return String(data);
}
