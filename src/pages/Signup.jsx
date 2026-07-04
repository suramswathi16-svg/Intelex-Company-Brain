import { useNavigate } from "react-router-dom";

function Signup() {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2>Create Account</h2>
        <p>Register to Intelex Company Brain</p>

        <input type="text" placeholder="Full Name" style={styles.input} />
        <input type="email" placeholder="Email" style={styles.input} />
        <input type="password" placeholder="Password" style={styles.input} />
        <input type="password" placeholder="Confirm Password" style={styles.input} />

        <button style={styles.button}>
          Sign Up
        </button>

        <p style={{ marginTop: "20px" }}>
          Already have an account?
          <span
            style={{ color: "#2563EB", cursor: "pointer", marginLeft: "5px" }}
            onClick={() => navigate("/")}
          >
            Login
          </span>
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#F4F7FC",
  },
  card: {
    width: "380px",
    background: "white",
    padding: "30px",
    borderRadius: "12px",
    boxShadow: "0 5px 12px rgba(0,0,0,.15)",
    textAlign: "center",
  },
  input: {
    width: "100%",
    padding: "12px",
    margin: "10px 0",
    boxSizing: "border-box",
  },
  button: {
    width: "100%",
    padding: "12px",
    background: "#2563EB",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  },
};

export default Signup;