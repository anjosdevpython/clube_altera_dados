---
phase: 02-ux-operacional
plan: "02"
subsystem: automation-retry
tags: [ux, retry-button, thread-safety, tkinter]
dependency_graph:
  requires: [02-01]
  provides: [UX-02]
  affects: [CLUBE_modif.py]
tech_stack:
  added: []
  patterns: [root.after(0, _show) for thread-safe UI dispatch, pack_forget on success]
key_files:
  created: []
  modified:
    - "CLUBE_modif.py"
decisions:
  - "mostrar_btn_tentar_novamente() uses root.after(0, _show) internally — same pattern as adicionar_log() — so it is safe to call from background thread iniciar()"
  - "Separator inserted in start_thread() only when log is non-empty, avoiding a separator on first run"
  - "_tentar_novamente_click() hides button synchronously (main thread) before calling start_thread()"
metrics:
  duration: "4m"
  completed: "2026-06-05"
---

# Phase 2 Plan 02: Retry Button and Log Separator Summary

Thread-safe retry button (bootstyle=warning) appears after any Zanthus or CRM failure; clicking it hides the button, shows a timestamped separator in the log, and restarts automation with form fields preserved.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add mostrar_btn_tentar_novamente() + update reset_values() | 3d35129 | CLUBE_modif.py |
| 2 | Separator in start_thread() + 5 failure-point calls | 386cbd4 | CLUBE_modif.py |

## What Was Built

**Task 1 — New methods and reset_values() update:**

- `mostrar_btn_tentar_novamente()`: dispatches button creation to Tkinter main thread via `root.after(0, _show)`; guards against duplicate creation with `hasattr + winfo_exists()`; button uses `bootstyle="warning"` (yellow)
- `_tentar_novamente_click()`: hides button immediately then calls `start_thread()` — no field clearing
- `reset_values()`: added `pack_forget` guard so button disappears on successful operation

**Task 2 — Separator and wiring:**

- `start_thread()`: before the "Iniciando..." log line, checks if log is non-empty and inserts `────────────────── Nova tentativa — HH:MM:SS ──────────────────`
- 5 calls to `self.mostrar_btn_tentar_novamente()` inserted:
  1. `iniciar()` else branch — Zanthus wrong credentials
  2. `iniciar()` except err_zanthus — Zanthus technical error
  3. `iniciar()` except err (change_password) — CRM failure
  4. `iniciar()` except err (change_email) — CRM failure
  5. `iniciar()` except err (change_all) — CRM failure

## Verification Results

```
OK — 5 chamadas de mostrar_btn_tentar_novamente, separador presente
```

- ast.parse() passed — no syntax errors
- 5 calls to mostrar_btn_tentar_novamente() confirmed
- "Nova tentativa" separator present
- root.after(0, _show) thread-safety confirmed
- Log accumulates between retries (no log_text.delete added)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, file access, or schema changes introduced.

## Self-Check: PASSED

- CLUBE_modif.py modified: confirmed (28 total insertions across 2 commits)
- ast.parse() passed: confirmed
- 5 failure-point calls: confirmed
- Separator present: confirmed
- Thread-safety (root.after): confirmed
