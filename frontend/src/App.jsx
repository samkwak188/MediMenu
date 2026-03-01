import { useEffect, useState } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import {
  createProfile,
  fetchPersonalizedMenu,
  fetchProfile,
} from "./api";
import AuthScreen from "./components/AuthScreen";
import ProfileForm from "./components/ProfileForm";
import QRScanner from "./components/QRScanner";
import RestaurantDashboard from "./components/RestaurantDashboard";
import logo from "../logo.png";

const STORAGE_KEY = "medimenu_profile_id";
const AUTH_KEY = "medimenu_user";

// Hackathon demo: clear all saved state on page load so every session starts fresh
localStorage.removeItem(STORAGE_KEY);
localStorage.removeItem(AUTH_KEY);
localStorage.removeItem("medimenu_restaurant_id");
localStorage.removeItem("medimenu_images");

/* ── Personalized Restaurant Menu View (QR scan) ── */
function PersonalizedView({ restaurantData, onBack }) {
  const [filter, setFilter] = useState(null); // null = show all, "green" | "yellow" | "red"

  if (!restaurantData) return null;

  const { restaurant_name, dishes, safety_score } = restaurantData;
  const counts = { green: 0, yellow: 0, red: 0 };
  dishes.forEach((d) => { if (counts[d.risk] !== undefined) counts[d.risk] += 1; });

  const filteredDishes = filter ? dishes.filter((d) => d.risk === filter) : dishes;
  const scoreColor = safety_score >= 70 ? "var(--ok)" : safety_score >= 40 ? "var(--warn)" : "var(--danger)";

  function toggleFilter(risk) {
    setFilter((prev) => (prev === risk ? null : risk));
  }

  return (
    <section className="unified-panel">
      <button
        className="btn btn-ghost btn-sm"
        type="button"
        onClick={onBack}
        style={{ marginBottom: "1rem" }}
      >
        ← Scan Another QR
      </button>

      <h2>{restaurant_name}</h2>

      {safety_score != null && (
        <div className="safety-score-banner">
          <div className="safety-score-circle" style={{ borderColor: scoreColor, color: scoreColor }}>
            {Math.round(safety_score)}
          </div>
          <div>
            <p style={{ fontWeight: 600, color: "var(--text-main)", margin: 0 }}>
              Menu Safety Score
            </p>
            <p className="muted" style={{ fontSize: "0.8rem" }}>
              Personalized for your dietary profile
            </p>
          </div>
        </div>
      )}

      <p className="muted" style={{ marginBottom: "1.5rem" }}>
        Menu personalized for your dietary profile
        {filter && <span style={{ fontWeight: 600, marginLeft: "0.5rem" }}>
          — showing {filter === "green" ? "OK" : filter === "yellow" ? "Caution" : "Avoid"} only
        </span>}
      </p>

      <div className="summary-grid">
        <button
          type="button"
          className={`summary summary-clickable ${filter === "green" ? "summary-active" : ""}`}
          style={{ borderColor: "var(--ok)" }}
          onClick={() => toggleFilter("green")}
        >
          <span className="summary-count" style={{ color: "var(--ok)" }}>{counts.green}</span>
          <span className="summary-label" style={{ color: "var(--ok)" }}>OK</span>
        </button>
        <button
          type="button"
          className={`summary summary-clickable ${filter === "yellow" ? "summary-active" : ""}`}
          style={{ borderColor: "var(--warn)" }}
          onClick={() => toggleFilter("yellow")}
        >
          <span className="summary-count" style={{ color: "var(--warn)" }}>{counts.yellow}</span>
          <span className="summary-label" style={{ color: "var(--warn)" }}>Caution</span>
        </button>
        <button
          type="button"
          className={`summary summary-clickable ${filter === "red" ? "summary-active" : ""}`}
          style={{ borderColor: "var(--danger)" }}
          onClick={() => toggleFilter("red")}
        >
          <span className="summary-count" style={{ color: "var(--danger)" }}>{counts.red}</span>
          <span className="summary-label" style={{ color: "var(--danger)" }}>Avoid</span>
        </button>
      </div>

      <div className="results-card-col">
        {filteredDishes.map((dish, i) => (
          <div key={`${dish.dish}-${i}`} className="dish-card-personalized">
            <div className="dish-header">
              <h3>{dish.dish}</h3>
              <span className={`badge badge-${dish.risk}`}>
                {dish.risk === "green" ? "✓ OK" : dish.risk === "yellow" ? "⚡ Caution" : "⚠️ Avoid"}
              </span>
            </div>
            {dish.inferred_ingredients?.length > 0 && (
              <div className="ingredient-list">
                <span className="ingredient-label">Ingredients: </span>
                {dish.inferred_ingredients.join(", ")}
              </div>
            )}
            {dish.cross_contact_risk && (
              <p className="cross-contact-inline">
                ⚠️ Cross-contact risk — shared cooking equipment
              </p>
            )}
            {dish.flags?.length > 0 && (
              <ul className="flag-list">
                {dish.flags.map((flag, fi) => (
                  <li key={fi}>
                    {flag.detail}
                    <span className="severity-tag">{flag.severity}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
        {filteredDishes.length === 0 && (
          <p className="muted" style={{ textAlign: "center", padding: "2rem" }}>
            No dishes in this category.
          </p>
        )}
      </div>
    </section>
  );
}

/* ── Consumer (B2C) view ─────────────────────────── */
function ConsumerApp({ user, onLogout }) {
  const [profileId, setProfileId] = useState(localStorage.getItem(STORAGE_KEY) || "");
  const [profile, setProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [error, setError] = useState("");

  // QR scan state
  const [scannedRestaurantId, setScannedRestaurantId] = useState(null);
  const [personalizedData, setPersonalizedData] = useState(null);
  const [loadingPersonalized, setLoadingPersonalized] = useState(false);

  // Load saved profile
  useEffect(() => {
    if (!profileId) return;
    let cancelled = false;
    (async () => {
      setError("");
      try {
        const p = await fetchProfile(profileId);
        if (!cancelled) setProfile(p);
      } catch (err) {
        if (!cancelled) {
          localStorage.removeItem(STORAGE_KEY);
          setProfileId("");
          setProfile(null);
          setError(err.message || "Could not load saved profile.");
        }
      }
    })();
    return () => { cancelled = true; };
  }, [profileId]);

  async function handleCreateProfile({ allergies, medications, dietaryRestrictions }) {
    setLoadingProfile(true);
    setError("");
    try {
      const created = await createProfile(allergies, medications, dietaryRestrictions);
      localStorage.setItem(STORAGE_KEY, created.id);
      setProfileId(created.id);
      setProfile(created);
    } finally {
      setLoadingProfile(false);
    }
  }

  async function handleQRScan(restaurantId) {
    if (!profileId) return;
    setScannedRestaurantId(restaurantId);
    setLoadingPersonalized(true);
    setError("");
    try {
      const data = await fetchPersonalizedMenu(restaurantId, profileId);
      setPersonalizedData(data);
    } catch (err) {
      setError(err.message || "Could not load restaurant menu.");
      setScannedRestaurantId(null);
    } finally {
      setLoadingPersonalized(false);
    }
  }

  function handleBackToScanner() {
    setScannedRestaurantId(null);
    setPersonalizedData(null);
    setError("");
  }

  function handleEditProfile() {
    setProfile(null);
    setProfileId("");
    localStorage.removeItem(STORAGE_KEY);
    setPersonalizedData(null);
    setScannedRestaurantId(null);
  }

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="topbar-left">
          <img src={logo} alt="MediMenu" className="topbar-logo-img" />
        </div>
        <div className="topbar-right">
          <span className="topbar-user">👤 {user.username}</span>
          <button className="btn btn-ghost btn-sm" type="button" onClick={onLogout}>
            Log Out
          </button>
        </div>
      </header>

      {error && <p className="error global-error">{error}</p>}

      {!profile ? (
        <ProfileForm onSave={handleCreateProfile} loading={loadingProfile} />
      ) : (
        <>
          <div className="profile-chip">
            <div className="profile-chip-content">
              <h3>Your Profile</h3>
              <p><strong>Allergies:</strong> {profile.allergies.length ? profile.allergies.join(", ") : "None"}</p>
              <p><strong>Medications:</strong> {profile.medications.length ? profile.medications.join(", ") : "None"}</p>
              {profile.dietary_restrictions?.length > 0 && (
                <p><strong>Diet:</strong> {profile.dietary_restrictions.join(", ")}</p>
              )}
            </div>
            <button className="btn btn-ghost btn-sm" type="button" onClick={handleEditProfile}>
              Edit Profile
            </button>
          </div>

          {/* Show QR Scanner or Personalized Results */}
          {!scannedRestaurantId ? (
            <QRScanner onScan={handleQRScan} loading={loadingPersonalized} />
          ) : (
            <>
              {loadingPersonalized ? (
                <div className="loading-overlay">
                  <div className="spinner" />
                  <p className="loading-text">Loading personalized menu…</p>
                </div>
              ) : personalizedData ? (
                <PersonalizedView
                  restaurantData={personalizedData}
                  onBack={handleBackToScanner}
                />
              ) : null}
            </>
          )}
        </>
      )}
    </div>
  );
}

/* ── Root App with routing ───────────────────────── */
export default function App() {
  const navigate = useNavigate();

  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(AUTH_KEY)); } catch { return null; }
  });

  function handleAuth(userData) {
    setUser(userData);
    localStorage.setItem(AUTH_KEY, JSON.stringify(userData));
    if (userData.role === "restaurant") {
      navigate("/dashboard");
    } else {
      navigate("/");
    }
  }

  function handleLogout() {
    setUser(null);
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(STORAGE_KEY);
    navigate("/");
  }

  if (!user) {
    return <AuthScreen onAuth={handleAuth} />;
  }

  return (
    <Routes>
      <Route
        path="/"
        element={<ConsumerApp user={user} onLogout={handleLogout} />}
      />
      <Route
        path="/dashboard"
        element={
          <RestaurantDashboard onLogout={handleLogout} />
        }
      />
    </Routes>
  );
}
