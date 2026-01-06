import Sidebar from "./components/Sidebar";
import Header from "./components/Header";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={styles.layout}>
      <Sidebar />

      <div style={styles.page}>
        <Header />
        <div style={styles.content}>{children}</div>
      </div>
    </div>
  );
}

const styles = {
  layout: {
    display: "flex",
    minHeight: "100vh",
    background: "#f1f5f9",
  },
  page: {
    flex: 1,
    display: "flex",
    flexDirection: "column" as const,
  },
  content: {
    padding: 24,
    flex: 1,
  },
};
