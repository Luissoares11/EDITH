# EDITH Learning System

This document explains how EDITH learns from corrections and builds preferences over time.

## The Learning Flow

```
User sends message
         ↓
   EDITH responds
         ↓
   User corrects EDITH (optional)
         ↓
   Correction logged to database
         ↓
   Patterns analyzed from corrections
         ↓
   Preferences learned/inferred
         ↓
   Next time: EDITH uses learned preferences
```

## Step-by-Step Example: Learning Task Priorities

### 1. Initial Interaction (No Learning Yet)

```bash
POST /api/chat/message
{
  "message": "Add: Prepare quarterly report",
  "session_id": "default"
}

Response:
{
  "message_id": 42,
  "response": "I'll add that as a task.",
  "ok": true,
  "intent": "create_task"
}
```

EDITH guesses a default priority (let's say "medium"). You realize it should be "high" for work.

### 2. Log the Correction

```bash
POST /api/learning/corrections
{
  "message_id": 42,
  "intent": "create_task",
  "field": "priority",
  "edith_value": "medium",
  "corrected_value": "high",
  "context": "quarterly report"
}

Response:
{
  "correction_id": 1
}
```

This is stored in the `corrections` table — the raw signal that EDITH got priority wrong.

### 3. Repeat (Build a Pattern)

You add more tasks:
- "Schedule team meeting" → EDITH: "low", You: "high" (correction #2)
- "Update personal blog" → EDITH: "high", You: "low" (correction #3)
- "Prepare presentation" → EDITH: "medium", You: "high" (correction #4)
- "Buy groceries" → EDITH: "medium", You: "low" (correction #5)

### 4. Analyze Patterns

```bash
GET /api/learning/patterns/create_task

Response:
{
  "intent": "create_task",
  "total_corrections": 5,
  "patterns": [
    {
      "field": "priority",
      "most_corrected_to": "high",
      "frequency": 3,
      "total_corrections": 5
    }
  ]
}
```

The pattern emerges: **for task creation, you correct priority to "high" 60% of the time.**

### 5. Create a Preference

Based on this pattern, EDITH (or you) can infer a preference:

```bash
POST /api/learning/preferences
{
  "category": "tasks",
  "key": "default_priority",
  "value": "high",
  "learned_from": "inferred",
  "confidence": 0.6
}

Response:
{
  "preference_id": 7
}
```

This says: "For tasks, the default priority is high, and I'm 60% confident because that's what Luis corrects to most often."

### 6. Apply the Learning

Next time you add a task:

```bash
POST /api/chat/message
{
  "message": "Add: Review project proposal",
  "session_id": "default"
}

Response:
{
  "message_id": 43,
  "response": "I'll add that as high priority.",
  "ok": true,
  "intent": "create_task"
}
```

Now EDITH checks its preferences first and suggests "high" automatically—because it learned from your corrections.

### 7. Confirm or Refine

If EDITH got it right:
```bash
POST /api/learning/preferences/tasks/default_priority/confirm
# Confidence goes to 1.0
```

If it got it wrong:
```bash
POST /api/learning/corrections
{
  "message_id": 43,
  "intent": "create_task",
  "field": "priority",
  "edith_value": "high",
  "corrected_value": "medium",
  "context": "project proposal"
}
# Confidence drops; pattern is re-analyzed
```

## API Reference

### Recording Corrections

**POST** `/api/learning/corrections`

```json
{
  "message_id": 42,          // From the chat message response
  "intent": "create_task",   // What EDITH was doing
  "field": "priority",       // What field was wrong
  "edith_value": "medium",   // What EDITH suggested
  "corrected_value": "high", // What you changed it to
  "context": "quarterly report"  // Optional context for pattern matching
}
```

### Viewing Corrections

**GET** `/api/learning/corrections?intent=create_task&limit=100`

Returns all logged corrections, optionally filtered.

### Finding Patterns

**GET** `/api/learning/patterns/{intent}`

Example: `/api/learning/patterns/create_task`

Returns:
```json
{
  "intent": "create_task",
  "total_corrections": 15,
  "patterns": [
    {
      "field": "priority",
      "most_corrected_to": "high",
      "frequency": 12
    }
  ]
}
```

### Managing Preferences

**POST** `/api/learning/preferences` — Create a preference
```json
{
  "category": "tasks",
  "key": "default_priority",
  "value": "high",
  "learned_from": "explicit",  // or "inferred"
  "confidence": 1.0
}
```

**GET** `/api/learning/preferences?category=tasks` — List preferences

**GET** `/api/learning/preferences/tasks/default_priority` — Get one preference

**POST** `/api/learning/preferences/tasks/default_priority/confirm` — Confirm an inferred preference

**DELETE** `/api/learning/preferences/tasks/default_priority` — Remove a preference

## Real-World Strategy

### Phase 1: Track Corrections (Week 1-2)
- Use EDITH normally
- Log corrections whenever EDITH gets something wrong
- Don't worry about preferences yet — just collect data

```bash
# Run this whenever you correct EDITH
POST /api/learning/corrections
{
  "message_id": <from response>,
  "intent": "<the action>",
  "field": "<what was wrong>",
  "corrected_value": "<what you changed it to>",
  "context": "<relevant details>"
}
```

### Phase 2: Analyze Patterns (Week 3)
- Check what patterns are emerging

```bash
GET /api/learning/patterns/create_task
GET /api/learning/patterns/schedule_meeting
# etc.
```

### Phase 3: Create Preferences (Week 4+)
- For strong patterns (80%+ frequency), create preferences
- Mark as "inferred" with confidence matching the frequency
- Start applying them

```bash
POST /api/learning/preferences
{
  "category": "tasks",
  "key": "work_priority",
  "value": "high",
  "learned_from": "inferred",
  "confidence": 0.8
}
```

### Phase 4: Iterate
- As EDITH uses preferences, correct it when it guesses wrong
- Confidence updates automatically from new corrections
- Preferences evolve over time

## The Point

This system lets EDITH learn *your* patterns without you having to explicitly program them. It's not magic pattern-matching—it's honest signal: **what do you actually correct me to, and how often?**

Over weeks and months, EDITH gets better at anticipating your preferences because it's learning from real data: your corrections.
