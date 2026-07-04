import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#f4f6fb",
      }}
    >
      <div
        style={{
          width: "360px",
          background: "white",
          padding: "30px",
          borderRadius: "12px",
          boxShadow: "0 5px 15px rgba(0,0,0,0.15)",
        }}
      >
        <h2>Intelex Company Brain</h2>
        <p>AI Enterprise Knowledge Assistant</p>

        <input
          type="email"
          placeholder="Email"
          style={{
            width: "100%",
            padding: "10px",
            marginTop: "15px",
            marginBottom: "10px",
            boxSizing: "border-box",
          }}
        />

        <input
          type="password"
          placeholder="Password"
          style={{
            width: "100%",
            padding: "10px",
            marginBottom: "20px",
            boxSizing: "border-box",
          }}
        />

        <button
          onClick={() => navigate("/dashboard")}
          style={{
            width: "100%",
            padding: "12px",
            background: "#2563EB",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Login
        </button>
        <p style={{ marginTop: "20px", textAlign: "center" }}>
  Don't have an account?{" "}
  <span
    onClick={() => navigate("/signup")}
    style={{
      color: "#2563EB",
      cursor: "pointer",
      fontWeight: "bold",
    }}
  >
    Sign Up
  </span>
</p>
      </div>
    </div>
  );
}

export default Login;