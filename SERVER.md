# E.D.I.T.H. FastAPI Server

This document describes the FastAPI server implementation for E.D.I.T.H., adapted from the Jarvis assistant architecture.

## Getting Started

### Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Server

Start the server with:

```bash
python run_server.py
```

Or directly with uvicorn:

```bash
uvicorn server.main:app --reload
```

The server will be available at `http://localhost:8000`

### API Documentation

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Chat Endpoints

#### Send Message
- **POST** `/api/chat/message`
- Send a message to E.D.I.T.H. and receive a response
- **Request**:
  ```json
  {
    "message": "What do you know about me?",
    "session_id": "default"
  }
  ```
- **Response**:
  ```json
  {
    "response": "I know you are a software developer.",
    "ok": true,
    "error_type": null,
    "detail": null
  }
  ```

#### Reset Session
- **POST** `/api/chat/reset?session_id=default`
- Clear the context for a conversation session

#### List Sessions
- **GET** `/api/chat/sessions`
- Get all active conversation sessions

### Knowledge Management Endpoints

#### Facts

**Get Facts**
- **GET** `/api/knowledge/facts?subject=john&relation=age`
- Query facts with optional filters
- Parameters:
  - `subject` (optional): Filter by subject
  - `relation` (optional): Filter by relation

**Add Fact**
- **POST** `/api/knowledge/facts`
- Add a new fact
- **Request**:
  ```json
  {
    "subject": "john",
    "relation": "age",
    "object": "30"
  }
  ```

**Update Fact**
- **PUT** `/api/knowledge/facts`
- Replace an existing fact

**Delete Fact**
- **DELETE** `/api/knowledge/facts?subject=john&relation=age`
- Delete a specific fact or all facts for a subject

#### Entities

**List Entities**
- **GET** `/api/knowledge/entities`
- Get all known entities (people, places, etc.)

**Get Entity Profile**
- **GET** `/api/knowledge/entities/{entity}`
- Get the complete profile of an entity with all related facts

#### Collections

**Create Collection**
- **POST** `/api/knowledge/collections`
- Create a named collection of items
- **Request**:
  ```json
  {
    "owner": "user",
    "name": "favorite_books",
    "items": ["The Hobbit", "Dune"]
  }
  ```

**Get Collections**
- **GET** `/api/knowledge/collections?owner=user`
- Get all collections for an owner

**Get Collection**
- **GET** `/api/knowledge/collections/{owner}/{name}`
- Get a specific collection

**Add Item**
- **POST** `/api/knowledge/collections/{owner}/{name}/items?item=NewBook`
- Add an item to a collection

**Update Item**
- **PUT** `/api/knowledge/collections/{owner}/{name}/items?old=OldBook&new=NewBook`
- Replace an item in a collection

**Remove Item**
- **DELETE** `/api/knowledge/collections/{owner}/{name}/items?index=0`
- Remove an item by index (0-based)

**Delete Collection**
- **DELETE** `/api/knowledge/collections/{owner}/{name}`
- Delete an entire collection

#### Aliases

**Get All Aliases**
- **GET** `/api/knowledge/aliases`
- Get all entity aliases

**Create Alias**
- **POST** `/api/knowledge/aliases`
- Create an alias for quick reference
- **Request**:
  ```json
  {
    "alias": "johnny",
    "target": "john"
  }
  ```

## Architecture

The server is structured as follows:

```
server/
├── __init__.py
├── main.py              # FastAPI app setup, lifespan management
└── routers/
    ├── __init__.py
    ├── chat.py          # Chat and conversation endpoints
    └── knowledge.py     # Knowledge base management endpoints
```

### Key Features

1. **Session Management**: Each conversation can have its own context/session with automatic session management
2. **Database Integration**: Uses EDITH's SQLite-based memory store
3. **CORS Support**: Configured to accept requests from any origin
4. **Automatic API Docs**: Swagger UI and ReDoc documentation available
5. **Error Handling**: Structured error responses with proper HTTP status codes

## Configuration

The server configuration is set in [server/main.py](server/main.py):

- **Host**: 127.0.0.1 (localhost)
- **Port**: 8000
- **Reload**: Enabled for development

To change these settings, modify `run_server.py` or pass flags to uvicorn:

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8080
```

## Integration with EDITH Core

The server integrates with EDITH's core functionality:

- **Intent Processing**: Uses `core.process.process_input()` for understanding user messages
- **Memory Store**: Leverages `memory.store` for persistent knowledge
- **Context Management**: Uses `memory.context.make_context()` for conversation state

This ensures the server provides the same intelligent, context-aware responses as the CLI interface.

## Development

### Adding New Endpoints

To add new endpoints:

1. Create a new router in `server/routers/` (e.g., `server/routers/calendar.py`)
2. Define your endpoints and models
3. Include the router in `server/main.py`:
   ```python
   from server.routers import calendar
   app.include_router(calendar.router)
   ```

### Testing

Run the test suite to verify server functionality:

```bash
pytest tests/
```

## Future Enhancements

Similar to Jarvis, you can extend E.D.I.T.H. with:

- **Weather Integration**: Add weather-related commands and information
- **Task Management**: Track tasks and todos
- **Calendar Integration**: Schedule events and reminders
- **Timer System**: Set and manage timers
- **Notifications**: Proactive reminders and alerts

Each feature would have:
1. A new router in `server/routers/`
2. Core logic in the respective module
3. Database schema updates as needed
4. Integration with the chat endpoint where appropriate
