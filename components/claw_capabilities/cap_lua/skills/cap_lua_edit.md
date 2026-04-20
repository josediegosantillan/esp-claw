# Lua Script Editing

Use this skill when the user wants to create or modify a Lua script.

## Fast path (save turns and wall-clock time)

1. **Activate only what you need** — In one batch, activate `cap_lua_patterns` plus each `lua_module_*` the script will `require`. **Do not** activate `board_hardware_info` unless GPIO/wiring is unknown or the user asks for hardware discovery; extra skills inflate Active Skill Docs and slow each turn.
2. **Reuse before author** — Call `lua_list_scripts` once; if a listed file is close, read it with `read_file` (see **Reading Lua files below**) and edit instead of authoring from scratch.
3. **Start from shipped skeletons** — For button + WeChat notify, base edits on `temp/wechat_button_notify_skeleton.lua` (or `button_demo.lua` for button-only), using the **`read_file` path** form below. Do not invent a new layout when a demo already matches.
4. **IM replies from Lua** — Prefer `ep.publish_message("text")` (string only). Table form **must** include `source_cap` and `text`; partial tables fail in button callbacks. See `lua_module_event_publisher`.
5. **Iterate one path** — Prefer `lua_write_script` → `lua_run_script_async` with the **same** `temp/*.lua` path across revisions instead of creating `temp/foo2.lua`, `temp/foo3.lua`, …

### Reading Lua files (`read_file` vs `lua_list_scripts`)

- `lua_list_scripts` returns paths **relative to the Lua script root** (e.g. `button_demo.lua`, `temp/wechat_button_notify_skeleton.lua`).
- The `read_file` tool is rooted at the **FATFS mount** (e.g. `/fatfs`), while the Lua root is **`/fatfs/scripts`**. So you **must not** pass the bare `lua_list_scripts` string to `read_file` — that resolves to `/fatfs/...` and **fails**.
- **Correct:** prefix with `scripts/`: `read_file` path = `scripts/` + *exactly* the string from `lua_list_scripts` (e.g. `scripts/button_demo.lua`, `scripts/temp/wechat_button_notify_skeleton.lua`).

## Sprint 1 — Lua runtime (C) is frozen

The following is **already in firmware** (see improvement report **P2-13** and Lua quality baseline). **Do not ask for ad-hoc Lua C changes** in routine tasks; open a **new sprint** if the runtime itself must change.

| Area | Behavior |
|------|------------|
| Timeout / WDT | `lua_sethook` + wall-clock deadline + `taskYIELD` so busy Lua loops do not starve the IDLE task |
| Tool `args` | JSON whole numbers map to Lua integers where lossless |
| Agent + IM | When the tool is invoked from a chat session, missing `channel` / `chat_id` / `session_id` may be merged into global `args` |
| `event_publisher` | `publish_message` — **prefer string** `ep.publish_message("hi")`; table form needs **`source_cap` + `text`** (and channel/chat_id if not in `args`). Dot syntax, not colon |

**Iteration surface from here:** this skill, `cap_lua_patterns`, `cap_lua_run`, and scripts under **`temp/`** / **`user/`** plus shipped demos — **not** new C unless scheduled.

## Workflow (keep cloud layout)

- Before writing or revising Lua code, use `board_hardware_info` **only when** you need discovered GPIO/peripheral layout or the user asked for it. For a known devkit pin (e.g. GPIO0 boot button), skip it to save turns and context size. **Do not guess** GPIO or wiring; ask the user if unsure.
- Activate the relevant `lua_module_*` skills in one go when possible — they define which modules exist and the real API names.
- Only `require` modules documented by an activated skill. Do not invent APIs or assume extra packages beyond the Lua runtime built-ins.
- Write scripts through **`lua_write_script`**, not `cap_cli`.
- **`path`** must be a relative `.lua` path, for example `temp/foo.lua` or `user/foo.lua`.
- `lua_list_scripts` also supports an optional `keyword` filter that does a case-insensitive substring match on the relative path.
- **Iterate under `temp/`** until the user confirms behavior; then move or rewrite to **`user/`** for kept scripts.
- `overwrite` defaults to `true`; set `false` only for create-only behavior when the user asks.

## Quality rules (aligned with project improvement report)

1. **No busy-wait for timing** — use `delay.delay_ms(ms)` from `lua_module_delay` inside any loop (animations, polling, monitors). Empty `for` loops as delay can still trip watchdogs under load.
2. **Reuse before creating** — call `lua_list_scripts` and extend an existing script when the request overlaps.
3. **Hardware lifecycle** — use `local function run() ... end` to open handles, `local function cleanup() ... end` with `pcall` on close/off, then `xpcall(run, debug.traceback)`, then `cleanup()`, then rethrow on failure. Prefer **`args`** (with `math.floor` for GPIO/counts) over hardcoded pins. On-device references: `button_demo.lua`, `led_strip_demo.lua`, `button_play_test_wav.lua` (the last keeps `board_manager` only for `audio_dac` codec params).
4. **Integers** — GPIO indices and pixel coordinates must be integers; use `math.floor` on computed floats before passing to hardware APIs.
5. **IM messages from Lua** — activate `lua_module_event_publisher`. **Default:** `ep.publish_message("text")` (string sets `source_cap` and uses injected `args`). Only use a **full table** if you need extra fields; never omit `source_cap` in table form. Use **dot** calls, not colon.
6. **Listing files** — use `lua_list_scripts` for scripts. To **read** a script’s source with `read_file`, use `scripts/<path>` as in **Reading Lua files** above. For generic non-Lua files, stay under the firmware file base (e.g. `/fatfs/...`), not invented roots like `/lua`.

## Guidance

- Prefer small scripts and documented module calls.
- When revising a confirmed script under `user/`, keep the same path unless the user asks to rename or move it.
