const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const raw = await response.text();
  let data = {};
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: raw };
    }
  }

  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Request failed.";
    throw new Error(detail);
  }

  return data;
}

export async function createProfile(allergies, medications) {
  return request("/api/profile", {
    method: "POST",
    body: JSON.stringify({ allergies, medications }),
  });
}

export async function fetchProfile(profileId) {
  return request(`/api/profile/${encodeURIComponent(profileId)}`);
}

export async function analyzeMenu(profileId, imageBase64, mimeType) {
  return request("/api/analyze", {
    method: "POST",
    body: JSON.stringify({
      profile_id: profileId,
      image: imageBase64,
      mime_type: mimeType,
    }),
  });
}

export async function fetchHistory(profileId) {
  return request(`/api/history/${encodeURIComponent(profileId)}`);
}
