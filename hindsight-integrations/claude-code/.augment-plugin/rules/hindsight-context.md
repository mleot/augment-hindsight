---
description: Proactively check Hindsight for user context, preferences, and past decisions to provide personalized responses.
alwaysApply: true
---

# Hindsight Memory Context

## When to Check Hindsight

Proactively use the `recall` tool from the Hindsight MCP server when additional context would be helpful:

### Always Check For:
- **User preferences** - coding style, tools, frameworks, languages
- **Project context** - what the user is working on, project goals, architecture decisions
- **Past decisions** - why certain approaches were chosen or avoided
- **User background** - experience level, domain expertise, learning goals
- **Workflow patterns** - how the user prefers to work, testing approaches, commit patterns

### Examples:

**Before suggesting tools or approaches:**
```
User: "I need to set up a new Python project"
→ Check: recall("Python project setup preferences tools")
→ Might learn: User prefers uv, Python 3.12, specific project structure
```

**When answering technical questions:**
```
User: "How should I handle authentication?"
→ Check: recall("authentication approach preferences security")
→ Might learn: User's security requirements, preferred auth libraries, past implementations
```

**When starting work on a project:**
```
User: "Let's continue working on the battery model"
→ Check: recall("battery model project PyBaMM goals")
→ Might learn: Project name, specific goals, architecture, previous work
```

**When the user asks about their own work:**
```
User: "What was I working on yesterday?"
→ Check: recall("recent work projects tasks")
```

## How to Use Recall

Use the `recall` tool with a descriptive query:

```json
{
  "name": "recall",
  "arguments": {
    "query": "Python project setup preferences and tools",
    "budget": "low"
  }
}
```

### Budget Levels:
- `"low"` - Fast, 5-10 memories (default, use this most of the time)
- `"medium"` - Balanced, 10-20 memories (when you need more context)
- `"high"` - Thorough, 20+ memories (complex questions requiring deep context)

## When NOT to Check

- **Don't spam recall** - Only check once per conversation turn at most
- **Don't recall for simple factual questions** - If you already know the answer
- **Don't recall when context is already provided** - If the user gave you all the info you need

## Integration with Work

After recalling relevant context:
1. **Use it to personalize responses** - Match the user's style and preferences
2. **Reference past decisions** - "Last time we discussed this, you preferred..."
3. **Build on previous work** - Continue from where you left off
4. **Avoid suggesting what didn't work** - Learn from past failed approaches

## Example Workflow

```
User: "Help me write tests for the battery simulation"

1. Recall context:
   recall("battery simulation project testing preferences")

2. Response based on memories:
   "I see you're working on PyBaMM battery modeling. Based on your 
   preferences, I'll use pytest with markers for slow tests..."
```

---

**Remember**: Hindsight recall helps you be a more personalized, context-aware assistant. Use it to avoid asking the user to repeat information they've already shared.
