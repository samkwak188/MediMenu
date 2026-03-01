import { useEffect, useState } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import { jsPDF } from "jspdf";
import {
  createMealRecord,
  createProfile,
  fetchMealRecords,
  fetchPersonalizedMenu,
  fetchProfile,
} from "./api";
import AuthScreen from "./components/AuthScreen";
import ProfileForm from "./components/ProfileForm";
import QRScanner from "./components/QRScanner";
import RestaurantDashboard from "./components/RestaurantDashboard";
import logo from "../logo.png";

function loadImageAsBase64(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      canvas.getContext("2d").drawImage(img, 0, 0);
      resolve(canvas.toDataURL("image/png"));
    };
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

async function generateMealHistoryPDF(records, logoSrc) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const margin = 18;
  const contentW = pageW - margin * 2;
  let y = margin;

  const brandColor = [59, 130, 246];
  const textDark = [15, 23, 42];
  const textMuted = [100, 116, 139];
  const lineSoft = [226, 232, 240];

  const logoBase64 = await loadImageAsBase64(logoSrc);

  function addHeader() {
    if (logoBase64) {
      const logoH = 12;
      const logoW = logoH * 3.2;
      doc.addImage(logoBase64, "PNG", margin, y, logoW, logoH);
      y += logoH + 2;
    } else {
      doc.setFont("helvetica", "bold");
      doc.setFontSize(20);
      doc.setTextColor(...brandColor);
      doc.text("MediMenu", margin, y + 7);
      y += 12;
    }
    doc.setDrawColor(...brandColor);
    doc.setLineWidth(0.6);
    doc.line(margin, y, pageW - margin, y);
    y += 8;
  }

  function checkPageBreak(needed) {
    if (y + needed > pageH - margin) {
      doc.addPage();
      y = margin;
      addHeader();
    }
  }

  addHeader();

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.setTextColor(...textDark);
  doc.text("Meal History Report", margin, y);
  y += 7;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...textMuted);
  doc.text(`Generated on ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}`, margin, y);
  y += 4;
  doc.text(`${records.length} meal${records.length !== 1 ? "s" : ""} recorded`, margin, y);
  y += 10;

  if (records.length === 0) {
    doc.setFont("helvetica", "italic");
    doc.setFontSize(11);
    doc.setTextColor(...textMuted);
    doc.text("No meals recorded yet.", margin, y);
  } else {
    records.forEach((rec, idx) => {
      const ingredientText = rec.ingredients?.length
        ? rec.ingredients.join(", ")
        : "Not available";
      const ingredientLines = doc.splitTextToSize(`Ingredients: ${ingredientText}`, contentW - 10);
      const cardH = 24 + ingredientLines.length * 4;

      checkPageBreak(cardH + 4);

      doc.setFillColor(248, 250, 252);
      doc.setDrawColor(...lineSoft);
      doc.roundedRect(margin, y, contentW, cardH, 3, 3, "FD");

      const innerX = margin + 5;
      let cy = y + 6;

      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(...textDark);
      doc.text(rec.dish_name, innerX, cy);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(8.5);
      doc.setTextColor(...textMuted);
      doc.text(rec.date, pageW - margin - 5, cy, { align: "right" });

      cy += 5.5;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(...brandColor);
      const restaurantLine = rec.restaurant_location
        ? `${rec.restaurant_name} — ${rec.restaurant_location}`
        : rec.restaurant_name;
      doc.text(restaurantLine, innerX, cy);

      cy += 5.5;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8.5);
      doc.setTextColor(...textMuted);
      doc.text(ingredientLines, innerX, cy);

      y += cardH + 3;
    });
  }

  // Footer on every page
  const totalPages = doc.internal.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7.5);
    doc.setTextColor(...textMuted);
    doc.text(
      `MediMenu — AI-powered food safety for allergens & medication interactions`,
      pageW / 2,
      pageH - 8,
      { align: "center" }
    );
    doc.text(`Page ${p} of ${totalPages}`, pageW - margin, pageH - 8, { align: "right" });
  }

  doc.save("MediMenu_Meal_History.pdf");
}

const STORAGE_KEY = "medimenu_profile_id";
const AUTH_KEY = "medimenu_user";

// Hackathon demo: clear all saved state on page load so every session starts fresh
localStorage.removeItem(STORAGE_KEY);
localStorage.removeItem(AUTH_KEY);
localStorage.removeItem("medimenu_restaurant_id");
localStorage.removeItem("medimenu_images");

/* ── Personalized Restaurant Menu View (QR scan) ── */
function PersonalizedView({ restaurantData, onBack, onRecordMeal }) {
  const [filter, setFilter] = useState(null); // null = show all, "green" | "yellow" | "red"
  const [recorded, setRecorded] = useState({});

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
            <button
              className={`btn btn-sm ${recorded[i] ? "btn-ghost" : "btn-accent"}`}
              type="button"
              disabled={!!recorded[i]}
              style={{ marginTop: "0.75rem" }}
              onClick={async () => {
                await onRecordMeal(dish.dish, dish.inferred_ingredients || []);
                setRecorded((prev) => ({ ...prev, [i]: true }));
              }}
            >
              {recorded[i] ? "Recorded ✓" : "I ate this"}
            </button>
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

  // Meal records state
  const [mealRecords, setMealRecords] = useState([]);
  const [showMealHistory, setShowMealHistory] = useState(false);

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

  useEffect(() => {
    if (!profileId) return;
    let cancelled = false;
    (async () => {
      try {
        const records = await fetchMealRecords(profileId);
        if (!cancelled) setMealRecords(records);
      } catch {
        // ignore — records just won't load
      }
    })();
    return () => { cancelled = true; };
  }, [profileId]);

  async function handleRecordMeal(dishName, ingredients) {
    if (!profileId || !scannedRestaurantId) return;
    try {
      const record = await createMealRecord(profileId, scannedRestaurantId, dishName, ingredients);
      setMealRecords((prev) => [record, ...prev]);
    } catch (err) {
      setError(err.message || "Failed to record meal.");
    }
  }

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
    setMealRecords([]);
    setShowMealHistory(false);
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
                  onRecordMeal={handleRecordMeal}
                />
              ) : null}
            </>
          )}

          {/* Meal History */}
          <section className="meal-history-section">
            <div className="meal-history-header">
              <button
                className="btn btn-ghost meal-history-toggle"
                type="button"
                onClick={() => setShowMealHistory((v) => !v)}
              >
                {showMealHistory ? "▼" : "▶"} My Meal History ({mealRecords.length})
              </button>
              {mealRecords.length > 0 && (
                <button
                  className="btn btn-accent btn-sm"
                  type="button"
                  onClick={() => generateMealHistoryPDF(mealRecords, logo)}
                >
                  ↓ Download PDF
                </button>
              )}
            </div>
            {showMealHistory && (
              <div className="meal-history-list">
                {mealRecords.length === 0 ? (
                  <p className="muted" style={{ textAlign: "center", padding: "1.5rem" }}>
                    No meals recorded yet. Scan a QR code and tap "I ate this" to start tracking.
                  </p>
                ) : (
                  mealRecords.map((rec) => (
                    <div key={rec.id} className="meal-record-card">
                      <div className="meal-record-header">
                        <h4>{rec.dish_name}</h4>
                        <span className="meal-record-date">{rec.date}</span>
                      </div>
                      <p className="meal-record-restaurant">
                        {rec.restaurant_name}
                        {rec.restaurant_location ? ` — ${rec.restaurant_location}` : ""}
                      </p>
                      {rec.ingredients?.length > 0 && (
                        <p className="meal-record-ingredients">
                          <span className="ingredient-label">Ingredients: </span>
                          {rec.ingredients.join(", ")}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </section>
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
