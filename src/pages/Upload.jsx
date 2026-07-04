import { FaCloudUploadAlt, FaArrowLeft } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

function Upload() {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <button style={styles.backButton} onClick={() => navigate("/dashboard")}>
        <FaArrowLeft /> Back
      </button>

      <div style={styles.card}>
        <FaCloudUploadAlt size={70} color="#2563EB" />

        <h2>Upload Company Documents</h2>

        <p>
          Upload PDF, DOCX, PPTX, TXT or company policy documents.
        </p>

        <input
          type="file"
          style={{ marginTop: "20px", marginBottom: "20px" }}
        />

        <button style={styles.uploadButton}>
          Upload Document
        </button>
      </div>

      <div style={styles.list}>
        <h3>Recently Uploaded</h3>

        <p>📄 Employee Handbook.pdf</p>
        <p>📄 Leave Policy.pdf</p>
        <p>📄 HR Guidelines.docx</p>
        <p>📄 Company Rules.pdf</p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: "40px",
    background: "#F4F7FC",
    minHeight: "100vh",
    fontFamily: "Arial",
  },

  backButton: {
    padding: "10px 18px",
    border: "none",
    background: "#2563EB",
    color: "white",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "20px",
  },

  card: {
    background: "white",
    padding: "40px",
    borderRadius: "15px",
    textAlign: "center",
    boxShadow: "0 5px 12px rgba(0,0,0,0.1)",
  },

  uploadButton: {
    padding: "12px 30px",
    background: "#2563EB",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
  },

  list: {
    marginTop: "30px",
    background: "white",
    padding: "25px",
    borderRadius: "15px",
    boxShadow: "0 5px 12px rgba(0,0,0,0.1)",
  },
};

export default Upload;