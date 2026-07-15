---
description: "Use when creating or modifying ReactJS UI code, including components, hooks, pages, forms, and client-side state."
name: "ReactJS Standards"
applyTo: ["**/*.jsx"]
---
# ReactJS Standards

- Components: MUST be functional components. Do not use class components.
- Hooks: MUST call hooks only at the top level and only from React components or custom hooks.
- State: MUST keep state as local as possible; lift state only when multiple children need the same source of truth.
- Router: MUST use React Router for client-side routing when routing is needed.
- Global state: MUST use React Context when cross-tree shared state is required; MUST NOT introduce Redux or Zustand unless a separate instruction explicitly allows it.
- Props: MUST keep props explicit and minimal; avoid large pass-through prop chains when composition can be used.
- Effects: MUST use `useEffect` only for side effects (network, subscriptions, timers, DOM integration), not for derived render data.
- Data flow: MUST keep render logic declarative and avoid direct DOM manipulation unless required by a library integration.
- Files: MUST keep one primary component per file and colocate related styles and tests with the component.
- Accessibility: MUST provide semantic HTML and accessible labels for interactive controls.
- Styling: MUST use CSS Modules for component styling. MUST NOT use large inline style objects for component-level styling.
- Testing: MUST use Jest with React Testing Library and MUST add or update component tests for behavior changes.

## Component Example

```jsx
import { useMemo } from 'react';

export default function UserBadge({ user }) {
  const fullName = useMemo(() => `${user.firstName} ${user.lastName}`, [user.firstName, user.lastName]);

  return <span aria-label="user name">{fullName}</span>;
}
```
