---
name: hindsight:auto-recall
description: Always use Hindsight recall before processing user requests to gather relevant context from past conversations, decisions, and preferences. This skill is automatically applied by the UserPromptSubmit hook.
---

# Hindsight Auto-Recall

This skill ensures you **always** use Hindsight's recall functionality to gather relevant context before responding to user requests.

## Core Principle

**ALWAYS recall memories BEFORE thinking or responding to any user request.**

The recall happens automatically via the `UserPromptSubmit` hook, which injects relevant memories into the conversation context. You should treat these memories as high-priority context.

## How Auto-Recall Works

1. **User submits a prompt** → Triggers `UserPromptSubmit` hook
2. **Hook calls `recall.py`** → Queries Hindsight for relevant memories
3. **Memories are injected** → Added to your context in `<hindsight_memories>` tags
4. **You respond** → Using both current request and recalled memories

## Using Recalled Memories

Recalled memories appear in your context like this:

```xml
<hindsight_memories>
Relevant memories from past conversations (prioritize recent when conflicting). 
Only use memories that are directly useful to continue this conversation; ignore the rest:

- User prefers functional programming patterns over OOP [experience] (2024-03-15)
- Project uses TypeScript with strict mode enabled [world] (2024-03-14)
- User is working on a React application with Next.js [experience] (2024-03-10)
</hindsight_memories>
```

### Guidelines for Using Memories

1. **Prioritize recalled memories** when they're relevant to the current request
2. **Resolve conflicts** by preferring recent memories over old ones
3. **Ignore irrelevant memories** - not every memory applies to every request
4. **Don't mention the memory system** unless directly asked
5. **Use memories naturally** - incorporate them into your response without saying "I recall that..."

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

## Recall Configuration

The recall behavior is controlled by `settings.json`:

```json
{
  "autoRecall": true,
  "recallBudget": "mid",
  "recallMaxTokens": 1024,
  "recallTypes": ["world", "experience"],
  "recallContextTurns": 1,
  "recallMaxQueryChars": 800
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `autoRecall` | `true` | Enable/disable automatic recall |
| `recallBudget` | `"mid"` | Search effort: `"low"`, `"mid"`, `"high"` |
| `recallMaxTokens` | `1024` | Max tokens for recalled memories |
| `recallTypes` | `["world", "experience"]` | Memory types to include |
| `recallContextTurns` | `1` | Number of recent conversation turns to include in query |

## Manual Recall (MCP Tools)

In addition to auto-recall, you can also manually query memories using MCP tools:

### `recall_hindsight`
Query memories for specific information:
```
recall_hindsight(
  query="What are the user's Python testing preferences?",
  max_tokens=2048,
  budget="high"
)
```

### `reflect_hindsight`
Get synthesized analysis from memories:
```
reflect_hindsight(
  query="What architectural patterns does the user prefer based on past projects?",
  max_tokens=4096
)
```

## Best Practices

1. **Trust the auto-recall** - The hook already ran; memories are in context
2. **Don't ignore memories** - They're injected for a reason
3. **Use manual recall sparingly** - Only when you need deeper context than auto-recall provides
4. **Keep retain working** - The more you retain, the better recall becomes
5. **Monitor recall quality** - If memories seem off-topic, the query construction may need tuning

## Troubleshooting

**No memories appearing?**
- Check `autoRecall: true` in settings.json
- Verify Hindsight API is reachable (`hindsightApiUrl`)
- Look for `[Hindsight]` debug logs if `debug: true`

**Too many irrelevant memories?**
- Reduce `recallMaxTokens` to get fewer, more relevant results
- Lower `recallBudget` to `"low"` for faster but less thorough search
- Adjust `recallTypes` to exclude opinion if you only want facts

**Memories from wrong project?**
- Check that `bankId` is unique per project if using `dynamicBankId: true`
- Review tags to ensure proper filtering (e.g., by session, computer, user)

## Summary

**You don't need to do anything special** - auto-recall happens automatically on every user request. Just:

1. ✅ Read the `<hindsight_memories>` in your context
2. ✅ Use relevant memories when responding
3. ✅ Ignore memories that don't apply
4. ✅ Continue working naturally

The system handles recall timing and query construction automatically.
