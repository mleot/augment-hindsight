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

## Best Practices

1. **ALWAYS call recall first** - This is the most important rule
2. **Pass the user's exact query** - Don't paraphrase; use their actual words
3. **Don't skip on "simple" requests** - Context matters even for basic questions
4. **Read ALL results** - Don't just look at the first one
5. **Use memories to inform** - Not just repeat, but apply intelligently
6. **Keep retain working** - The more you retain, the better recall becomes

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

### ✅ Correct Flow
```
User: "How do I add logging?"
You: [call recall_hindsight]
You: [read results]
You: [respond using current request + recalled context]
```

### ❌ Incorrect Flow
```
User: "How do I add logging?"
You: [respond immediately without calling recall]  ← WRONG
```

## Summary

1. **Call `recall_hindsight` on EVERY user message** - No exceptions
2. **Use the user's query as the search query**
3. **Read the results before responding**
4. **Apply relevant memories to your response**
5. **Ignore irrelevant memories**
6. **Never mention you're using memory** unless asked

**The entire purpose of this skill is to make you call recall first, every time.**
