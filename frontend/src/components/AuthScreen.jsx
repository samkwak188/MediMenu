import { useState } from "react";

export default function AuthScreen({ onAuth }) {
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
        });
    }

    return (
        <div className="auth-screen">
            <div className="auth-card">
                <div className="auth-logo">
                    <span className="auth-logo-icon">🍽️</span>
                    <h1>SafePlate</h1>
                </div>
                <p className="auth-subtitle">
                    AI-powered menu safety scanner for allergens &amp; medication interactions
                </p>

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
                            <label htmlFor="username">Username</label>
                            <input
                                id="username"
                                type="text"
                                placeholder="johndoe"
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
                    Demo mode — enter any credentials to continue
                </p>
            </div>
        </div>
    );
}
