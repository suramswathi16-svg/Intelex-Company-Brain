import { useNavigate } from "react-router-dom";

function Settings() {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <button
        style={styles.back}
        onClick={() => navigate("/dashboard")}
      >
        ← Back to Dashboard
      </button>

      <h1>⚙️ Settings</h1>

      <div style={styles.card}>
        <h3>👤 Profile</h3>
        <p>Admin User</p>

        <h3>🔔 Notifications</h3>
        <p>Enabled</p>

        <h3>🌙 Theme</h3>
        <p>Light Mode</p>

        <button style={styles.logout}>
          Logout
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: "30px",
    background: "#F4F7FC",
    minHeight: "100vh",
    fontFamily: "Arial",
  },

  back: {
    padding: "10px 18px",
    background: "#2563EB",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "20px",
  },

  card: {
    background: "white",
    padding: "30px",
    borderRadius: "15px",
    boxShadow: "0 5px 12px rgba(0,0,0,.1)",
    maxWidth: "500px",
  },

  logout: {
    marginTop: "25px",
    padding: "12px 25px",
    background: "#EF4444",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  },
};

export default Settings;