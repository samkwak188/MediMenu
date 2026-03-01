import { useState } from "react";
import logo from "../../logo.png";

export default function AuthScreen({ onAuth }) {
    const [role, setRole] = useState(""); // "" | "customer" | "restaurant"
    const [mode, setMode] = useState("signup"); // "signup" | "login"
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    function handleSubmit(e) {
        e.preventDefault();
        setError("");

        if (mode === "signup") {
            if (!username.trim() || !email.trim() || !password.trim()) {
                setError("Please fill in all fields.");
                return;
            }
        } else {
            if (!email.trim() || !password.trim()) {
                setError("Please fill in all fields.");
                return;
            }
        }

        // Demo auth — any input works
        onAuth({
            username: username.trim() || email.split("@")[0],
            email: email.trim(),
            role,
        });
    }

    // ── Step 1: Role Selection ─────────────────────
    if (!role) {
        return (
            <div className="auth-screen">
                <div className="auth-card auth-card-wide">
                    <div className="auth-logo">
                        <img src={logo} alt="MediMenu" className="auth-logo-img" />
                    </div>
                    <p className="auth-subtitle">
                        AI-powered food safety for allergens &amp; medication interactions
                    </p>

                    <div className="role-selector">
                        <button
                            type="button"
                            className="role-card"
                            onClick={() => setRole("customer")}
                        >
                            <span className="role-icon">👤</span>
                            <h3>I'm a Customer</h3>
                            <p>Scan a restaurant's QR code to check food safety based on your allergies, medications, and dietary restrictions</p>
                        </button>

                        <button
                            type="button"
                            className="role-card"
                            onClick={() => setRole("restaurant")}
                        >
                            <span className="role-icon">🏪</span>
                            <h3>I'm a Restaurant Owner</h3>
                            <p>Upload your menu, manage allergen compliance, and generate QR codes for diners</p>
                        </button>
                    </div>

                    <p className="auth-hint">
                        MediMenu @ CheeseHack 2026
                    </p>
                </div>
            </div>
        );
    }

    // ── Step 2: Login / Signup Form ────────────────
    return (
        <div className="auth-screen">
            <div className="auth-card">
                <div className="auth-logo">
                    <img src={logo} alt="MediMenu" className="auth-logo-img" />
                </div>
                <p className="auth-subtitle">
                    {role === "customer"
                        ? "Sign in to scan menus & check food safety"
                        : "Sign in to manage your restaurant dashboard"}
                </p>

                <div className="auth-role-indicator">
                    <span className="role-indicator-icon">
                        {role === "customer" ? "👤" : "🏪"}
                    </span>
                    <span>{role === "customer" ? "Customer" : "Restaurant Owner"}</span>
                    <button
                        type="button"
                        className="btn btn-ghost btn-xs"
                        onClick={() => { setRole(""); setError(""); }}
                    >
                        Switch
                    </button>
                </div>

                <div className="auth-tabs">
                    <button
                        type="button"
                        className={`auth-tab ${mode === "signup" ? "active" : ""}`}
                        onClick={() => { setMode("signup"); setError(""); }}
                    >
                        Sign Up
                    </button>
                    <button
                        type="button"
                        className={`auth-tab ${mode === "login" ? "active" : ""}`}
                        onClick={() => { setMode("login"); setError(""); }}
                    >
                        Log In
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    {mode === "signup" && (
                        <div className="form-group">
                            <label htmlFor="username">
                                {role === "customer" ? "Username" : "Restaurant Name"}
                            </label>
                            <input
                                id="username"
                                type="text"
                                placeholder={role === "customer" ? "johndoe" : "Seoul Kitchen"}
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                autoComplete="username"
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete={mode === "signup" ? "new-password" : "current-password"}
                        />
                    </div>

                    {error && <p className="error">{error}</p>}

                    <button className="btn btn-primary btn-large" type="submit" style={{ width: "100%" }}>
                        {mode === "signup" ? "Create Account" : "Log In"}
                    </button>
                </form>

                <p className="auth-hint">
                    MediMenu @ CheeseHack 2026
                </p>
            </div>
        </div>
    );
}
