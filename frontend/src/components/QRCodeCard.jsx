import { QRCodeSVG } from "qrcode.react";

export default function QRCodeCard({ restaurantId, restaurantName, confirmed }) {
    if (!restaurantId) return null;

    const scanUrl = `${window.location.origin}/?restaurant=${restaurantId}`;

    return (
        <div className="qr-card">
            <h3>QR Code for Diners</h3>
            {confirmed ? (
                <>
                    <p className="qr-description">
                        Print and display this QR code. Customers scan it to check your confirmed
                        menu against their dietary restrictions.
                    </p>
                    <div className="qr-code-container">
                        <QRCodeSVG
                            value={scanUrl}
                            size={180}
                            level="H"
                            includeMargin
                            bgColor="transparent"
                            fgColor="var(--clr-text, #1a1a2e)"
                        />
                    </div>
                    <div className="qr-badge">
                        <span className="qr-badge-icon">🍽️</span>
                        <span className="qr-badge-text">Powered by SafePlate</span>
                    </div>
                    <p className="qr-url-preview">{scanUrl}</p>
                </>
            ) : (
                <div className="qr-inactive">
                    <p className="qr-description">
                        Confirm your menu to activate the QR code.
                        Diners can only scan confirmed menus.
                    </p>
                    <div className="qr-placeholder">
                        <span>📱</span>
                        <span>QR code will appear here</span>
                    </div>
                </div>
            )}
        </div>
    );
}
