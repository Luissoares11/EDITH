# EDITH Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / CLIENT                             │
│         (Web, CLI, Mobile, Integration)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   EDITH (FastAPI)                            │
│  The intelligent core — brain, personality, coordinator     │
└──────────┬──────────────────────────┬──────────────────────┘
           │                          │
           │ Routers                  │
    ┌──────┴────────┬─────────────┐  │
    │               │             │  │
    ▼               ▼             ▼  ▼
┌────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐
│ Chat   │  │ Knowledge  │  │ Learning │  │ Services    │
│ Router │  │  Router    │  │ Router   │  │ (external)  │
└────────┘  └────────────┘  └──────────┘  └─────────────┘
    │            │              │              │
    └────┬───────┴──────────┬───┴──────────────┘
         │                  │
         ▼                  ▼
    ┌─────────────────────────────┐
    │  Memory Store (SQLite)      │
    │  - Conversations/Messages   │
    │  - Facts & Entities         │
    │  - Collections              │
    │  - Corrections              │
    │  - Preferences              │
    └─────────────────────────────┘
         │
         ▼
    ┌──────────────┐
    │  edith.db    │
    └──────────────┘
```

## The Brain Layers

### 1. Chat Layer (`/api/chat`)
**What it does:** Handle conversation

- POST `/api/chat/message` — Send message, get response
- GET `/api/chat/history/{session_id}` — Retrieve conversation history
- POST `/api/chat/reset` — Clear a session

**Data:** Conversations, messages, intents

**Key insight:** Each message is stored with:
- What the user said
- What EDITH responded
- The parsed intent
- A unique message_id (for linking corrections)

### 2. Knowledge Layer (`/api/knowledge`)
**What it does:** Store and retrieve facts about the world

- Facts (subject-relation-object triples)
- Entities (people, places, things)
- Collections (lists you care about)
- Aliases (shortcuts)

**Data:** Facts, entities, collections

**Key insight:** The flexible fact model lets you store any relationship:
- `Luis | age | 28`
- `Luis | lives_in | Austin`
- `Machine Learning | taught_by | Luis`

No fixed schema needed. You define the relations you use.

### 3. Learning Layer (`/api/learning`)
**What it does:** Learn from corrections and build preferences

- POST `/api/learning/corrections` — Log when you correct EDITH
- GET `/api/learning/patterns/{intent}` — Analyze what EDITH gets wrong
- POST `/api/learning/preferences` — Create/store learned preferences
- GET `/api/learning/preferences` — View all preferences

**Data:** Corrections, patterns, preferences

**Key insight:** This is how EDITH gets smarter. Every correction is a data point:
```
correction = (what_EDITH_suggested, what_you_corrected_to, context)
pattern = frequent(corrections)
preference = pattern_with_confidence
```

### 4. Services Layer (Future)
**What it does:** Coordinate external services

Eventually: task managers, calendar, weather, automation, etc.

For now: EDITH calls them manually when needed.

## The Database Schema

```sql
-- Conversations & Messages (Chat context)
conversations
├─ id
├─ session_id
├─ title
└─ created_at

messages
├─ id
├─ conversation_id
├─ role (user/assistant/system)
├─ content
├─ intent
└─ created_at

-- Knowledge Base (Facts & Entities)
facts
├─ id
├─ subject
├─ relation
├─ object
└─ created_at

collections
├─ id
├─ owner
├─ name
├─ items (JSON)
└─ created_at

aliases
├─ alias
└─ target

-- Learning (Corrections & Preferences)
corrections
├─ id
├─ message_id (links to messages)
├─ intent (what EDITH was doing)
├─ field (what was wrong)
├─ edith_value (what EDITH suggested)
├─ corrected_value (what you changed it to)
├─ context (extra info for pattern matching)
└─ created_at

preferences
├─ id
├─ category (tasks, scheduling, etc.)
├─ key (preference name)
├─ value (preference value)
├─ learned_from (explicit/inferred)
├─ confidence (0-1)
├─ confirmed (boolean)
└─ created_at
```

## How It All Works Together

### Scenario: Task Creation with Learning

```
1. User sends message
   POST /api/chat/message
   {"message": "Add a task: Fix bug in API", "session_id": "default"}
   
   → Returns message_id=42, intent="create_task"

2. EDITH processes intent using core.process
   (This is the existing intent parsing logic)
   
   → Decides: create_task with priority=medium

3. EDITH responds
   Response: "I'll add that as a medium priority task"

4. User corrects (later, via API)
   POST /api/learning/corrections
   {
     "message_id": 42,
     "intent": "create_task",
     "field": "priority",
     "edith_value": "medium",
     "corrected_value": "high",
     "context": "API bug fix"
   }
   
   → Stored in corrections table

5. Pattern analysis (weekly)
   GET /api/learning/patterns/create_task
   
   → Shows: "You correct priority to 'high' 80% of the time"

6. Preference creation
   POST /api/learning/preferences
   {
     "category": "tasks",
     "key": "default_priority",
     "value": "high",
     "learned_from": "inferred",
     "confidence": 0.8
   }

7. Future interactions
   Next time user says "Add a task: ...",
   EDITH checks preferences first,
   suggests high priority automatically.
```

## The Intent Loop

```
User Input
    ↓
core.process.interpret()  ← Intent parsing (LLM-based)
    ↓
core.dispatch.handle_action()  ← Apply the action (knowledge ops)
    ↓
Response + message_id
    ↓
[Optional] User corrects
    ↓
log_correction()  ← Learn from the correction
    ↓
patterns emerge over time
    ↓
preferences learned
    ↓
EDITH gets smarter at predicting what you want
```

## Why This Architecture?

**Separation of Concerns:**
- Chat layer: stateful conversation
- Knowledge layer: facts and relationships
- Learning layer: corrections and patterns
- Services layer: external actions

**Incremental Learning:**
- You don't have to tell EDITH everything
- It learns from patterns in your corrections
- Confidence-based: weak patterns have low confidence

**Natural Evolution:**
- Week 1: Just chatting, no corrections
- Week 2: Start logging corrections
- Week 3: Patterns emerge
- Week 4+: Preferences take shape automatically

**Extensible:**
- New relations? Add a fact. No schema change.
- New preferences? Post them. No code change.
- New services? Register in service_registry. No routing change.

## Next Steps

1. **Test the correction tracking** (Week 1-2)
   - Send messages, get message_id responses
   - Manually log corrections via API
   - See the correction log grow

2. **Analyze patterns** (Week 3)
   - Query `/api/learning/patterns/{intent}`
   - See what you're actually correcting

3. **Create preferences** (Week 4+)
   - Post preferences from patterns
   - Watch EDITH anticipate better

4. **Integrate services** (Future)
   - Add task manager, calendar, etc.
   - EDITH calls them based on intents
   - Same correction → preference loop applies

## Files

- `server/main.py` — FastAPI app setup
- `server/routers/chat.py` — Chat endpoints
- `server/routers/knowledge.py` — Knowledge endpoints
- `server/routers/learning.py` — Learning endpoints
- `memory/store.py` — All database operations
- `core/process.py` — Intent parsing & dispatching
- `LEARNING.md` — Detailed learning system guide
- `SERVER.md` — API documentation
