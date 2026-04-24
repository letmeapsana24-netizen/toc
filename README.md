# TuringLab AI - Turing Machine Simulator

TuringLab AI is a comprehensive educational platform and simulator for Turing Machines (TM), designed for Theory of Computation (TOC) students and enthusiasts. It features a robust simulation engine, a massive question bank of over 1050 problems, and an AI-driven machine generator.

## 🚀 Getting Started

### Prerequisites
- **Node.js**: Required for the backend server.
- **Python 3.x**: Required for the question generator and AI inference scripts.
- **SQLite3**: Required for the question bank database.

### Installation
1. Clone the repository.
2. Navigate to the `backend` directory and install dependencies:
   ```bash
   cd backend
   npm install
   ```
3. (Optional) Generate the question bank database:
   ```bash
   cd ai
   python generate_questions.py
   ```

### Running the Application
You can use the provided batch file to launch both the backend and frontend:
- Run `launch_app.bat` from the root directory.

Alternatively, start them manually:
1. **Backend**:
   ```bash
   cd backend
   node server.js
   ```
   The server will run on `http://localhost:3000`.
2. **Frontend**: Open `frontend/index.html` in your browser.

---

## 🏗️ Project Architecture

### 1. Backend (`/backend`)
An Express server that handles:
- **Simulation Logic**: Provides endpoints for step-by-step (`/api/simulate-step`) and complete (`/api/run-complete`) TM execution.
- **Question Bank API**: Serves questions from the SQLite database, with support for pagination, random selection, and filtering by difficulty/type.
- **AI Integration**: Proxies natural language prompts to the Python inference script.
- **Static File Serving**: Serves the frontend assets.

### 2. Frontend (`/frontend`)
A vanilla HTML5/CSS3/JavaScript application:
- **Interactive Simulator**: Visualizes the TM tape, head, current state, and transition table.
- **Question Navigator**: Interface to browse and select questions from the 1000+ problem library.
- **AI Generation UI**: Allows users to describe a language (e.g., "Palindrome") and get a generated TM.

### 3. AI & Data (`/ai`)
Python-based logic for data generation and inference:
- `generate_questions.py`: Creates `database/tm_questions.db` using 13+ language templates (anbn, 0n1n, parity, palindromes, context-sensitive languages, etc.).
- `inference.py`: A logic-based "AI" that parses natural language prompts and returns corresponding TM configurations.

### 4. Database (`/database`)
Contains `tm_questions.db`, a 3NF normalized SQLite database:
- `questions`: Metadata (title, description, difficulty).
- `states`: State definitions (start, accept, reject).
- `transitions`: δ(q, σ) → (q', σ', D).
- `diagrams`: JSON-encoded structure for visual rendering.

---

## 🤖 Instructions for AI Agents

Welcome, fellow AI! If you are tasked with modifying or extending this project, please follow these guidelines:

### 🛠️ Extending the Machine Logic
- **Simulation Core**: The primary simulation logic is in `backend/server.js` (function `simulateStep`). If you modify how TMs run, ensure compatibility with both the backend and the frontend `app.js`.
- **Adding New Language Types**: 
  - Add the template logic to `ai/generate_questions.py`.
  - Add the prompt parsing to `ai/inference.py` so the AI generator can "understand" the new language.

### 📊 Database Management
- If you change the database schema, update `ai/generate_questions.py` (which creates the tables) AND `backend/server.js` (which queries them).
- Always use the `better-sqlite3` library in the backend for performance.

### 🎨 Frontend Development
- The frontend uses **Vanilla CSS** and **No Frameworks**. Keep it that way unless explicitly asked otherwise.
- The UI state is managed in `frontend/app.js`. When a new question is loaded, ensure the `machine` object is correctly initialized.

### 🧪 Testing
- Test TMs using the `/api/validate` endpoint to ensure transitions are valid.
- Verify simulation consistency by comparing `simulate-step` (single step) and `run-complete` (full history) outputs.

---

## 📜 License
This project is for educational purposes. Feel free to use and modify it for learning Theory of Computation.