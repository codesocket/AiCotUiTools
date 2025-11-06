# 💡 Example Interactions

This document shows real examples of how the LLM intelligently chooses tools.

## 🎨 UI Tool Examples

### Example 1: Simple Theme Change

**User Input:**
```
"Change the theme to purple"
```

**LLM Reasoning:**
```
The user wants to change the UI theme color.
I should use the change_theme_color tool.
```

**Tool Called:**
```json
{
  "name": "change_theme_color",
  "arguments": {
    "color": "purple"
  }
}
```

**Result:**
- UI instantly changes to purple theme
- Header, buttons, and accents update
- User sees visual confirmation

---

### Example 2: Accessibility Request

**User Input:**
```
"I have trouble reading the text, can you make it easier to see?"
```

**LLM Reasoning:**
```
The user is having visibility issues.
This is an accessibility concern.
I should enable high contrast mode to improve readability.
```

**Tool Called:**
```json
{
  "name": "enable_high_contrast",
  "arguments": {
    "enabled": true
  }
}
```

**Result:**
- High contrast mode activates
- Stronger borders, darker text
- Improved readability

---

## 🔧 Backend Tool Examples

### Example 3: Math Calculation

**User Input:**
```
"What's 47 times 89?"
```

**LLM Reasoning:**
```
This is a mathematical calculation.
I'll use the calculator tool to compute this accurately.
```

**Tool Called:**
```json
{
  "name": "calculator",
  "arguments": {
    "expression": "47 * 89"
  }
}
```

**Result:**
```
4183
```

---

### Example 4: Knowledge Search

**User Input:**
```
"Tell me about Python programming"
```

**LLM Reasoning:**
```
The user wants information about Python.
I should search the knowledge base.
```

**Tool Called:**
```json
{
  "name": "search_knowledge",
  "arguments": {
    "query": "python"
  }
}
```

**Result:**
```
Python is a high-level, interpreted programming language...
```

---

### Example 5: Date/Time Query

**User Input:**
```
"What time is it?"
```

**LLM Reasoning:**
```
The user wants the current date and time.
I'll use the get_current_date tool.
```

**Tool Called:**
```json
{
  "name": "get_current_date",
  "arguments": {}
}
```

**Result:**
```
2025-11-04 14:30:45
```

---

## 🎭 Mixed Tool Examples (UI + Backend)

### Example 6: Multi-Tool Request

**User Input:**
```
"Change the theme to teal and calculate 99 * 88"
```

**LLM Reasoning:**
```
This request has two parts:
1. Change UI theme to teal (UI tool)
2. Calculate 99 * 88 (backend tool)

I'll call both tools to fulfill the request.
```

**Tools Called:**
```json
[
  {
    "name": "change_theme_color",
    "arguments": {
      "color": "teal"
    }
  },
  {
    "name": "calculator",
    "arguments": {
      "expression": "99 * 88"
    }
  }
]
```

**Results:**
1. UI changes to teal theme ✅
2. Calculation: 8712 ✅

---

### Example 7: Complex Workflow

**User Input:**
```
"Enable high contrast, make the theme orange, search for AI information, and tell me the date"
```

**LLM Reasoning:**
```
This is a complex request with 4 tasks:
1. Enable high contrast (UI)
2. Change theme to orange (UI)
3. Search for AI (backend)
4. Get current date (backend)

I'll execute all four tools in sequence.
```

**Tools Called:**
```json
[
  {
    "name": "enable_high_contrast",
    "arguments": {"enabled": true}
  },
  {
    "name": "change_theme_color",
    "arguments": {"color": "orange"}
  },
  {
    "name": "search_knowledge",
    "arguments": {"query": "AI"}
  },
  {
    "name": "get_current_date",
    "arguments": {}
  }
]
```

**Results:**
1. High contrast enabled ✅
2. Theme changed to orange ✅
3. AI information retrieved ✅
4. Current date provided ✅

---

## 🤖 Intelligent Tool Selection

### Example 8: Implicit UI Request

**User Input:**
```
"The interface is too blue, I prefer something warmer"
```

**LLM Reasoning:**
```
The user doesn't like the current blue theme.
They want a "warmer" color.
Warm colors include: red, orange, pink.
I'll suggest orange as a warm alternative.
```

**Tool Called:**
```json
{
  "name": "change_theme_color",
  "arguments": {
    "color": "orange"
  }
}
```

**Response:**
```
I've changed the theme to orange, which is a warmer color.
Would you prefer a different warm color like red or pink?
```

---

### Example 9: Contextual Tool Use

**User Input:**
```
"I'm doing math homework. First, what's 15 * 23? Also, can you make the screen easier on my eyes?"
```

**LLM Reasoning:**
```
Two requests here:
1. Math calculation (calculator)
2. Make screen easier on eyes (accessibility → high contrast)

The user is studying, so high contrast will help with extended reading.
```

**Tools Called:**
```json
[
  {
    "name": "calculator",
    "arguments": {
      "expression": "15 * 23"
    }
  },
  {
    "name": "enable_high_contrast",
    "arguments": {
      "enabled": true
    }
  }
]
```

**Results:**
1. 15 * 23 = 345 ✅
2. High contrast enabled for better readability ✅

---

## 🎯 Edge Cases

### Example 10: Ambiguous Request

**User Input:**
```
"Make it green"
```

**LLM Reasoning:**
```
"Make it green" likely refers to the UI theme.
I'll change the theme color to green.
```

**Tool Called:**
```json
{
  "name": "change_theme_color",
  "arguments": {
    "color": "green"
  }
}
```

---

### Example 11: Invalid Color

**User Input:**
```
"Change the theme to yellow"
```

**LLM Reasoning:**
```
The user wants yellow, but that's not in the available colors.
Available: blue, purple, green, red, orange, pink, indigo, teal

The closest match to yellow is orange.
I'll use orange and explain to the user.
```

**Tool Called:**
```json
{
  "name": "change_theme_color",
  "arguments": {
    "color": "orange"
  }
}
```

**Response:**
```
I've changed the theme to orange, which is the closest available color to yellow.
The available theme colors are: blue, purple, green, red, orange, pink, indigo, and teal.
```

---

### Example 12: No Tool Needed

**User Input:**
```
"How does this application work?"
```

**LLM Reasoning:**
```
This is a general question about the app.
No tool execution is needed.
I'll provide an explanation using my knowledge.
```

**Tools Called:**
```
None
```

**Response:**
```
This application demonstrates intelligent tool calling with LLMs.
It connects a React frontend to a FastAPI backend via WebSocket...
```

---

## 📊 Tool Usage Statistics (Typical Session)

```
Session Duration: 15 minutes
Total Messages: 12

Tool Calls:
├─ UI Tools: 5 calls (42%)
│  ├─ change_theme_color: 3
│  └─ enable_high_contrast: 2
│
└─ Backend Tools: 7 calls (58%)
   ├─ calculator: 4
   ├─ search_knowledge: 2
   └─ get_current_date: 1

Multi-tool Requests: 3 (25%)
Average Response Time: 1.2s
```

---

## 🎓 Key Takeaways

1. **Natural Language Understanding**: The LLM understands intent, not just keywords
2. **Multi-Tool Orchestration**: Can execute multiple tools in one request
3. **Contextual Awareness**: Chooses appropriate tools based on context
4. **Fallback Handling**: Gracefully handles unavailable options
5. **Mixed Execution**: Seamlessly combines UI and backend tools

---

**Try these examples yourself to see the magic! 🪄**
