# E.D.I.T.H.
**Extended Distributed Intelligence Through Humanistic Interaction**

A conversational AI assistant that learns from your corrections, manages your knowledge, and integrates with your calendar. Built with FastAPI, SQLite, and Claude AI.

## Features

### 🧠 Learning System
- **Correction Tracking** — Log corrections when EDITH gets something wrong
- **Pattern Analysis** — Automatically detect correction patterns to infer your preferences
- **Preference Management** — Explicit and inferred preferences with confidence levels
- **Adaptive Responses** — EDITH learns and improves over time

### 📚 Knowledge Management
- **Facts Storage** — Subject-relation-object triples for flexible knowledge representation
- **Entity Profiles** — Complete profiles for people, places, and concepts
- **Collections** — Organize items into named collections (lists, groups, etc.)
- **Aliases** — Map multiple names to the same entity

### 📅 Calendar Integration
- **Event Management** — Create, read, update, delete calendar events
- **Natural Language** — Schedule events using natural language ("add a meeting tomorrow at 3pm")
- **Intent Parsing** — Smart command recognition for calendar operations
- **Error Handling** — Graceful error recovery and user feedback

### 💬 Conversation Management
- **Session Persistence** — Maintain context across conversations
- **Message History** — Store all messages with metadata for learning
- **Intent Tracking** — Track what EDITH was trying to accomplish

## Architecture

```
EDITH/
├── server/                  # FastAPI application
│   ├── main.py             # App entry point
│   └── routers/
│       ├── chat.py         # Conversation endpoints
│       ├── knowledge.py    # Knowledge management
│       └── learning.py     # Learning/correction system
├── core/
│   ├── dispatch.py         # Action handlers
│   ├── process.py          # Input processing pipeline
│   └── services/
│       └── calendar_client.py  # Calendar API client
├── intent/
│   ├── parser.py           # Intent parsing pipeline
│   ├── patterns.py         # Regex patterns for fast matching
│   └── llm.py              # LLM-based intent interpretation
├── memory/
│   ├── store.py            # SQLite database operations
│   ├── context.py          # Session context management
│   └── resolver.py         # Entity resolution
└── data/
    └── edith.db            # SQLite database
```

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Luissoares11/EDITH.git
cd EDITH

# Install dependencies
pip install -r requirements.txt

# Create .env file with your configuration
echo "ANTHROPIC_API_KEY=your_key_here" > .env
echo "CALENDAR_SERVICE_URL=http://your-calendar-service" >> .env
echo "CALENDAR_API_TOKEN=your_token" >> .env
```

### Running the Server

```bash
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Server will be available at `http://localhost:8000`

## API Endpoints

### Chat
- `POST /api/chat/message` — Send a message and get a response
- `GET /api/chat/history/{session_id}` — Get conversation history
- `POST /api/chat/reset` — Reset a session

### Knowledge
- `GET/POST /api/knowledge/facts` — Query and store facts
- `GET /api/knowledge/entities` — List all known entities
- `GET /api/knowledge/collections` — Manage collections

### Learning
- `POST /api/learning/corrections` — Log a correction
- `GET /api/learning/corrections` — Query correction log
- `GET /api/learning/patterns/{intent}` — Analyze correction patterns
- `POST/GET /api/learning/preferences` — Manage preferences

## Example Usage

### Chat
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is Luis",
    "session_id": "default"
  }'
```

### Calendar
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Schedule a meeting tomorrow at 2pm",
    "session_id": "default"
  }'
```

### Learning
```bash
curl -X POST http://localhost:8000/api/learning/corrections \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 5,
    "intent": "create_task",
    "field": "priority",
    "edith_value": "medium",
    "corrected_value": "high"
  }'
```

## Database Schema

### facts
- Stores knowledge as subject-relation-object triples
- Indexes on subject and relation for fast queries

### conversations & messages
- Tracks conversation sessions and message history
- Enables context persistence and learning

### corrections
- Logs all user corrections
- Used to infer preferences and patterns

### preferences
- Stores learned and explicit preferences
- Includes confidence levels and confirmation status

### collections
- Named groups of items per owner
- JSON-serialized for flexible schemas

## Configuration

Set these environment variables in `.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
CALENDAR_SERVICE_URL=http://your-calendar-service-url
CALENDAR_API_TOKEN=your_calendar_api_token
EDITH_DB_PATH=data/edith.db  # Optional, defaults to ./data/edith.db
```

## Technologies

- **FastAPI** — Modern web framework
- **SQLite** — Lightweight persistent storage
- **Anthropic Claude** — LLM for intent parsing and responses
- **httpx** — Async HTTP client for calendar service
- **Pydantic** — Data validation

## License

MIT

## Author

Luis Soares
