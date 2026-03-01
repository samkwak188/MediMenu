import { Html5Qrcode } from "html5-qrcode";
import { useRef, useState } from "react";

export default function QRScanner({ onScan, loading }) {
    const [scanning, setScanning] = useState(false);
    const [error, setError] = useState("");
    const scannerRef = useRef(null);
    const fileInputRef = useRef(null);

    function extractRestaurantId(text) {
        // Try to extract restaurant ID from URL like "http://localhost:5173/?restaurant=UUID"
        try {
            const url = new URL(text);
            const id = url.searchParams.get("restaurant");
            if (id) return id;
        } catch {
            // not a URL
        }
        // If it's a raw UUID, use directly
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        if (uuidRegex.test(text.trim())) return text.trim();
        return null;
    }

    async function handleFileUpload(e) {
        const file = e.target.files?.[0];
        if (!file) return;

        setError("");
        setScanning(true);

        try {
            const scanner = new Html5Qrcode("qr-reader-hidden");
            scannerRef.current = scanner;
            const result = await scanner.scanFile(file, true);
            const restaurantId = extractRestaurantId(result);
            if (restaurantId) {
                onScan(restaurantId);
            } else {
                setError("This QR code doesn't contain a valid SafePlate restaurant link.");
            }
            await scanner.clear();
        } catch {
            setError("Could not read QR code from this image. Please try again.");
        } finally {
            setScanning(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    }

    async function handleCameraScan() {
        setError("");
        setScanning(true);

        try {
            const scanner = new Html5Qrcode("qr-camera-view");
            scannerRef.current = scanner;

            await scanner.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: { width: 250, height: 250 } },
                (decodedText) => {
                    const restaurantId = extractRestaurantId(decodedText);
                    if (restaurantId) {
                        scanner.stop().then(() => scanner.clear());
                        setScanning(false);
                        onScan(restaurantId);
                    }
                },
                () => { /* ignore scan errors */ }
            );
        } catch {
            setError("Camera access denied or unavailable. Try uploading a QR image instead.");
            setScanning(false);
        }
    }

    function handleStopCamera() {
        if (scannerRef.current) {
            scannerRef.current.stop().then(() => {
                scannerRef.current.clear();
                setScanning(false);
            }).catch(() => setScanning(false));
        }
    }

    return (
        <section className="qr-scanner-section">
            <div className="qr-scanner-card">
                <div className="qr-scanner-header">
                    <span className="qr-scanner-icon">📱</span>
                    <h2>Scan Restaurant QR Code</h2>
                    <p className="muted">
                        Scan the QR code at the restaurant to see which dishes are right for you
                    </p>
                </div>

                <div className="qr-scanner-actions">
                    {/* Upload QR image */}
                    <label className="qr-upload-btn">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleFileUpload}
                            style={{ display: "none" }}
                        />
                        <span className="btn btn-primary btn-large">
                            {scanning ? "Reading QR..." : "📷 Upload QR Code Image"}
                        </span>
                    </label>

                    {/* Camera scan */}
                    {!scanning ? (
                        <button
                            className="btn btn-ghost btn-large"
                            type="button"
                            onClick={handleCameraScan}
                        >
                            🎥 Use Camera to Scan
                        </button>
                    ) : (
                        <button
                            className="btn btn-ghost btn-large"
                            type="button"
                            onClick={handleStopCamera}
                        >
                            ✕ Stop Camera
                        </button>
                    )}
                </div>

                {error && <p className="error" style={{ marginTop: "1rem" }}>{error}</p>}
                {loading && (
                    <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
                        <div className="spinner" />
                        <p className="loading-text">Loading personalized menu…</p>
                    </div>
                )}

                {/* Hidden element for file-based scanning */}
                <div id="qr-reader-hidden" style={{ display: "none" }} />

                {/* Camera view */}
                <div
                    id="qr-camera-view"
                    style={{
                        marginTop: scanning ? "1.5rem" : 0,
                        borderRadius: "var(--radius-md)",
                        overflow: "hidden",
                    }}
                />
            </div>
        </section>
    );
}
