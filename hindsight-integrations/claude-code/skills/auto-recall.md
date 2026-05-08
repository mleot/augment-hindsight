---
name: hindsight:auto-recall
description: Always use Hindsight recall_hindsight tool FIRST before processing any user request to gather relevant context from past conversations, decisions, and preferences. Call this tool proactively on every user message.
---

# Hindsight Auto-Recall

This skill ensures you **always** use Hindsight's recall functionality to gather relevant context before responding to user requests.

## Core Principle

**ALWAYS call `recall_hindsight` FIRST, before thinking or responding to any user request.**

This is not optional. This is not only for certain types of requests. This is **EVERY SINGLE TIME**.

## Workflow for Every User Request

```
1. User sends message
2. YOU call recall_hindsight(query=<user's request>, max_tokens=1024, budget="mid")
3. Read the recalled memories
4. THEN formulate your response using both current request + recalled context
5. Respond to user
```

## When to Call Recall

**ALWAYS** - Call `recall_hindsight` on:
- ✅ Every user question
- ✅ Every code request
- ✅ Every debugging task
- ✅ Every explanation request
- ✅ Every "how do I..." question
- ✅ Every follow-up message
- ✅ Every new topic
- ✅ Literally every single user message

**NEVER skip recall** - Even if the request seems simple or unrelated to past work.

## How to Call Recall

Use the `recall_hindsight` MCP tool:

```python
recall_hindsight(
    query="<user's request or question>",
    max_tokens=1024,
    budget="mid",
    types=["world", "experience"]
)
```

### Example Calls

**User asks:** "How do I add a new endpoint to the API?"

**You call first:**
```
recall_hindsight(
    query="How do I add a new endpoint to the API?",
    max_tokens=1024,
    budget="mid"
)
```

**Then use the results** to see if:
- User has API endpoint patterns already established
- User prefers certain frameworks or approaches
- There are existing examples in their codebase
- User has preferences about routing, validation, etc.

## Recalled Memory Format

Memories are returned as a list of results:

```json
{
  "results": [
    {
      "text": "User prefers functional programming patterns over OOP",
      "type": "experience",
      "mentioned_at": "2024-03-15T10:30:00Z",
      "score": 0.92
    },
    {
      "text": "Project uses FastAPI with Pydantic v2 for validation",
      "type": "world",
      "mentioned_at": "2024-03-14T15:20:00Z",
      "score": 0.88
    }
  ]
}
```

### Guidelines for Using Memories

1. **CALL RECALL FIRST** - Before any thinking, before any response
2. **Prioritize recalled memories** when they're relevant to the current request
3. **Resolve conflicts** by preferring recent memories over old ones (higher `mentioned_at` timestamps)
4. **Ignore irrelevant memories** - not every memory applies to every request
5. **Don't mention the memory system** unless directly asked
6. **Use memories naturally** - incorporate them into your response without saying "I recall that..."
7. **Check the score** - Higher scores (>0.8) are more relevant

## Memory Types

| Type | Description | Example |
|------|-------------|---------|
| `[world]` | General facts and knowledge | "The project uses Python 3.11" |
| `[experience]` | User's personal experiences and actions | "User previously fixed a similar bug in auth.py" |
| `[opinion]` | User's preferences and opinions | "User prefers pytest over unittest" |

## When Memories Are Most Valuable

- **Continuing previous work** - Recall helps you pick up where you left off
- **Applying user preferences** - Use preferred tools, patterns, languages
- **Avoiding repeated mistakes** - Don't suggest approaches that failed before
- **Understanding context** - Project structure, tech stack, team conventions
- **Personalization** - Adapt to user's working style and communication preferences

## Recall Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | *required* | The user's request or relevant question |
| `max_tokens` | `1024` | Max tokens for recalled memories (increase for more context) |
| `budget` | `"mid"` | Search effort: `"low"` (fast), `"mid"` (balanced), `"high"` (thorough) |
| `types` | `["world", "experience"]` | Memory types: `"world"`, `"experience"`, `"opinion"` |

## Advanced: Reflect for Deeper Analysis

For complex questions that need synthesized insights, use `reflect_hindsight`:

```python
reflect_hindsight(
    query="What architectural patterns does the user prefer based on past projects?",
    max_tokens=4096,
    budget="low"
)
```

**When to use reflect vs recall:**
- **Recall**: Retrieve specific facts → "What did the user say about X?"
- **Reflect**: Synthesize patterns → "Based on past work, what approach should I take?"

Use `recall_hindsight` by default. Use `reflect_hindsight` when you need reasoning across multiple memories.

## Manual Retain: Close the Knowledge Loop

When you recall and find **no answer** or **incomplete information**, but then **learn the answer** during the conversation, you should **manually retain** that new knowledge.

### The Pattern: Learn-Then-Retain

```
1. User asks a question
2. You call recall_hindsight (no relevant memories found)
3. You and user figure out the answer together
4. You NOW KNOW the answer → Call retain_hindsight to store it
```

### When to Manually Retain

**ALWAYS retain when:**
- ✅ Recall returned no results, and you learned the answer
- ✅ Recall returned outdated info, and you discovered the current answer
- ✅ User taught you a preference or pattern
- ✅ You discovered an important project fact (tech stack, architecture, etc.)
- ✅ User corrected you or provided clarification
- ✅ You solved a problem that wasn't in memory

**DON'T retain:**
- ❌ General knowledge or common facts
- ❌ Temporary information (today's weather, current time)
- ❌ Information that's already in recalled memories
- ❌ Routine confirmations or small talk

### How to Manually Retain

Use the `retain_hindsight` or `sync_retain_hindsight` MCP tool:

```python
# Synchronous (waits for completion)
sync_retain_hindsight(
    content="<what you learned>",
    context="learned-from-conversation",
    metadata={"learned_from": "user_explanation"}
)

# Or asynchronous (returns immediately)
retain_hindsight(
    content="<what you learned>",
    context="learned-from-conversation"
)
```

### Example: Learn-Then-Retain Flow

**User asks:** "What's our preferred logging library?"

**You call recall:**
```python
recall_hindsight(
    query="What's our preferred logging library?",
    max_tokens=1024
)
# Returns: [] (no results)
```

**Conversation continues:**
```
You: "I don't have that information stored. What logging library do you prefer?"
User: "We use structlog for all our Python services"
You: "Got it, I'll remember that."
```

**NOW YOU RETAIN:**
```python
sync_retain_hindsight(
    content="User's team uses structlog as the preferred logging library for Python services",
    context="user-preference",
    metadata={"topic": "logging", "language": "python"}
)
```

**Next time:** When someone asks about logging, recall will return this memory!

### What to Include in Manual Retains

Write retains as **clear, factual statements**:

✅ **Good retains:**
- "User prefers pytest over unittest for Python testing"
- "Project uses FastAPI with Pydantic v2 for API validation"
- "Team convention: use absolute imports, not relative imports"
- "Database connection pool is configured in config/db.py"

❌ **Bad retains:**
- "We talked about testing" (too vague)
- "The user said something about imports" (not specific)
- "I helped with the database" (not factual)

### Retain Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `content` | What you learned (required) | "User prefers functional over OOP" |
| `context` | Why/how you learned it | `"user-preference"`, `"discovered"`, `"correction"` |
| `metadata` | Additional structured data | `{"topic": "testing", "language": "python"}` |
| `tags` | Optional tags for filtering | `["project:myapp", "preference"]` |
| `timestamp` | When learned (ISO format) | `"2024-05-08T10:30:00Z"` (optional, auto-set) |

### Use Sync vs Async Retain

- **`sync_retain_hindsight`**: Waits for completion, confirms storage
- **`retain_hindsight`**: Returns immediately, processes in background

Use `sync_retain_hindsight` when:
- The information is critical
- You want to confirm it was stored
- You're about to use it in the next response

Use `retain_hindsight` when:
- It's supplementary information
- Speed matters more than confirmation
- You're retaining multiple things at once

## Best Practices

1. **ALWAYS call recall first** - This is the most important rule
2. **Pass the user's exact query** - Don't paraphrase; use their actual words
3. **Don't skip on "simple" requests** - Context matters even for basic questions
4. **Read ALL results** - Don't just look at the first one
5. **Use memories to inform** - Not just repeat, but apply intelligently
6. **Close the knowledge loop** - When recall fails but you learn the answer, retain it
7. **Retain new discoveries** - User preferences, corrections, project facts
8. **Write clear retains** - Make them specific, factual, and useful for future recall

## Troubleshooting

**No memories returned?**
- This is normal for new users or new projects
- Verify Hindsight MCP server is connected (check available tools)
- Continue with your response using current context only

**Too many irrelevant memories?**
- Reduce `max_tokens` to get fewer, more relevant results (try `512`)
- Lower `budget` to `"low"` for faster but more focused search
- Check if memories are actually irrelevant or just unexpected context

**Tool call fails?**
- Verify Hindsight MCP server is running
- Check that `recall_hindsight` is in your available tools
- Fall back to responding without recalled context

## Critical Reminders

### ⚠️ YOU MUST CALL RECALL FIRST

This is not a suggestion. This is not optional. This is **mandatory**.

**Every user message = Call `recall_hindsight` first**

### ✅ Correct Flow with Recall
```
User: "How do I add logging?"
You: [call recall_hindsight]
You: [read results]
You: [respond using current request + recalled context]
```

### ✅ Correct Flow with Learn-Then-Retain
```
User: "What's our API authentication pattern?"
You: [call recall_hindsight → no results]
You: "I don't have that information. What pattern do you use?"
User: "We use JWT tokens with refresh rotation"
You: [call sync_retain_hindsight to store this]
You: "Got it, I'll remember that for next time."
```

### ❌ Incorrect Flow
```
User: "How do I add logging?"
You: [respond immediately without calling recall]  ← WRONG

User: "We use JWT authentication"
You: "Thanks!" [but don't retain it]  ← WRONG, you should retain this
```

## Summary

### Core Workflow

1. **Call `recall_hindsight` on EVERY user message** - No exceptions
2. **Use the user's query as the search query**
3. **Read the results before responding**
4. **Apply relevant memories to your response**
5. **Ignore irrelevant memories**

### Close the Knowledge Loop

6. **When recall returns no answer** - Note that you don't have this information
7. **When you learn the answer** - Through user explanation, code exploration, or problem-solving
8. **Call `sync_retain_hindsight`** - Store the new knowledge for future recall
9. **Write clear, specific content** - Make it useful for next time

### What This Achieves

- **First conversation**: You ask questions, user teaches you → You retain
- **Later conversations**: You recall those learnings → You already know
- **Continuous improvement**: Every gap filled becomes future knowledge
- **Personalization**: You remember user's preferences, patterns, and context

**The entire purpose of this skill is to:**
1. **Always recall first** to use existing knowledge
2. **Always retain new learnings** to build future knowledge

This creates a virtuous cycle where Hindsight gets smarter with every conversation.
