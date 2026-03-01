const STATUS_ICON = {
    safe: "✅",
    warning: "⚠️",
    danger: "❌",
};

const STATUS_CLASS = {
    safe: "matrix-safe",
    warning: "matrix-warning",
    danger: "matrix-danger",
};

export default function AllergenMatrix({ matrix }) {
    if (!matrix || Object.keys(matrix).length === 0) {
        return <p className="muted">No allergen data yet. Upload a menu to generate the compliance matrix.</p>;
    }

    const dishes = Object.keys(matrix);
    const allergens = [
        "milk", "eggs", "fish", "shellfish", "tree nuts",
        "peanuts", "wheat", "soybeans", "sesame", "gluten",
        "mustard", "celery", "lupin", "mollusks",
    ];

    return (
        <div className="matrix-wrapper">
            <div className="matrix-scroll">
                <table className="allergen-matrix">
                    <thead>
                        <tr>
                            <th className="matrix-dish-header">Dish</th>
                            {allergens.map((a) => (
                                <th key={a} className="matrix-allergen-header">
                                    <span className="matrix-allergen-label">{a}</span>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {dishes.map((dish) => (
                            <tr key={dish}>
                                <td className="matrix-dish-name">{dish}</td>
                                {allergens.map((a) => {
                                    const status = matrix[dish]?.[a] || "safe";
                                    return (
                                        <td key={a} className={`matrix-cell ${STATUS_CLASS[status]}`}>
                                            <span title={`${dish} — ${a}: ${status}`}>
                                                {STATUS_ICON[status]}
                                            </span>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
