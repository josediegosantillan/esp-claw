# Lua Script Editing

Use this skill when the user wants to create or modify a Lua script.

## Rules
- Before writing or revising Lua code, first get the board hardware information. When information is lacking, **don't guess**, ask the user.
- Activate the relevant `lua_module_xxx` skills first. They are the source of truth for available Lua modules and function names.
- Only use modules documented by those skills. Do not invent APIs or assume extra Lua packages beyond the runtime's built-ins.
- Write scripts through `lua_write_script`, not `cap_cli`.
- `path` must be a relative `.lua` path under the configured Lua base directory, for example `demo.lua` or `temp/demo.lua`.
- New or unconfirmed scripts must be written under `temp/`.
- When the user confirms the script should be kept, save the final version under `user/`.
- `overwrite` defaults to `true`; set it to `false` only when the user explicitly wants create-only behavior.

## Import Rule
- Only use Lua modules that are described by the activated `lua_module_xxx` skills.
- Do not use `require(...)` for any module outside that set.
- Do not assume standard Lua libraries or third-party Lua modules are available unless they are explicitly described by an activated `lua_module_xxx` skill.
- If a needed capability is not covered by the activated `lua_module_xxx` skills, do not invent an API. Change the script design to use only the available modules.

## Writing Rule
- Prefer small, direct scripts that only depend on the available Lua modules.
- When using a module, follow the exact import name and function names documented by its `lua_module_xxx` skill.
- If the user asks for behavior that depends on GPIO, delay, storage, LED strip, or event publishing, activate the matching module skills first and then write the script.

## Workflow
1. Activate all `lua_module_xxx` skills.
2. Check which modules and functions are available.
3. Write or update the Lua script using only those modules.
4. Save the script through the Lua authoring capability flow.
