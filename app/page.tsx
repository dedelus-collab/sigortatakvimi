"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";

export default function LandingPage() {
  const [form, setForm] = useState({
    full_name: "",
    agency_name: "",
    email: "",
    phone: "",
  });

  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorText(null);

    const { error } = await supabase.from("demo_requests").insert([form]);

    setLoading(false);

    if (error) {
      setErrorText(`${error.message} (${error.code})`);
      return;
    }

    alert("🎉 Demo talebiniz alındı");
    setForm({ full_name: "", agency_name: "", email: "", phone: "" });
  }

  return (
    <main style={s.body}>
      <section style={s.container}>
        {/* SOL TARAF */}
        <div style={s.left}>
          <span style={s.badge}>🚀 Sigorta Acenteleri İçin SaaS</span>

          <h1 style={s.title}>
            Poliçeleri
            <br />
            <span style={s.highlight}>Asla Unutmayın</span>
          </h1>

          <p style={s.subtitle}>
            SigortaTakvimi, acentelerin poliçe bitişlerini otomatik takip
            etmesini ve müşterilerle zamanında iletişime geçmesini sağlar.
          </p>

          {/* MOCK DASHBOARD */}
          <div style={s.dashboard}>
            <div style={s.dashboardCard}>
              📄 <strong>Aktif Poliçeler</strong>
              <p>142</p>
            </div>

            <div style={s.dashboardCard}>
              🔔 <strong>Yaklaşan Bitiş</strong>
              <p style={{ color: "#dc2626" }}>8</p>
            </div>

            <div style={s.dashboardCard}>
              💰 <strong>Yenilenen</strong>
              <p style={{ color: "#16a34a" }}>36</p>
            </div>
          </div>

          {/* FEATURE LIST */}
          <div style={s.features}>
            <div style={s.feature}>📅 Otomatik Poliçe Takibi</div>
            <div style={s.feature}>📞 Müşteri Hatırlatmaları</div>
            <div style={s.feature}>📊 Acente Performans Raporları</div>
            <div style={s.feature}>🔐 Güvenli Bulut Altyapısı</div>
          </div>
        </div>

        {/* SAĞ TARAF */}
        <div style={s.right}>
          <div style={s.card}>
            <h2 style={s.cardTitle}>Ücretsiz Demo Talebi</h2>

            <form onSubmit={handleSubmit} style={s.form}>
              <input
                name="full_name"
                placeholder="Ad Soyad"
                value={form.full_name}
                onChange={handleChange}
                required
                style={s.input}
              />

              <input
                name="agency_name"
                placeholder="Acente Adı"
                value={form.agency_name}
                onChange={handleChange}
                required
                style={s.input}
              />

              <input
                name="email"
                type="email"
                placeholder="E-posta"
                value={form.email}
                onChange={handleChange}
                required
                style={s.input}
              />

              <input
                name="phone"
                placeholder="Telefon"
                value={form.phone}
                onChange={handleChange}
                style={s.input}
              />

              {errorText && <div style={s.errorBox}>❌ {errorText}</div>}

              <button style={s.button} disabled={loading}>
                {loading ? "Gönderiliyor..." : "Demo Talep Et"}
              </button>

              <p style={s.trust}>🔒 Bilgileriniz gizlidir</p>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
}

/* ================= STYLES ================= */

const s: any = {
  body: {
    minHeight: "100vh",
    background: "linear-gradient(180deg,#f8fafc,#eef2ff)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },

  container: {
    maxWidth: 1100,
    width: "100%",
    display: "grid",
    gridTemplateColumns: "1.2fr 0.8fr",
    gap: 60,
  },

  left: {
    padding: 20,
  },

  badge: {
    display: "inline-block",
    background: "#e0e7ff",
    color: "#3730a3",
    padding: "6px 14px",
    borderRadius: 999,
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 16,
  },

  title: {
    fontSize: 42,
    fontWeight: 900,
    lineHeight: 1.15,
    marginBottom: 16,
  },

  highlight: {
    color: "#2563eb",
  },

  subtitle: {
    fontSize: 16,
    color: "#475569",
    maxWidth: 520,
    marginBottom: 28,
  },

  dashboard: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 16,
    marginBottom: 28,
  },

  dashboardCard: {
    background: "#ffffff",
    borderRadius: 18,
    padding: 20,
    boxShadow: "0 20px 40px rgba(0,0,0,0.1)",
    fontSize: 14,
  },

  features: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: 12,
  },

  feature: {
    background: "rgba(255,255,255,0.8)",
    padding: "12px 16px",
    borderRadius: 14,
    fontSize: 14,
    boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
  },

  right: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },

  card: {
    background: "#fff",
    padding: 32,
    borderRadius: 24,
    boxShadow: "0 30px 60px rgba(0,0,0,0.12)",
    width: "100%",
    maxWidth: 420,
  },

  cardTitle: {
    fontWeight: 800,
    marginBottom: 16,
  },

  form: {
    display: "flex",
    flexDirection: "column",
    gap: 14,
  },

  input: {
    padding: "14px 16px",
    borderRadius: 14,
    border: "1px solid #e5e7eb",
    background: "#f8fafc",
    fontSize: 15,
  },

  button: {
    marginTop: 8,
    padding: 14,
    borderRadius: 14,
    border: "none",
    fontWeight: 700,
    fontSize: 16,
    background: "linear-gradient(135deg,#2563eb,#1d4ed8)",
    color: "#fff",
    cursor: "pointer",
  },

  trust: {
    marginTop: 10,
    fontSize: 12,
    color: "#64748b",
    textAlign: "center",
  },

  errorBox: {
    background: "#fee2e2",
    color: "#991b1b",
    padding: 12,
    borderRadius: 12,
    fontSize: 14,
  },
};
