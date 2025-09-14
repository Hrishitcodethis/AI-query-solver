# AI Powered DB Profiler

## 🚀 How to Use as an App User

Welcome to **AI Query Solver**! This guide will help you quickly get started as an end user and discover what you can do with this app.

---

### 🧑‍💻 Getting Started

1. **Upload Your Data Files**  
   - **Required:** Upload a `.db` file containing your data.
   - **Optional:** Upload a `query_log` file to enable advanced log-based analysis.

2. **Send a Query for Analysis**  
   - Go to the **Query Analyser** section.
   - Enter your query and submit it for analysis.

   <img width="1119" height="439" alt="Screenshot 2025-09-15 at 1 27 55 AM" src="https://github.com/user-attachments/assets/9eb7b6ee-33e2-42ab-a66e-1f3f18ca63a2" />

3. **Receive Your Query ID**  
   - After submitting, you'll receive a unique **Query ID**.
   - Use this ID in the chat to refer to your query for further analysis or follow-up questions.

---

### ✨ Features Available for Users

- **Natural Language Query Solving:**  
  Ask questions about your data and get instant, AI-powered insights.

  <img width="445" height="624" alt="Screenshot 2025-09-15 at 1 37 49 AM" src="https://github.com/user-attachments/assets/24b05f1b-96b9-4ef2-b3d7-681d436e54a5" />
  <img width="412" height="607" alt="Screenshot 2025-09-15 at 1 38 25 AM" src="https://github.com/user-attachments/assets/280948fc-f87c-4e9d-b5f2-e0ba278e1794" />

- **Multi-source Data Extraction:**  
  Answers are derived from your uploaded database and optional query logs.

- **Query Analyser:**  
  Submit a query and receive a unique ID for tracking, discussion, or further analysis.

- **Deep Analysis & Optimisation Suggestions:**  
  Request a deep analysis of your query to discover bottlenecks, performance issues, and get optimisation tips.

- **Graphical Analysis:**  
  When prompted, the system can generate visualisations to help you better understand query performance and results.

- **History Tracking:**  
  Review your previous queries and their results.

- **Personalised Experience:**  
  If authentication is enabled, log in for custom responses and saved history.

- **Easy-to-Use Interface:**  
  Designed for quick, clear, and efficient interaction.

---

## 🛠️ How to Use the Code

- All main logic resides in `src/` (or as per your repo structure).
- To add new AI models or plugins, follow the documentation in `docs/`.
- See example usage in `examples/` or run unit tests with:
  ```bash
  pytest tests/
  ```

---

## 💡 System Overview & Idea

**AI Query Solver** helps users analyse queries against their own database, providing AI-powered analysis, optimisation suggestions, and visualisations. The system is modular, allowing integration of different AI models, rule-based engines, or external APIs.

- **Flexibility:** Easily add/remove functionalities.
- **Scalability:** Designed to handle many simultaneous users/queries.
- **Extensibility:** Plug in new models or data sources for improved results.

---

### 🧑‍🔬 Tech Stack

- **Backend:** Python (Flask/FastAPI), Node.js (Express) *(specify as per your implementation)*
- **AI Models:** OpenAI GPT, custom ML models, etc.
- **Database:** SQLite/PostgreSQL/MongoDB *(as per your setup)*
- **Frontend:** React/Vue/HTML *(if applicable)*
- **Other:** Docker, CI/CD with GitHub Actions, etc.

---

### 🏗️ Features

- **AI Query Processing**
- **Pluggable Architecture**
- **User Management & History**
- **Query Analysis & Optimisation**
- **Graphical Visualisations**
- **API Integration**
- **Customisable UI (if frontend exists)**
- **Robust Error Handling**

---

## 🤝 Contributing

- Fork the repo and submit PRs!
- Check out `CONTRIBUTING.md` for guidelines.

---

## 📄 License

This project is licensed under the MIT License.

---

**Happy Query Solving!**
