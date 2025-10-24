CHECK_EXISTING_KNOWLEDGE_PROMPT = """
**Two response modes**
**A. Relevant context found** – If the context lets you answer the user’s question:

1. Give a concise, one-sentence answer.
2. Provide a well-structured explanation (paragraphs or bullet points).
3. Cite every fact with the rules below.

**B. No relevant context** – If the context does **not** answer the question:

1. On its own line type exactly **“you don’t know”** (lower-case, no period).
2. Add a brief **“Context Summary”** section that objectively summarizes what *is* in the context.
3. Add a **“Why Insufficient”** section explaining why the context cannot answer the user’s question.
4. Use citations for both sections.

**Citation rules**
• Treat every `source:` occurrence in the `context` as a unique citation anchor.
• Number chunks in order of appearance: `[1]`, `[2]`, …
• Append the number(s) after each sentence that uses information from that chunk.

**User request:**

```text
{query}
```

**Assistant response format:**
*Follow the mode A or B template above.*
*Do not introduce external knowledge or speculation.*

**Context:**

```text
{context}
```
"""
