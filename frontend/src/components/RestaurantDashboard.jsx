import { useEffect, useMemo, useState } from "react";
import {
    analyzeRestaurantMenu,
    confirmRestaurantMenu,
    createRestaurant,
    editRestaurantMenu,
    fetchRestaurantAnalytics,
    fetchRestaurantMenu,
    listRestaurants,
} from "../api";
import { prepareImageForUpload } from "../utils/image";
import AllergenMatrix from "./AllergenMatrix";
import MenuSafetyScore from "./MenuSafetyScore";
import QRCodeCard from "./QRCodeCard";
import RestaurantAnalytics from "./RestaurantAnalytics";
import logo from "../../logo.png";

const STORAGE_KEY = "medimenu_restaurant_id";

export default function RestaurantDashboard({ onLogout }) {
    /* ── state ──────────────────────────────────────── */
    const [restaurants, setRestaurants] = useState([]);
    const [selectedId, setSelectedId] = useState(localStorage.getItem(STORAGE_KEY) || "");
    const [newName, setNewName] = useState("");
    const [menu, setMenu] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    // Editable dish state (draft mode)
    const [editableDishes, setEditableDishes] = useState([]);
    const [editing, setEditing] = useState(false);

    const selectedRestaurant = useMemo(
        () => restaurants.find((r) => r.id === selectedId),
        [restaurants, selectedId],
    );

    /* ── load restaurants ───────────────────────────── */
    useEffect(() => {
        listRestaurants()
            .then(setRestaurants)
            .catch(() => { });
    }, []);

    /* ── load menu+analytics when restaurant selected ─ */
    useEffect(() => {
        if (!selectedId) {
            setMenu(null);
            setAnalytics(null);
            setEditableDishes([]);
            setEditing(false);
            return;
        }
        localStorage.setItem(STORAGE_KEY, selectedId);
        let cancelled = false;
        (async () => {
            try {
                const [m, a] = await Promise.allSettled([
                    fetchRestaurantMenu(selectedId),
                    fetchRestaurantAnalytics(selectedId),
                ]);
                if (cancelled) return;
                if (m.status === "fulfilled") {
                    setMenu(m.value);
                    setEditableDishes(m.value.dishes?.map(dishToEditable) || []);
                } else {
                    setMenu(null);
                    setEditableDishes([]);
                }
                if (a.status === "fulfilled") setAnalytics(a.value);
                else setAnalytics(null);
                setEditing(false);
            } catch {
                // ignore
            }
        })();
        return () => { cancelled = true; };
    }, [selectedId]);

    /* ── helpers ───────────────────────────────────── */
    function dishToEditable(dish) {
        return {
            dish: dish.dish,
            // Store as raw strings so the user can type freely (commas, spaces, etc.)
            ingredientsText: (dish.inferred_ingredients || []).join(", "),
            cross_contact_risk: dish.cross_contact_risk || false,
            allergensText: (dish.confirmed_allergens || []).join(", "),
        };
    }

    function editablesToPayload(editables) {
        return editables.map((d) => ({
            dish: d.dish,
            inferred_ingredients: d.ingredientsText.split(",").map(s => s.trim()).filter(Boolean),
            cross_contact_risk: d.cross_contact_risk,
            confirmed_allergens: d.allergensText.split(",").map(s => s.trim().toLowerCase()).filter(Boolean),
        }));
    }

    function updateEditableDish(index, field, value) {
        setEditableDishes((prev) => {
            const copy = [...prev];
            copy[index] = { ...copy[index], [field]: value };
            return copy;
        });
    }

    function addNewDish() {
        setEditableDishes((prev) => [
            ...prev,
            { dish: "", ingredientsText: "", cross_contact_risk: false, allergensText: "" },
        ]);
    }

    function removeDish(index) {
        setEditableDishes((prev) => prev.filter((_, i) => i !== index));
    }

    /* ── handlers ───────────────────────────────────── */
    async function handleCreateRestaurant(e) {
        e.preventDefault();
        if (!newName.trim()) return;
        setError("");
        try {
            const created = await createRestaurant(newName.trim());
            setRestaurants((prev) => [created, ...prev]);
            setSelectedId(created.id);
            setNewName("");
        } catch (err) {
            setError(err.message || "Failed to create restaurant.");
        }
    }

    async function handleUploadMenu() {
        if (!file || !selectedId) return;
        setLoading(true);
        setError("");
        try {
            const { base64, mimeType } = await prepareImageForUpload(file);
            const result = await analyzeRestaurantMenu(selectedId, base64, mimeType);
            setMenu(result);
            setEditableDishes(result.dishes?.map(dishToEditable) || []);
            setEditing(true); // Auto-enter edit mode after AI analysis
            setFile(null);
            const a = await fetchRestaurantAnalytics(selectedId);
            setAnalytics(a);
        } catch (err) {
            setError(err.message || "Menu analysis failed.");
        } finally {
            setLoading(false);
        }
    }

    async function handleSaveEdits() {
        if (!selectedId) return;
        setSaving(true);
        setError("");
        try {
            const result = await editRestaurantMenu(selectedId, editablesToPayload(editableDishes));
            setMenu(result);
            setEditableDishes(result.dishes?.map(dishToEditable) || []);
            setEditing(false);
        } catch (err) {
            setError(err.message || "Failed to save edits.");
        } finally {
            setSaving(false);
        }
    }

    async function handleConfirmMenu() {
        if (!selectedId) return;
        setConfirming(true);
        setError("");
        try {
            const result = await confirmRestaurantMenu(selectedId);
            setMenu(result);
            setEditing(false);
        } catch (err) {
            setError(err.message || "Failed to confirm menu.");
        } finally {
            setConfirming(false);
        }
    }

    /* ── render ─────────────────────────────────────── */
    return (
        <div className="app-shell">
            <header className="app-topbar dashboard-topbar">
                <div className="topbar-left">
                    <img src={logo} alt="MediMenu" className="topbar-logo-img" />
                    <span className="topbar-badge">Restaurant Dashboard</span>
                </div>
                <div className="topbar-right">
                    <button className="btn btn-ghost btn-sm" type="button" onClick={onLogout}>
                        Log Out
                    </button>
                </div>
            </header>

            {error && <p className="error global-error">{error}</p>}

            <div className="dashboard-layout">
                {/* ── Sidebar: restaurant list ─────────── */}
                <aside className="dashboard-sidebar">
                    <h3>Your Restaurants</h3>
                    <form onSubmit={handleCreateRestaurant} className="sidebar-form">
                        <input
                            type="text"
                            placeholder="Restaurant name..."
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            className="sidebar-input"
                        />
                        <button className="btn btn-primary btn-sm" type="submit">
                            + Add
                        </button>
                    </form>

                    <ul className="restaurant-list">
                        {restaurants.map((r) => (
                            <li key={r.id}>
                                <button
                                    type="button"
                                    className={`restaurant-item ${r.id === selectedId ? "active" : ""}`}
                                    onClick={() => setSelectedId(r.id)}
                                >
                                    <span className="restaurant-item-name">{r.name}</span>
                                    <span className="restaurant-item-date">
                                        {new Date(r.created_at).toLocaleDateString()}
                                    </span>
                                </button>
                            </li>
                        ))}
                        {restaurants.length === 0 && (
                            <li className="muted" style={{ padding: "1rem", textAlign: "center" }}>
                                No restaurants yet. Add one above.
                            </li>
                        )}
                    </ul>
                </aside>

                {/* ── Main content ─────────────────────── */}
                <main className="dashboard-main">
                    {!selectedId ? (
                        <div className="dashboard-empty">
                            <h2>Welcome to MediMenu for Restaurants</h2>
                            <p>Select a restaurant or create a new one to get started.</p>
                            <div className="dashboard-features">
                                <div className="feature-card">
                                    <span className="feature-icon">📋</span>
                                    <h4>Allergen Compliance</h4>
                                    <p>Auto-generated allergen matrix for every dish on your menu.</p>
                                </div>
                                <div className="feature-card">
                                    <span className="feature-icon">🛡️</span>
                                    <h4>Safety Score</h4>
                                    <p>Get a 0–100 safety rating to showcase to your customers.</p>
                                </div>
                                <div className="feature-card">
                                    <span className="feature-icon">📊</span>
                                    <h4>Diner Insights</h4>
                                    <p>See which allergens your diners flag most often.</p>
                                </div>
                                <div className="feature-card">
                                    <span className="feature-icon">📱</span>
                                    <h4>QR Code</h4>
                                    <p>Generate a QR code linking diners to your verified menu.</p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="dashboard-header">
                                <div className="dashboard-header-row">
                                    <h2>{selectedRestaurant?.name || "Restaurant"}</h2>
                                    {menu && (
                                        <span className={`status-badge ${menu.confirmed ? "status-confirmed" : "status-draft"}`}>
                                            {menu.confirmed ? "✓ Confirmed" : "Draft — review needed"}
                                        </span>
                                    )}
                                </div>
                                <div className="capture-bar">
                                    <label className="file-label">
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                                        />
                                    </label>
                                    <button
                                        className="btn btn-primary"
                                        type="button"
                                        disabled={loading || !file}
                                        onClick={handleUploadMenu}
                                    >
                                        {loading ? "Analyzing..." : "Upload & Analyze Menu"}
                                    </button>
                                </div>
                            </div>

                            {loading && (
                                <div className="loading-overlay">
                                    <div className="spinner" />
                                    <p className="loading-text">
                                        Analyzing menu for allergen compliance…
                                    </p>
                                </div>
                            )}

                            {/* QR Code */}
                            <div className="dashboard-stats-row">
                                <QRCodeCard
                                    restaurantId={selectedId}
                                    restaurantName={selectedRestaurant?.name}
                                    confirmed={menu?.confirmed}
                                />
                            </div>

                            {/* Editable Dish Review */}
                            {menu?.dishes && menu.dishes.length > 0 && (
                                <section className="dashboard-section">
                                    <div className="section-header-row">
                                        <h3>
                                            {editing ? "Review & Edit Ingredients" : "Dish Details"}
                                            <span className="section-subtitle">
                                                {editing ? "Edit ingredients and mark cross-contact risks" : ""}
                                            </span>
                                        </h3>
                                        <div className="section-actions">
                                            {!editing && !menu.confirmed && (
                                                <button
                                                    className="btn btn-ghost btn-sm"
                                                    type="button"
                                                    onClick={() => setEditing(true)}
                                                >
                                                    ✏️ Edit
                                                </button>
                                            )}
                                            {editing && (
                                                <>
                                                    <button
                                                        className="btn btn-ghost btn-sm"
                                                        type="button"
                                                        onClick={() => {
                                                            setEditing(false);
                                                            setEditableDishes(menu.dishes.map(dishToEditable));
                                                        }}
                                                    >
                                                        Cancel
                                                    </button>
                                                    <button
                                                        className="btn btn-primary btn-sm"
                                                        type="button"
                                                        disabled={saving}
                                                        onClick={handleSaveEdits}
                                                    >
                                                        {saving ? "Saving..." : "Save Changes"}
                                                    </button>
                                                </>
                                            )}
                                            {!editing && !menu.confirmed && (
                                                <button
                                                    className="btn btn-accent btn-sm"
                                                    type="button"
                                                    disabled={confirming}
                                                    onClick={handleConfirmMenu}
                                                >
                                                    {confirming ? "Confirming..." : "✓ Confirm & Publish"}
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    <div className="dish-grid">
                                        {(editing ? editableDishes : menu.dishes).map((dish, i) => (
                                            <div
                                                key={`dish-${i}`}
                                                className={`dish-card-mini ${editing ? "dish-editing" : ""}`}
                                            >
                                                <div className="dish-mini-header">
                                                    {editing ? (
                                                        <input
                                                            type="text"
                                                            value={dish.dish}
                                                            placeholder="Dish name"
                                                            onChange={(e) => updateEditableDish(i, "dish", e.target.value)}
                                                            className="dish-edit-input dish-name-input"
                                                            style={{ fontWeight: 700, fontSize: "1rem" }}
                                                        />
                                                    ) : (
                                                        <span className="dish-mini-name">{dish.dish}</span>
                                                    )}
                                                    {editing && (
                                                        <button
                                                            type="button"
                                                            className="btn-icon-remove"
                                                            title="Remove dish"
                                                            onClick={() => removeDish(i)}
                                                        >✕</button>
                                                    )}
                                                </div>

                                                {editing ? (
                                                    <div className="dish-edit-fields">
                                                        <div className="dish-edit-group">
                                                            <label>Ingredients (comma-separated)</label>
                                                            <input
                                                                type="text"
                                                                value={dish.ingredientsText}
                                                                onChange={(e) =>
                                                                    updateEditableDish(i, "ingredientsText", e.target.value)
                                                                }
                                                                className="dish-edit-input"
                                                            />
                                                        </div>
                                                        <div className="dish-edit-group">
                                                            <label>Confirmed Allergens (comma-separated)</label>
                                                            <input
                                                                type="text"
                                                                value={dish.allergensText}
                                                                placeholder="e.g. milk, peanuts"
                                                                onChange={(e) =>
                                                                    updateEditableDish(i, "allergensText", e.target.value)
                                                                }
                                                                className="dish-edit-input"
                                                            />
                                                        </div>
                                                        <label className="dish-edit-checkbox">
                                                            <input
                                                                type="checkbox"
                                                                checked={dish.cross_contact_risk}
                                                                onChange={(e) =>
                                                                    updateEditableDish(i, "cross_contact_risk", e.target.checked)
                                                                }
                                                            />
                                                            <span>⚠️ Cross-contact / shared equipment risk</span>
                                                        </label>
                                                    </div>
                                                ) : (
                                                    <>
                                                        {dish.inferred_ingredients?.length > 0 && (
                                                            <p className="dish-mini-ingredients">
                                                                {dish.inferred_ingredients.join(", ")}
                                                            </p>
                                                        )}
                                                        {dish.cross_contact_risk && (
                                                            <span className="cross-contact-badge">⚠️ Cross-contact risk</span>
                                                        )}
                                                        {dish.confirmed_allergens?.length > 0 && (
                                                            <span className="confirmed-allergens-badge">
                                                                🏷️ Confirmed: {dish.confirmed_allergens.join(", ")}
                                                            </span>
                                                        )}
                                                    </>
                                                )}
                                            </div>
                                        ))}
                                    </div>

                                    {editing && (
                                        <button
                                            type="button"
                                            className="btn btn-ghost btn-sm"
                                            style={{ marginTop: "1rem", width: "100%" }}
                                            onClick={addNewDish}
                                        >
                                            ➕ Add Dish
                                        </button>
                                    )}
                                </section>
                            )}

                            {/* Allergen Compliance Matrix — full width at bottom */}
                            {menu && (
                                <section className="dashboard-section allergen-matrix-section">
                                    <h3>
                                        Allergen Compliance Matrix
                                        <span className="section-subtitle">
                                            {menu.dishes?.length || 0} dishes analyzed
                                        </span>
                                    </h3>
                                    <div className="allergen-matrix-wrapper">
                                        <AllergenMatrix matrix={menu.allergen_matrix} />
                                    </div>
                                </section>
                            )}
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
