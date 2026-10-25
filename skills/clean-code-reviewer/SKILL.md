---
name: clean-code-reviewer
description: Systematic code quality and architectural cleanliness reviewer. Use when reviewing code changes, auditing codebases for anti-patterns, or refactoring components.
---

# Clean Code Reviewer Skill

This skill guides the agent in conducting thorough, constructive, and actionable code reviews.

---

## Review Checklist

1. **Readability & Intent**
   - Are variable and function names descriptive and aligned with domain concepts?
   - Is logic split into small, understandable functions?
   - Are magic numbers and hardcoded strings replaced with constants?

2. **Architecture & Boundaries**
   - Are concerns separated cleanly (presentation vs business logic vs persistence)?
   - Are dependencies injected rather than hard-wired where appropriate?
   - Is unnecessary coupling avoided?

3. **Error Handling & Robustness**
   - Are exceptions handled gracefully with appropriate recovery or logging?
   - Are edge cases (nulls, empty collections, invalid inputs) checked explicitly?

4. **Testing & Maintainability**
   - Are changes accompanied by tests?
   - Do tests assert specific behavior rather than trivial implementation details?

---

## Review Output Format

Provide feedback grouped into:
- 🌟 **Strengths**: What is well-designed.
- ⚠️ **Key Recommendations**: Prioritized suggestions with concrete before/after code snippets.
- 💡 **Questions / Discussion Points**: Nuanced trade-offs requiring user input.
