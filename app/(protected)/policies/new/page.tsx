"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../../../lib/supabase";

export default function NewPolicyPage() {
  const router = useRouter();

  const [form, setForm] = useState({
    customer_name: "",
    phone: "",
    company: "",
    policy_type: "Kasko",
    start: "",
    end: "",
  });

  function handleChange(e: any) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: any) {
    e.preventDefault();

    const { data } = await supabase.auth.getUser();
    if (!data.user) {
      alert("Giriş yapmalısınız");
      return;
    }

    const { error } = await supabase.from("policies").insert([
      {
        customer_name: form.customer_name,
        phone: form.phone,
        company: form.company,
        policy_type: form.policy_type, // ✅ DB ile uyumlu
        start_date: form.start,
        end_date: form.end,
        user_id: data.user.id,
      },
    ]);

    if (error) {
      alert(error.message);
      return;
    }

    router.push("/policies");
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <h1 style={s.title}>Yeni Poliçe</h1>
        <p style={s.subtitle}>Poliçe bilgilerini girin</p>

        <form onSubmit={handleSubmit} style={s.form}>
          <input
            name="customer_name"
            placeholder="Müşteri Adı"
            onChange={handleChange}
            style={s.input}
            required
          />

          <input
            name="phone"
            placeholder="Telefon"
            onChange={handleChange}
            style={s.input}
            required
          />

          <input
            name="company"
            placeholder="Sigorta Şirketi"
            onChange={handleChange}
            style={s.input}
            required
          />

          <select
            name="policy_type"
            onChange={handleChange}
            style={s.input}
          >
            <option>Kasko</option>
            <option>Trafik</option>
            <option>DASK</option>
            <option>Sağlık</option>
          </select>

          <div style={s.row}>
            <input
              type="date"
              name="start"
              onChange={handleChange}
              style={s.input}
              required
            />
            <input
              type="date"
              name="end"
              onChange={handleChange}
              style={s.input}
              required
            />
          </div>

          <button style={s.button}>Kaydet</button>
        </form>
      </div>
    </div>
  );
}

/* 🎨 SAAS STYLES */
const s: any = {
  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    paddingTop: 40,
    background: "linear-gradient(180deg,#f8fafc,#eef2ff)",
  },
  card: {
    width: "100%",
    maxWidth: 520,
    background: "#fff",
    borderRadius: 24,
    padding: 32,
    boxShadow: "0 25px 50px rgba(0,0,0,0.12)",
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
  },
  subtitle: {
    marginTop: 6,
    marginBottom: 24,
    color: "#64748b",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  row: {
    display: "flex",
    gap: 12,
  },
  input: {
    padding: "14px 16px",
    borderRadius: 14,
    border: "1px solid #e5e7eb",
    background: "#f8fafc",
    fontSize: 15,
    outline: "none",
  },
  button: {
    marginTop: 10,
    background: "linear-gradient(135deg,#6366f1,#2563eb)",
    color: "#fff",
    padding: "14px",
    borderRadius: 16,
    fontWeight: 800,
    border: "none",
    cursor: "pointer",
    fontSize: 16,
  },
};
