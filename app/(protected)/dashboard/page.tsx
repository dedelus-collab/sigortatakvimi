"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

type Policy = {
  id: number;
  customer: string;
  phone: string;
  company: string;
  type: string;
  end_date: string;
};

export default function DashboardPage() {
  const [expiring, setExpiring] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExpiring();
  }, []);

  async function fetchExpiring() {
    const today = new Date();
    const next7 = new Date();
    next7.setDate(today.getDate() + 7);

    const { data, error } = await supabase
      .from("policies")
      .select("*")
      .gte("end_date", today.toISOString().split("T")[0])
      .lte("end_date", next7.toISOString().split("T")[0])
      .order("end_date", { ascending: true });

    if (!error) {
      setExpiring(data || []);
    } else {
      console.error(error);
    }

    setLoading(false);
  }

  return (
    <div>
      <h1 style={s.title}>Dashboard</h1>

      <div style={s.card}>
        <h2 style={s.cardTitle}>⏰ Bitmek Üzere Olan Poliçeler</h2>

        {loading ? (
          <p>Yükleniyor...</p>
        ) : expiring.length === 0 ? (
          <p style={s.ok}>Yaklaşan poliçe yok 🎉</p>
        ) : (
          <div style={s.list}>
            {expiring.map((p) => (
              <div key={p.id} style={s.item}>
                <div>
                  <strong>{p.customer}</strong>
                  <div style={s.muted}>{p.phone}</div>
                </div>

                <div>{p.company}</div>
                <div>{p.type}</div>

                <div style={s.badge}>
                  {p.end_date}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const s: any = {
  title: {
    fontSize: 30,
    fontWeight: 800,
    marginBottom: 24,
  },
  card: {
    background: "#fff",
    borderRadius: 20,
    padding: 24,
    boxShadow: "0 20px 40px rgba(0,0,0,0.08)",
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 16,
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: 14,
  },
  item: {
    display: "grid",
    gridTemplateColumns: "2fr 2fr 1fr 1fr",
    gap: 12,
    padding: 14,
    borderRadius: 14,
    background: "#fff7ed",
    alignItems: "center",
  },
  badge: {
    background: "#ef4444",
    color: "#fff",
    padding: "6px 10px",
    borderRadius: 999,
    fontSize: 13,
    fontWeight: 700,
    textAlign: "center",
  },
  muted: {
    fontSize: 13,
    color: "#64748b",
  },
  ok: {
    color: "#16a34a",
    fontWeight: 600,
  },
};
