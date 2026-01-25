import { CSSProperties } from "react";
import DemoForm from "./DemoForm";

export const metadata = {
  title: "SigortaTakvimi | Sigorta Acenteleri İçin Poliçe Takip Sistemi",
  description:
    "Sigorta acenteleri için poliçe bitişlerini otomatik takip eden SaaS yazılımı.",
};

export default function Page() {
  return (
    <main style={s.page}>
      <section style={s.container}>
        <div>
          <span style={s.badge}>Sigorta Acenteleri İçin SaaS</span>

          <h1 style={s.title}>
            Sigorta Acenteleri İçin
            <br />
            Poliçe Takip Yazılımı
          </h1>

          <h2 style={s.subtitle}>
            Poliçe bitişlerini otomatik takip edin, müşterilerinizi zamanında arayın.
          </h2>

          <ul style={s.list}>
            <li>Otomatik poliçe hatırlatma</li>
            <li>Müşteri takip sistemi</li>
            <li>Acente performans raporları</li>
            <li>Bulut tabanlı güvenli altyapı</li>
          </ul>
        </div>

        <DemoForm />
      </section>
    </main>
  );
}

const s: Record<string, CSSProperties> = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(180deg,#f8fafc,#eef2ff)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  container: {
    maxWidth: 1100,
    width: "100%",
    display: "grid",
    gridTemplateColumns: "1.2fr 0.8fr",
    gap: 60,
  },
  badge: {
    background: "#e0e7ff",
    color: "#3730a3",
    padding: "6px 14px",
    borderRadius: 999,
    fontSize: 13,
    fontWeight: 600,
    display: "inline-block",
    marginBottom: 16,
  },
  title: {
    fontSize: 42,
    fontWeight: 900,
    lineHeight: 1.15,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 18,
    color: "#475569",
    marginBottom: 24,
  },
  list: {
    paddingLeft: 18,
    lineHeight: "2em",
    color: "#334155",
  },
};
