"use client";

import { useState, CSSProperties } from "react";
import { supabase } from "@/lib/supabase";

export default function DemoForm() {
  const [form, setForm] = useState({
    full_name: "",
    agency_name: "",
    email: "",
    phone: "",
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorText(null);
    setSuccess(false);

    const { error } = await supabase.from("demo_requests").insert([form]);

    setLoading(false);

    if (error) {
      setErrorText(error.message);
      return;
    }

    setSuccess(true);
    setForm({ full_name: "", agency_name: "", email: "", phone: "" });
  }

  return (
    <div style={s.card}>
      <h3 style={s.title}>Ücretsiz Demo Talebi</h3>

      <form onSubmit={handleSubmit} style={s.form}>
        <input name="full_name" placeholder="Ad Soyad" value={form.full_name} onChange={handleChange} required style={s.input} />
        <input name="agency_name" placeholder="Acente Adı" value={form.agency_name} onChange={handleChange} required style={s.input} />
        <input name="email" type="email" placeholder="E-posta" value={form.email} onChange={handleChange} required style={s.input} />
        <input name="phone" placeholder="Telefon" value={form.phone} onChange={handleChange} style={s.input} />

        {errorText && <div style={s.error}>❌ {errorText}</div>}
        {success && <div style={s.success}>✅ Demo talebiniz alındı</div>}

        <button disabled={loading} style={{ ...s.button, opacity: loading ? 0.7 : 1 }}>
          {loading ? "Gönderiliyor..." : "Demo Talep Et"}
        </button>

        <p style={s.trust}>Bilgileriniz gizlidir</p>
      </form>
    </div>
  );
}

const s: Record<string, CSSProperties> = {
  card: {
    background: "#fff",
    padding: 32,
    borderRadius: 24,
    boxShadow: "0 30px 60px rgba(0,0,0,0.12)",
    maxWidth: 420,
    width: "100%",
  },
  title: {
    fontSize: 22,
    fontWeight: 800,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 14,
    marginTop: 16,
  },
  input: {
    padding: "14px 16px",
    borderRadius: 14,
    border: "1px solid #e5e7eb",
    background: "#f8fafc",
    fontSize: 15,
  },
  button: {
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
    fontSize: 12,
    textAlign: "center",
    color: "#64748b",
  },
  error: {
    background: "#fee2e2",
    color: "#991b1b",
    padding: 12,
    borderRadius: 12,
  },
  success: {
    background: "#dcfce7",
    color: "#166534",
    padding: 12,
    borderRadius: 13,
  },
};
