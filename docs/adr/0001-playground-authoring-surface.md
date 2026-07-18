---
Status: accepted
---

# Playground is a prompt-authoring surface, not a live chat

The Playground was reworked from a live mock chat (type -> Ctrl+Enter -> mock AI reply) into a static prompt-authoring surface: the Chat panel shows a seed exchange, the input's only action is a disabled "Run Ctrl ↵" button, and Ctrl+Enter is a no-op. Run is intentionally disabled because the execution pipeline isn't built yet; RunSettings configures a future Run. Don't re-add a working send button or mock AI replies - that loop was removed deliberately. Reversing this means redefining what the Playground is for, not just re-adding code.
