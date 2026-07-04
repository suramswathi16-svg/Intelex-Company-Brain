import { useNavigate } from "react-router-dom";
import {
  FaBuilding,
  FaUsers,
  FaFileAlt,
  FaRobot,
  FaBell,
} from "react-icons/fa";

function CompanyDashboard() {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <button
        onClick={() => navigate("/dashboard")}
        style={styles.backButton}
      >
        ← Back to Dashboard
      </button>

      <h1>🏢 Company Dashboard</h1>

      <div style={styles.cards}>
        <div style={styles.card}>
          <FaUsers size={35} color="#2563EB" />
          <h2>245</h2>
          <p>Total Employees</p>
        </div>

        <div style={styles.card}>
          <FaFileAlt size={35} color="#10B981" />
          <h2>1,278</h2>
          <p>Documents Uploaded</p>
        </div>

        <div style={styles.card}>
          <FaRobot size={35} color="#F59E0B" />
          <h2>3,562</h2>
          <p>AI Queries</p>
        </div>

        <div style={styles.card}>
          <FaBell size={35} color="#EF4444" />
          <h2>5</h2>
          <p>Critical Alerts</p>
        </div>
      </div>

      <div style={styles.section}>
        <h2>📊 Company Summary</h2>

        <p>✔ 12 Departments</p>
        <p>✔ 198 Active Users Today</p>
        <p>✔ 326 AI Questions Answered Today</p>
        <p>✔ 97% Employee Satisfaction</p>
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

  backButton: {
    padding: "10px 18px",
    background: "#2563EB",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "20px",
  },

  cards: {
    display: "grid",
    gridTemplateColumns: "repeat(4,1fr)",
    gap: "20px",
    marginTop: "25px",
  },

  card: {
    background: "white",
    padding: "25px",
    borderRadius: "15px",
    textAlign: "center",
    boxShadow: "0 5px 12px rgba(0,0,0,.1)",
  },

  section: {
    background: "white",
    marginTop: "30px",
    padding: "25px",
    borderRadius: "15px",
    boxShadow: "0 5px 12px rgba(0,0,0,.1)",
  },
};

export default CompanyDashboard;