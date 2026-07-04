import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaArrowLeft, FaPaperPlane, FaRobot } from "react-icons/fa";

function Chat() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");

  const [messages, setMessages] = useState([
    {
      sender: "AI",
      text: "👋 Hello! I'm Intelex AI. Ask me anything about company policies, HR rules, or documents.",
    },
    {
      sender: "You",
      text: "What is the leave policy?",
    },
    {
      sender: "AI",
      text: "Employees are entitled to 20 annual leave days and 12 sick leave days.",
    },
  ]);
  const sendMessage = () => {
  if (message.trim() === "") return;

  setMessages([
    ...messages,
    { sender: "You", text: message },
    {
      sender: "AI",
      text: "Thank you! This is a demo response. The backend AI will answer here later.",
    },
  ]);

  setMessage("");
};

  return (
    <div style={styles.container}>
      <button style={styles.back} onClick={() => navigate("/dashboard")}>
        <FaArrowLeft /> Dashboard
      </button>

      <div style={styles.chatBox}>
        <div style={styles.header}>
          <FaRobot size={28} />
          <h2>Intelex AI Assistant</h2>
        </div>

        <div style={styles.messages}>
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                ...styles.message,
                alignSelf:
                  msg.sender === "You" ? "flex-end" : "flex-start",
                background:
                  msg.sender === "You" ? "#2563EB" : "#E5E7EB",
                color:
                  msg.sender === "You" ? "white" : "black",
              }}
            >
              <strong>{msg.sender}:</strong> {msg.text}
            </div>
          ))}
        </div>

        <div style={styles.inputArea}>
          <input
            type="text"
            placeholder="Ask a question..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            style={styles.input}
          />

          <button style={styles.send} onClick={sendMessage}>
  <FaPaperPlane />
</button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    background: "#F4F7FC",
    minHeight: "100vh",
    padding: "30px",
    fontFamily: "Arial",
  },

  back: {
    padding: "10px 18px",
    border: "none",
    background: "#2563EB",
    color: "white",
    borderRadius: "8px",
    cursor: "pointer",
    marginBottom: "20px",
  },

  chatBox: {
    background: "white",
    borderRadius: "15px",
    boxShadow: "0 5px 12px rgba(0,0,0,.1)",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    height: "80vh",
  },

  header: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    borderBottom: "1px solid #ddd",
    paddingBottom: "15px",
  },

  messages: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "15px",
    marginTop: "20px",
    overflowY: "auto",
  },

  message: {
    padding: "12px",
    borderRadius: "12px",
    maxWidth: "70%",
  },

  inputArea: {
    display: "flex",
    gap: "10px",
    marginTop: "20px",
  },

  input: {
    flex: 1,
    padding: "12px",
    borderRadius: "8px",
    border: "1px solid #ccc",
  },

  send: {
    background: "#2563EB",
    color: "white",
    border: "none",
    padding: "12px 18px",
    borderRadius: "8px",
    cursor: "pointer",
  },
};

export default Chat;