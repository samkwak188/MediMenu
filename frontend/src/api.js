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

// ── B2C Consumer API ───────────────────────────────

export async function createProfile(allergies, medications, dietaryRestrictions = []) {
  return request("/api/profile", {
    method: "POST",
    body: JSON.stringify({
      allergies,
      medications,
      dietary_restrictions: dietaryRestrictions,
    }),
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

// ── B2B Restaurant API ─────────────────────────────

export async function createRestaurant(name, location = "") {
  return request("/api/restaurant", {
    method: "POST",
    body: JSON.stringify({ name, location }),
  });
}

export async function listRestaurants() {
  return request("/api/restaurants");
}

export async function analyzeRestaurantMenu(restaurantId, imageBase64, mimeType) {
  return request(`/api/restaurant/${encodeURIComponent(restaurantId)}/menu`, {
    method: "POST",
    body: JSON.stringify({ image: imageBase64, mime_type: mimeType }),
  });
}

export async function fetchRestaurantMenu(restaurantId) {
  return request(`/api/restaurant/${encodeURIComponent(restaurantId)}/menu`);
}

export async function editRestaurantMenu(restaurantId, dishes) {
  return request(`/api/restaurant/${encodeURIComponent(restaurantId)}/menu`, {
    method: "PUT",
    body: JSON.stringify({ dishes }),
  });
}

export async function confirmRestaurantMenu(restaurantId) {
  return request(`/api/restaurant/${encodeURIComponent(restaurantId)}/menu/confirm`, {
    method: "POST",
  });
}

export async function fetchPersonalizedMenu(restaurantId, profileId) {
  return request(
    `/api/restaurant/${encodeURIComponent(restaurantId)}/menu/personalized?profile_id=${encodeURIComponent(profileId)}`
  );
}

export async function fetchRestaurantAnalytics(restaurantId) {
  return request(`/api/restaurant/${encodeURIComponent(restaurantId)}/analytics`);
}

// ── Meal Records API ───────────────────────────────

export async function createMealRecord(profileId, restaurantId, dishName, ingredients) {
  return request("/api/meal-record", {
    method: "POST",
    body: JSON.stringify({
      profile_id: profileId,
      restaurant_id: restaurantId,
      dish_name: dishName,
      ingredients,
    }),
  });
}

export async function fetchMealRecords(profileId) {
  return request(`/api/meal-records/${encodeURIComponent(profileId)}`);
}
