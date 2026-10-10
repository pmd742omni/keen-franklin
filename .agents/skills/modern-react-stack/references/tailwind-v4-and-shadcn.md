# Tailwind CSS v4 & shadcn/ui Architecture (2026)

> Technical reference for CSS-first token configuration with Tailwind v4 (Oxide engine) and accessible primitive engineering via shadcn/ui.

---

## 1. Tailwind CSS v4 CSS-First Paradigm

Tailwind v4 replaces JavaScript-based configuration (`tailwind.config.js`) with native CSS `@theme` variables powered by the Rust-based Oxide compiler.

### 1.1 CSS Theme Token Definition
```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-primary-50: oklch(0.97 0.02 260);
  --color-primary-500: oklch(0.60 0.22 260);
  --color-primary-900: oklch(0.25 0.15 260);

  --font-display: 'Cabinet Grotesk', system-ui, sans-serif;
  --font-body: 'Geist', system-ui, sans-serif;

  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
}
```

---

## 2. Accessible shadcn/ui Component Pattern

```tsx
// components/ui/dialog.tsx
'use client';

import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-in fade-in" />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] rounded-lg bg-background p-6 shadow-lg border animate-in zoom-in-95",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100 transition-opacity">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;
```
