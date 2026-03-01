# MediMenu

MediMenu is a powerful, dual-sided web application that bridges the gap between restaurants and diners with dietary restrictions. By leveraging OpenAI's GPT-4o vision capabilities, MediMenu digitizes restaurant menus and provides personalized safety assessments for users based on their specific allergies, medications, and dietary preferences.

## 🌟 Key Features

### For Diners (B2C)
- **Personalized Profiles**: Set up a detailed profile with specific allergies, medications, and dietary restrictions (e.g., Vegan, Gluten-Free, Halal).
- **QR Code Menu Scanning**: Scan a restaurant's MediMenu QR code to instantly view their menu.
- **Personalized Risk Assessment**: Every dish on the menu is automatically color-coded based on your profile:
  - 🟢 **OK (Green)**: Safe to eat.
  - 🟡 **Caution (Yellow)**: Possible cross-contact risks or minor dietary warnings.
  - 🔴 **Avoid (Red)**: Contains allergens or heavily conflicts with your restrictions.
- **Detailed Safety Insights**: See exactly why a dish was flagged and what ingredients triggered the warning.

### For Restaurants (B2B)
- **AI-Powered Menu Digitization**: Simply upload an image of your physical menu, and GPT-4o vision will extract the dishes and infer ingredients automatically.
- **Menu Management**: Review and edit the AI-generated menu, confirm specific allergens, and flag cross-contact risks for shared preparation areas.
- **Instant Publishing**: Once confirmed, publish the menu to immediately generate a scan-ready QR code for your diners to use.
- **Analytics Dashboard**: Track how many diners with specific allergies are scanning your menu to better tailor your offerings in the future.

## 🛠️ Tech Stack

- **Frontend**: React + Vite, React Router, vanilla CSS
- **Backend**: FastAPI (Python), SQLite
- **AI Integration**: OpenAI GPT-4o (Vision + Structured JSON outputs)

## 📁 Project Structure

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ main.py           # FastAPI entry point & API endpoints
│  │  ├─ config.py         # Environment configuration
│  │  ├─ database.py       # SQLite database operations
│  │  ├─ prompts.py        # OpenAI system prompts
│  │  ├─ schemas.py        # Pydantic models & validation
│  │  └─ services/
│  │     └─ analyzer.py    # GPT-4o Vision API integration
│  ├─ requirements.txt     # Python dependencies
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ App.jsx           # React app router & main B2C view
│  │  ├─ api.js            # API client for backend communication
│  │  ├─ styles.css        # Global styles and UI components
│  │  ├─ components/       # UI Components (Dashboards, QR Scanner, forms)
│  │  └─ utils/
│  │     └─ image.js       # Image processing utilities
│  ├─ package.json
│  ├─ vite.config.js
│  └─ .env.example
└─ .gitignore
```

## 🚀 Getting Started

You can try our app here: https://medimenu-frontend.onrender.com

For local set up, refer to below steps:
### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```
2. **Create and activate a Python virtual environment** (Optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**:
   - Copy the environment template:
     ```bash
     cp .env.example .env
     ```
   - Open `backend/.env` and add your `OPENAI_API_KEY`.
5. **Run the API server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend will be available at `http://localhost:8000`.*

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```
2. **Install dependencies**:
   ```bash
   npm install
   ```
3. **Configure environment variables**:
   - Copy the environment template:
     ```bash
     cp .env.example .env
     ```
   - Make sure `VITE_API_BASE_URL` is set to your backend URL (usually `http://localhost:8000`).
4. **Run the development server**:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:5173`.*

## 🛣️ API Endpoints Overview

### B2C (Diners)
- `POST /api/profile` - Create a new user profile
- `GET /api/profile/{id}` - Fetch user profile details
- `POST /api/analyze` - Analyze an independent menu image against a profile
- `GET /api/history/{profile_id}` - View past scan history

### B2B (Restaurants)
- `POST /api/restaurant` - Register a new restaurant
- `GET /api/restaurants` - List available restaurants
- `GET /api/restaurant/{restaurant_id}` - Get restaurant details
- `POST /api/restaurant/{restaurant_id}/menu` - Upload and analyze a menu image via GPT-4o
- `GET /api/restaurant/{restaurant_id}/menu` - Get the current draft menu
- `PUT /api/restaurant/{restaurant_id}/menu` - Update dishes and confirm allergens
- `POST /api/restaurant/{restaurant_id}/menu/confirm` - Publish the menu for QR scanning
- `GET /api/restaurant/{restaurant_id}/menu/personalized` - Get a personalized view of the menu for a specific profile
- `GET /api/restaurant/{restaurant_id}/analytics` - View scan analytics


## 📱 Mobile Testing

MediMenu is designed as a responsive, mobile-first web application (React). Here is how you can deploy and view it on a mobile device:

### Local Network (Your Phone)
Go to https://medimenu-frontend.onrender.com on your phone for demo.

## 📈 Financial View
- **B2B (Restaurants)**: A tiered subscription model. Basic menu digitization is free, but advanced features like cross-contact analysis, automated allergen tagging, and diner analytics are part of a premium tier.
- **B2C (Diners)**: A freemium model. Basic profile matching and scanning are free to ensure accessibility for those who need it most. Premium features could include saving favorite safe meals across multiple restaurants and nutritional tracking.

## 🔮 Future Prospects
- **POS Integration**: Direct integration with restaurant Point-of-Sale (POS) systems (like Toast or Square) to automatically sync menu updates and ingredient changes in real-time.
- **Community-Driven Reviews**: Allowing users to verify and review the allergen-safety of specific dishes.
- **Multi-lingual Support**: Translating menus dynamically for international travelers with dietary restrictions.
- **Expanded Medical Database**: Partnering with healthcare providers to maintain an up-to-date database of complex food-medication interactions.

## 👩‍💻 Authors
- Jenny
- Sam 
- Sherry
- Mckenna

## 🏛️ Source & Usage
Built with ❤️ for **CheeseHack 2026** at **UW-Madison**.

