# 🐉 MAGGxDND

> AI-Powered D&D Game Engine with Real-Time Web Interface

<div align="center">
  <img src="./img/MAGGxDND.png" alt="MAGGxDND Logo" width="60%">
</div>

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## 📖 About

**MAGGxDND** is an AI-powered D&D 5e game engine with a real-time web interface. It features:

- 🤖 **AI Dungeon Master** — Powered by Google Gemini for dynamic storytelling
- 🎮 **Real-Time Combat** — WebSocket-based real-time game updates
- 🌍 **Living World** — NPCs act independently with their own goals
- 📝 **Full Character Creation** — 13-step D&D 5e character builder
- 🎲 **Dice Rolling** — All standard D&D dice types
- 💾 **Save/Load** — Persistent game state

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.11+) |
| **Frontend** | React 19 + TypeScript + Vite |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI** | Google Gemini API |
| **Real-time** | WebSocket |
| **State** | Zustand |
| **Vector DB** | ChromaDB |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key ([get one free](https://makersuite.google.com/app/apikey))

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/MAGGxDND.git
cd MAGGxDND

# Copy env template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Install Dependencies

```bash
# Python
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run build && cd ..
```

### 3. Run

```bash
python start.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Dev Mode

```bash
# Backend (Terminal 1)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend && npm run dev
```

---

## 📁 Project Structure

```
MAGGxDND/
├── backend/              # FastAPI server
│   ├── src/
│   │   ├── api/          # REST API routers
│   │   ├── auth/         # Authentication (JWT)
│   │   ├── database/     # SQLAlchemy setup
│   │   ├── models/       # DB models
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities
│   └── tests/            # Backend tests
├── frontend/             # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API clients
│   │   ├── store/        # Zustand state
│   │   └── types/        # TypeScript types
│   └── arts/             # Game art assets
├── core/                 # Game engine core
│   ├── game/             # Session engine
│   ├── entity/           # Player, NPC, entities
│   ├── magg/             # AI Dungeon Master
│   └── schemas/          # Data schemas
├── docs/                 # Documentation
├── data/                 # SQLite database
└── logs/                 # Application logs
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](./docs/QUICKSTART.md) | Get started in 5 minutes |
| [Env Setup](./backend/ENV_SETUP_GUIDE.md) | Full environment configuration |
| [Architecture](./docs/SERVER_ARCHITECTURE.md) | Server architecture overview |
| [Session API](./docs/SESSION_API_GUIDE.md) | Session management API guide |
| [Reorganization](./docs/REORGANIZATION_GUIDE.md) | Project structure guide |

---

## 🧪 Testing

```bash
# Backend
cd backend && pytest tests/

# Frontend
cd frontend && npm run test
```

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](./CONTRIBUTING.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 🔒 Security

Found a security vulnerability? Please review our [Security Policy](./SECURITY.md).

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.

---

<div align="center">

**MAGGxDND** — Where AI meets dice & dragons 🐉🎲

[Documentation](./docs/) · [API Docs](http://localhost:8000/docs) · [Issues](../../issues) · [Pull Requests](../../pulls)

</div>
