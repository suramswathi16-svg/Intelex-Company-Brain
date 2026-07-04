import { useNavigate } from "react-router-dom";
import { FaUsers, FaUserCheck, FaUserTimes, FaChartLine } from "react-icons/fa";

function EmployeeAnalysis() {
    const navigate = useNavigate();
  return (
    <div style={styles.container}>
        <button
  onClick={() => navigate("/dashboard")}
  style={{
    padding: "10px 20px",
    background: "#2563EB",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "20px",
  }}
>
  ← Back to Dashboard
</button>
      <h1>Employee Analysis</h1>

      <div style={styles.cards}>
        <div style={styles.card}>
          <FaUsers size={35} color="#2563EB" />
          <h2>245</h2>
          <p>Total Employees</p>
        </div>

        <div style={styles.card}>
          <FaUserCheck size={35} color="green" />
          <h2>228</h2>
          <p>Present Today</p>
        </div>

        <div style={styles.card}>
          <FaUserTimes size={35} color="red" />
          <h2>17</h2>
          <p>On Leave</p>
        </div>

        <div style={styles.card}>
          <FaChartLine size={35} color="orange" />
          <h2>92%</h2>
          <p>Performance Score</p>
        </div>
      </div>

      <div style={styles.section}>
        <h2>Department Overview</h2>

        <div style={styles.row}>
          <span>Engineering</span>
          <progress value="90" max="100"></progress>
        </div>

        <div style={styles.row}>
          <span>HR</span>
          <progress value="75" max="100"></progress>
        </div>

        <div style={styles.row}>
          <span>Finance</span>
          <progress value="65" max="100"></progress>
        </div>

        <div style={styles.row}>
          <span>Marketing</span>
          <progress value="80" max="100"></progress>
        </div>
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

  row: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "20px",
  },
};

export default EmployeeAnalysis;