"use client";

const policies = [
  {
    customer: "Ahmet Yılmaz",
    type: "Kasko",
    date: "2025-02-10",
    color: "#2563eb",
  },
  {
    customer: "Mehmet Kaya",
    type: "Trafik",
    date: "2025-02-14",
    color: "#22c55e",
  },
  {
    customer: "Ayşe Demir",
    type: "DASK",
    date: "2025-02-20",
    color: "#f97316",
  },
];

export default function CalendarPage() {
  return (
    <div>
      <h1 style={s.title}>Sigorta Takvimi</h1>
      <p style={s.subtitle}>
        Yaklaşan poliçeleriniz
      </p>

      <div style={s.grid}>
        {policies.map((p, i) => (
          <div key={i} style={{ ...s.card, borderLeft: `6px solid ${p.color}` }}>
            <div style={s.date}>
              {new Date(p.date).toLocaleDateString("tr-TR")}
            </div>
            <div style={s.customer}>{p.customer}</div>
            <div style={s.type}>{p.type} Poliçesi</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const s: any = {
  title: {
    fontSize: 28,
    fontWeight: 800,
  },
  subtitle: {
    color: "#64748b",
    marginBottom: 24,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill,minmax(260px,1fr))",
    gap: 20,
  },
  card: {
    background: "#fff",
    padding: 20,
    borderRadius: 20,
    boxShadow: "0 10px 20px rgba(0,0,0,0.08)",
  },
  date: {
    fontSize: 13,
    color: "#64748b",
    marginBottom: 6,
  },
  customer: {
    fontSize: 18,
    fontWeight: 700,
  },
  type: {
    fontSize: 14,
    color: "#475569",
    marginTop: 4,
  },
};
