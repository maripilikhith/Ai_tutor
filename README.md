<div align="center">
  <h1>🧠 AI Study Companion</h1>
  <p><strong>A Persistent, Contextual, Measurable AI Learning Workspace</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Frontend-Next.js_14-black?style=for-the-badge&logo=next.js" alt="Next.js" />
    <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Database-Supabase-3ECF8E?style=for-the-badge&logo=supabase" alt="Supabase" />
    <img src="https://img.shields.io/badge/AI-Google_Gemini-4285F4?style=for-the-badge&logo=google" alt="Google Gemini" />
  </p>
</div>

---

## 📖 Overview

The **AI Study Companion** is not just another chatbot. It is a fully persistent, context-aware learning partner that helps users understand, practice, measure, and continuously improve their knowledge. 

By unifying learning materials (PDFs), an intelligent AI Tutor, adaptive assessments, concept mastery tracking, and actionable recommendations into a single connected experience, the system continuously answers three core questions:
1. **What am I learning?**
2. **How well am I learning it?**
3. **What should I do next?**

## ✨ Key Features

- **📚 Intelligent RAG & Document Processing:** Upload PDFs. Background workers extract text, perform OCR, map concepts, and embed chunks for accurate vector retrieval.
- **🤖 Grounded AI Tutor:** The Tutor restricts its answers to your uploaded materials. If the material doesn't contain the answer, the Tutor explains why rather than hallucinating. Every claim includes a precise source citation.
- **📝 Adaptive Quizzes & Evaluation:** Generate multiple-choice and open-ended questions based on current concept mastery and recent mistakes. Open-ended answers are evaluated by AI for understanding, accuracy, and missing concepts.
- **📈 Mastery & Growth Analytics:** Visualizes your learning trajectory. Understand which concepts are improving, stable, or declining.
- **🎯 Smart Recommendations:** Automatically suggests the next best action (e.g., "Re-read chapter 2", "Take a quiz on Concept A") based on recent performance.
- **🎙️ Multimodal Interactions:** Built-in Speech-to-Text (STT) and Text-to-Speech (TTS) for an accessible, hands-free learning experience.
- **🔐 Bring Your Own Key (BYOK):** Users can provide their own API keys for AI interactions, ensuring data privacy and cost control.
- **🎨 Modern UI/UX:** Fully responsive design with beautifully crafted **Dark and Light Themes**.
- **📊 Admin Dashboard & Observability:** Platform-wide visibility into user activity, background jobs, AI latency, model token usage, estimated costs, and AI evaluation metrics.

---

## 🏗️ Architecture & Tech Stack

This project follows a strict **Decoupled Feature-Based Architecture**:

### Frontend
- **Framework:** Next.js 14 (App Router)
- **UI:** Tailwind CSS, shadcn/ui, Lucide Icons, Recharts
- **State/AI:** Vercel AI SDK (`useChat`), Context API

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (via Supabase) with `pgvector` for similarity search
- **Auth/Storage:** Supabase Auth (with Row-Level Security) & Supabase Storage
- **AI/LLM:** Google Gemini 2.5 Flash, `text-embedding-004`
- **Background Jobs:** Custom Postgres-based job queue (eliminating heavy Redis/Celery dependencies)
- **Caching:** Upstash Redis

> **Note:** For a deep dive into the architecture design, read our [Architecture Documentation](docs/architecture_documentation.html).

---

## 🚀 Setup Instructions

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.10+)
- A [Supabase](https://supabase.com/) Project
- A [Google Gemini API Key](https://aistudio.google.com/)
- An [Upstash Redis](https://upstash.com/) Database

### 1. Backend Setup

1. **Navigate to the backend directory and create a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - **Windows:** `venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the `backend/` directory based on `.env.example`:
   ```env
   # backend/.env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   SUPABASE_JWT_SECRET=your-jwt-secret
   GEMINI_API_KEY=your-gemini-api-key
   UPSTASH_REDIS_URL=https://your-redis.upstash.io
   UPSTASH_REDIS_TOKEN=your-redis-token
   FRONTEND_URL=http://localhost:3000
   BACKEND_URL=http://localhost:8000
   ENVIRONMENT=development
   ```

5. **Run the backend server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 2. Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Environment Variables:**
   Create a `.env.local` file in the `frontend/` directory based on `.env.example`:
   ```env
   # frontend/.env.local
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

4. **Run the frontend development server:**
   ```bash
   npm run dev
   ```

---

## 🧪 Testing Instructions

### Backend Testing
The backend utilizes `pytest` for robust unit and integration testing. Tests ensure RLS compliance, proper prompt injection defenses, and business logic validity.
```bash
cd backend
pytest
```

### Frontend Testing
Run standard linting and formatting checks for the Next.js application:
```bash
cd frontend
npm run lint
```

---

## 🌍 Deployment Information

### Backend (FastAPI)
The backend is designed to be easily containerized and deployed to services like **Railway**, **Render**, or **Fly.io**.
1. Set up a Dockerfile or use the native Python environment buildpacks provided by your host.
2. Add your `.env` variables securely in the platform's dashboard.
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Next.js)
The frontend is optimized for zero-config deployment on **Vercel**.
1. Import your GitHub repository into Vercel.
2. Select the `frontend/` folder as the Root Directory.
3. Add the `NEXT_PUBLIC_*` environment variables in the Vercel project settings.
4. Deploy!

### Database Migrations
Don't forget to run your Supabase SQL migrations against your production database instance. This creates the necessary tables, enables `pgvector`, establishes the custom `background_jobs` table, and applies Row-Level Security (RLS) policies.

---

## 📚 Project Documentation

We have generated comprehensive, beautifully formatted HTML documentation detailing the internals of this project. You can find them in the `docs/` folder:

1. **[Architecture Documentation](docs/architecture_documentation.html):** System design, ER diagrams, frontend/backend structures, and RAG data flows.
2. **[AI Tools & Usage Documentation](docs/ai_tools_usage_documentation.html):** A deep dive into how AI was used *to build* the product, versus how AI operates *within* the product.
3. **[Development Prompts Documentation](docs/development_prompts_documentation.html):** The actual system prompts, workflows, and iterative engineering strategies used during development.

---
<div align="center">
  <i>Built with precision, care, and intelligent automation.</i>
</div>
