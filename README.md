# SafePlate

SafePlate is a hackathon-ready web app that scans restaurant menus and flags allergen and medication-food risks using a single GPT-4o vision call.

## Stack

- Frontend: React + Vite
- Backend: FastAPI + SQLite
- AI: OpenAI GPT-4o (vision + structured JSON)

## Project Structure

```
.
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ prompts.py
│  │  ├─ schemas.py
│  │  └─ services/
│  │     └─ analyzer.py
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ App.jsx
│  │  ├─ api.js
│  │  ├─ styles.css
│  │  ├─ components/
│  │  │  ├─ ProfileForm.jsx
│  │  │  ├─ MenuCapture.jsx
│  │  │  ├─ ResultsView.jsx
│  │  │  └─ HistoryPanel.jsx
│  │  └─ utils/
│  │     └─ image.js
│  ├─ package.json
│  ├─ vite.config.js
│  └─ .env.example
└─ .gitignore
```

## Backend Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:
   `pip install -r backend/requirements.txt`
3. Copy env template:
   `copy backend\\.env.example backend\\.env` (Windows)
4. Add your OpenAI key to `backend/.env`.
5. Run API:
   `uvicorn app.main:app --reload --port 8000` from `backend/`.

## Frontend Setup

1. Install dependencies:
   `npm install` from `frontend/`.
2. Copy env template:
   `copy frontend\\.env.example frontend\\.env`
3. Run frontend:
   `npm run dev` from `frontend/`.

## API Endpoints

- `POST /api/profile`
- `GET /api/profile/{id}`
- `POST /api/analyze`
- `GET /api/history/{profile_id}`

## Deployment Notes

- Deploy frontend to Vercel.
- Deploy backend to Railway or Render.
- Set `VITE_API_BASE_URL` on frontend to your backend URL.
- Set `OPENAI_API_KEY`, `OPENAI_MODEL`, and `CORS_ORIGINS` on backend.
