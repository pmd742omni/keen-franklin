# AI SDK & Vector RAG Integration in Web Applications (2026)

> Technical reference for integrating real-time streaming LLM responses, tool calls, and PostgreSQL pgvector RAG pipelines into web applications.

---

## 1. Streaming LLM Responses with Vercel AI SDK & Local Ollama

The Vercel AI SDK (`ai`) standardizes streaming protocols over HTTP Server-Sent Events (SSE) across client and server components:

```tsx
// app/api/chat/route.ts (Next.js App Router)
import { createOpenAI } from '@ai-sdk/openai';
import { streamText } from 'ai';

// Connect to local open-source Ollama endpoint
const ollama = createOpenAI({
  baseURL: 'http://localhost:11434/v1',
  apiKey: 'ollama', // Unauthenticated local daemon
});

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: ollama('llama3.2'),
    messages,
    system: 'You are an expert fullstack software architect assistant.',
  });

  return result.toDataStreamResponse();
}
```

Client Hook Consumption:
```tsx
// components/ChatWindow.tsx
'use client';

import { useChat } from 'ai/react';

export function ChatWindow() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();

  return (
    <div className="flex flex-col h-[500px] border rounded-lg p-4">
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div key={m.id} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className="inline-block p-2 rounded-lg bg-muted text-sm">{m.content}</span>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 mt-4">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Ask a question..."
          className="flex-1 border rounded px-3 py-2 text-sm"
        />
        <button type="submit" disabled={isLoading} className="btn-primary text-sm px-4">
          Send
        </button>
      </form>
    </div>
  );
}
```

---

## 2. Retrieval-Augmented Generation (RAG) with `pgvector`

```ts
// lib/rag.ts
import { db } from '@/db';
import { documentChunks } from '@/db/schema';
import { cosineDistance, desc, sql } from 'drizzle-orm';

export async function findRelevantChunks(queryEmbedding: number[], limit = 5) {
  const similarity = sql<number>`1 - (${cosineDistance(documentChunks.embedding, queryEmbedding)})`;

  return await db
    .select({
      id: documentChunks.id,
      content: documentChunks.content,
      similarity,
    })
    .from(documentChunks)
    .where(sql`${similarity} > 0.75`)
    .orderBy(desc(similarity))
    .limit(limit);
}
```
