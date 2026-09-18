# Jev for Piximi

Read README.md before editing.
Keep the loop small: page -> indexed elements -> operation + target -> execution.

- The input is one natural-language goal.
  Piximi workflow guidance belongs in questions.py; never hardcode user field values or click sequences.
- TypeSafe chooses an operation and operation-specific target heads in one request.
  Consume only the selected operation's target.
- Targets must map to observed elements and supported operations.
  Never let the model emit selectors or executable code.
- TYPE_TEXT invokes the text LLM.
  Cache a stale retry's value only while its entire helper input is identical.
- Never retry a browser mutation.
  Log execution before observing its result.
- Screenshots are optional; the model does not consume them.
  Keep demonstration footage at its original speed.
- Keep credentials server-side and .env ignored.
  Tests must not call paid APIs.
- Verify actual final outcomes independently.
  A DONE choice is not proof of success.
- Keep examples, README claims, raw evidence, and model-call counts consistent.
- Do not commit or push unless the user requests it.

Checks: uv run ruff check ., uv run pytest, node --check jev_ultrafast/static/app.js, uv build.

## TypeSafe skill

Use `.agents/skills/typesafe-ai/SKILL.md` for TypeSafe/Jev work.
Install the project-local skill with:

```bash
npx skills@1.5.20 add typesafe-ai/skills --skill typesafe-ai -a codex -a claude-code -y
```

Track `skills-lock.json`; the installer owns the ignored skill directory and Claude symlink.
