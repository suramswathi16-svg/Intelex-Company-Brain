import { useNavigate } from "react-router-dom";
import {
  FaHome,
  FaUpload,
  FaComments,
  FaChartBar,
  FaBuilding,
  FaCog,
  FaBell,
  FaUserCircle,
} from "react-icons/fa";

function Dashboard() {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      {/* Sidebar */}
      <div style={styles.sidebar}>
        <h2 style={{ color: "white" }}>Intelex</h2>

        <div style={styles.menu} onClick={() => navigate("/dashboard")}>
          <FaHome /> Dashboard
        </div>

        <div style={styles.menu} onClick={() => navigate("/upload")}>
          <FaUpload /> Upload
        </div>

        <div style={styles.menu} onClick={() => navigate("/chat")}>
          <FaComments /> AI Chat
        </div>

        <div style={styles.menu} onClick={() => navigate("/analysis")}>
          <FaChartBar /> Analysis
        </div>

        <div style={styles.menu} onClick={() => navigate("/company")}>
          <FaBuilding /> Company
        </div>

        <div style={styles.menu} onClick={() => navigate("/settings")}>
          <FaCog /> Settings
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.main}>
        {/* Top Bar */}
        <div style={styles.topbar}>
          <h2>Company Dashboard</h2>

          <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
            <FaBell size={22} />
            <FaUserCircle size={30} />
          </div>
        </div>

        {/* Cards */}
        <div style={styles.cardContainer}>
          <div style={styles.card}>
            <h3>Employees</h3>
            <h1>245</h1>
          </div>

          <div style={styles.card}>
            <h3>Documents</h3>
            <h1>1278</h1>
          </div>

          <div style={styles.card}>
            <h3>AI Queries</h3>
            <h1>3562</h1>
          </div>

          <div style={styles.card}>
            <h3>Alerts</h3>
            <h1>5</h1>
          </div>
        </div>

        {/* Recent Activity */}
        <div style={styles.activity}>
          <h2>Recent Activity</h2>

          <p>✅ HR Policy uploaded</p>
          <p>✅ Employee Handbook updated</p>
          <p>💬 AI answered 326 questions today</p>
          <p>⚠ 5 Pending Alerts</p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    height: "100vh",
    background: "#F8FAFC",
    fontFamily: "Arial",
  },

  sidebar: {
    width: "230px",
    background: "#0F172A",
    padding: "25px",
  },

  menu: {
    color: "white",
    marginTop: "25px",
    cursor: "pointer",
    display: "flex",
    gap: "10px",
    alignItems: "center",
    fontSize: "18px",
  },

  main: {
    flex: 1,
    padding: "30px",
  },

  topbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  cardContainer: {
    display: "grid",
    gridTemplateColumns: "repeat(4,1fr)",
    gap: "20px",
    marginTop: "30px",
  },

  card: {
    background: "#2563EB",
    color: "white",
    padding: "25px",
    borderRadius: "15px",
    textAlign: "center",
    boxShadow: "0 6px 12px rgba(0,0,0,0.15)",
  },

  activity: {
    background: "white",
    marginTop: "30px",
    padding: "25px",
    borderRadius: "15px",
    boxShadow: "0 5px 10px rgba(0,0,0,0.1)",
  },
};

export default Dashboard;