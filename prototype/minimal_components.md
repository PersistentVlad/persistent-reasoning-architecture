# Minimal Components

This document describes the **minimal set of components** required to demonstrate executable persistent reasoning.

Each component exists to enforce a boundary.
No component exists to increase capability.

---

## Component Overview

The prototype consists of exactly six conceptual components:

1. Persistent Store  
2. Write Barrier  
3. Proposal Engine  
4. Commit Gate  
5. Inference Stub  
6. Execution Loop  

Removing any component collapses the architecture.
Adding components risks erosion.

---

## 1. Persistent Store

### Role
Holds persistent reasoning structures.

### Properties
- append-only,
- versioned,
- non-queryable,
- immutable per version.

### Explicit Non-Properties
- no evaluation,
- no satisfaction checking,
- no search,
- no optimization.

The store preserves identity, not answers.

---

## 2. Write Barrier

### Role
The **only** point where persistent structures may change.

### Properties
- validates revisions,
- enforces constraints,
- rejects implicit mutation.

The write barrier is the architectural center of gravity.

---

## 3. Proposal Engine

### Role
Generates candidate revisions.

### Properties
- stateless,
- replaceable,
- non-authoritative.

The proposal engine has no memory.
It has no ownership.

---

## 4. Commit Gate

### Role
Decides whether a proposal becomes persistent.

### Properties
- explicit,
- deliberate,
- governed.

The commit gate is where persistence earns the right to survive.

---

## 5. Inference Stub

### Role
Simulates reasoning activity.

### Properties
- intentionally weak,
- deliberately simple,
- non-optimizing.

Its purpose is not to reason well,
but to demonstrate repeated inference without identity loss.

---

## 6. Execution Loop

### Role
Coordinates interaction between components.

### Properties
- deterministic,
- sequential,
- transparent.

The execution loop makes persistence observable over time.

---

## What Is Intentionally Missing

The following are deliberately absent:

- LLMs
- embeddings
- vector databases
- planners
- solvers
- reward functions
- learning algorithms

Their absence is not a limitation.
It is a guardrail.

---

## Minimality Principle

> **Every component must justify its existence by enforcing a boundary.**

If a component exists only to improve capability,
it does not belong in this prototype.

---

## Final Note

This component set is not sufficient to build a useful system.

It is sufficient to demonstrate one thing:

> **Persistent reasoning is architecturally possible — but only under severe constraint.**

That constraint is the message.
