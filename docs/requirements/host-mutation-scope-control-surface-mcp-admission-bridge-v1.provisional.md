# Provisional Requirement — Host Mutation Scope Control Surface & MCP Admission Bridge V1

> Provisional transport bootstrap only. This file exists only until GitHub allocates the canonical PR-backed Task ID.

## Problem

`SX-HMSA-001` implemented provider-owned `host_mutation_sandbox_v1` scope authority and scoped `script_run`, but the Host Agent exposes no routable operation that lets an authorized control plane provision/revalidate/read back that provider-owned scope before scoped execution.

The result is a control-plane dead end: capability self-check can pass, but ChatGPT/DevForge cannot lawfully obtain `workspace_id` / `mutation_scope_ref` without inventing caller-owned authority.

## Goal

Expose the existing provider-owned mutation-scope lifecycle through a bounded Agent operation and define a safe admission path usable through SentinelX's existing generic Hub operation relay, without weakening scope ownership, AppContainer enforcement, audit ordering, or terminalization semantics.

## Core Constraints

- `provision_scope` remains the only producer of `workspace_id` and mutation scope identity.
- Caller-supplied workspace/write-root/protected-root authority remains forbidden.
- Scope operations must bind exact repository + project/task/run/attempt[/slice] identity.
- Scoped execution must remain fail-closed and must never fall back to unrestricted execution.
- The open-source Agent repository does not own the closed-source Hub/MCP schema; V1 must not claim a dedicated MCP tool unless live Hub evidence proves it exists.
- V1 may use the already-existing generic Hub `/op` relay as the bridge, provided end-to-end admission is verified.
- No material implementation is authorized before Plan Review approval.
