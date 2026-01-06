"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

type Policy = {
  id: number;
  customer: string;
  phone: string;
  company: string;
  type: string;
  start_date: string;
  end_date: string;
};

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicies();
  }, []);

  async function fetchPolicies() {
    const { data, error } = await supabase
      .from("policies")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) {
      console.error(error);
      alert("Poliçeler alınamadı");
    } else {
      setPolicies(data || []);
    }
    setLoading(false);
  }

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 16 }}>
        Poliçeler
      </h1>

      <Link href="/policies/new">
        <button
          style={{
            marginBottom: 20,
            background: "#2563eb",
            color: "#fff",
            padding: "10px 16px",
            borderRadius: 12,
            fontWeight: 700,
            border: "none",
            cursor: "pointer",
          }}
        >
          + Yeni Poliçe
        </button>
      </Link>

      <div
        style={{
          background: "#fff",
          padding: 20,
          borderRadius: 16,
          boxShadow: "0 10px 20px rgba(0,0,0,0.08)",
        }}
      >
        {loading ? (
          <p>Yükleniyor...</p>
        ) : policies.length === 0 ? (
          <p>Henüz poliçe yok</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {policies.map((p) => (
              <div
                key={p.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "2fr 2fr 1fr 2fr",
                  gap: 12,
                  padding: 14,
                  borderRadius: 12,
                  background: "#f8fafc",
                }}
              >
                <div>
                  <strong>{p.customer}</strong>
                  <div style={{ fontSize: 13, color: "#64748b" }}>
                    {p.phone}
                  </div>
                </div>

                <div>{p.company}</div>
                <div>{p.type}</div>
                <div style={{ fontSize: 14 }}>
                  {p.start_date} → {p.end_date}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
