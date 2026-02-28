import { useEffect, useState } from "react";
import { analyzeMenu, createProfile, fetchHistory, fetchProfile } from "./api";
import AuthScreen from "./components/AuthScreen";
import HistoryPanel from "./components/HistoryPanel";
import ProfileForm from "./components/ProfileForm";
import ResultsView from "./components/ResultsView";

const STORAGE_KEY = "safeplate_profile_id";
const IMAGE_CACHE_KEY = "safeplate_images";
const AUTH_KEY = "safeplate_user";
const MAX_CACHED_IMAGES = 10;

function loadImageCache() {
  try { return JSON.parse(localStorage.getItem(IMAGE_CACHE_KEY) || "{}"); } catch { return {}; }
}

function saveImageCache(cache) {
  const keys = Object.keys(cache);
  if (keys.length > MAX_CACHED_IMAGES) {
    keys.slice(0, keys.length - MAX_CACHED_IMAGES).forEach((k) => delete cache[k]);
  }
  try { localStorage.setItem(IMAGE_CACHE_KEY, JSON.stringify(cache)); } catch { /* ignore */ }
}

export default function App() {
  // Auth state
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(AUTH_KEY)); } catch { return null; }
  });

  // Profile state
  const [profileId, setProfileId] = useState(localStorage.getItem(STORAGE_KEY) || "");
  const [profile, setProfile] = useState(null);

  // Analysis state
  const [history, setHistory] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [analysisImages, setAnalysisImages] = useState(loadImageCache);
  const [activeImageSrc, setActiveImageSrc] = useState("");
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState("");

  // Load profile + history when profileId changes
  useEffect(() => {
    if (!profileId) return;
    let cancelled = false;
    (async () => {
      setError("");
      try {
        const [p, h] = await Promise.all([fetchProfile(profileId), fetchHistory(profileId)]);
        if (cancelled) return;
        setProfile(p);
        setHistory(h.analyses || []);
      } catch (err) {
        if (!cancelled) {
          localStorage.removeItem(STORAGE_KEY);
          setProfileId("");
          setProfile(null);
          setHistory([]);
          setError(err.message || "Could not load saved profile.");
        }
      }
    })();
    return () => { cancelled = true; };
  }, [profileId]);

  /* ── handlers ──────────────────────────────────── */

  function handleAuth(userData) {
    setUser(userData);
    localStorage.setItem(AUTH_KEY, JSON.stringify(userData));
  }

  function handleLogout() {
    setUser(null);
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(IMAGE_CACHE_KEY);
    setProfileId("");
    setProfile(null);
    setHistory([]);
    setCurrentAnalysis(null);
    setActiveImageSrc("");
    setError("");
  }

  async function handleCreateProfile({ allergies, medications }) {
    setLoadingProfile(true);
    setError("");
    try {
      const created = await createProfile(allergies, medications);
      localStorage.setItem(STORAGE_KEY, created.id);
      setProfileId(created.id);
      setProfile(created);
      setHistory([]);
      setCurrentAnalysis(null);
    } finally {
      setLoadingProfile(false);
    }
  }

  async function handleAnalyze({ base64, mimeType, imageDataUrl }) {
    if (!profileId) throw new Error("Create a profile first.");
    setLoadingAnalysis(true);
    setError("");
    try {
      const analysis = await analyzeMenu(profileId, base64, mimeType);
      setCurrentAnalysis(analysis);
      setActiveImageSrc(imageDataUrl || "");

      const updatedCache = { ...analysisImages, [analysis.analysis_id]: imageDataUrl || "" };
      setAnalysisImages(updatedCache);
      saveImageCache(updatedCache);

      const histData = await fetchHistory(profileId);
      setHistory(histData.analyses || []);
    } catch (err) {
      setError(err.message || "Analysis failed.");
      throw err;
    } finally {
      setLoadingAnalysis(false);
    }
  }

  function handleSelectHistory(entry) {
    setCurrentAnalysis(entry);
    setActiveImageSrc(analysisImages[entry.analysis_id] || "");
  }

  function handleEditProfile() {
    setProfile(null);
    setProfileId("");
    localStorage.removeItem(STORAGE_KEY);
    setCurrentAnalysis(null);
    setHistory([]);
  }

  /* ── render ────────────────────────────────────── */

  // Step 1: Auth screen
  if (!user) {
    return <AuthScreen onAuth={handleAuth} />;
  }

  // Step 2: Profile setup (if no profile yet)
  // Step 3: Scanner + Results (if profile exists)
  return (
    <div className="app-shell">
      {/* Top bar */}
      <header className="app-topbar">
        <div className="topbar-left">
          <span className="topbar-logo">🍽️ SafePlate</span>
        </div>
        <div className="topbar-right">
          <span className="topbar-user">👤 {user.username}</span>
          <button className="btn btn-ghost btn-sm" type="button" onClick={handleLogout}>
            Log Out
          </button>
        </div>
      </header>

      {error && <p className="error global-error">{error}</p>}

      {!profile ? (
        /* Step 2: Profile preferences */
        <ProfileForm onSave={handleCreateProfile} loading={loadingProfile} />
      ) : (
        /* Step 3: Scanner app */
        <>
          <div className="profile-chip">
            <div className="profile-chip-content">
              <h3>Your Profile</h3>
              <p><strong>Allergies:</strong> {profile.allergies.length ? profile.allergies.join(", ") : "None"}</p>
              <p><strong>Medications:</strong> {profile.medications.length ? profile.medications.join(", ") : "None"}</p>
            </div>
            <button className="btn btn-ghost btn-sm" type="button" onClick={handleEditProfile}>
              Edit Profile
            </button>
          </div>

          <ResultsView
            analysis={currentAnalysis}
            imageSrc={activeImageSrc}
            onAnalyze={handleAnalyze}
            loading={loadingAnalysis}
          />

          {history.length > 0 && <HistoryPanel analyses={history} onSelect={handleSelectHistory} />}
        </>
      )}
    </div>
  );
}
