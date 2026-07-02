# 5. Permissions & Hooks — the Security Model

An agent that runs shell commands on your machine needs guardrails. Claude Code's model has three layers: permission rules, permission modes, and hooks.

## Permission rules

Settings files carry `allow` / `ask` / `deny` lists of rule patterns:

```json
{
  "permissions": {
    "allow": ["Bash(git status:*)", "Read(~/projects/**)"],
    "deny":  ["Read(.env)", "Bash(curl:*)"]
  }
}
```

- Rules match `Tool(specifier)`. For Bash, the *command itself* is parsed and matched — `Bash(git commit:*)` allows any `git commit …` but not `git push`.
- Deny always wins. Unmatched calls prompt the user interactively ("Yes / Yes, don't ask again / No").
- "Don't ask again" writes an allow rule into `.claude/settings.local.json` — the allowlist is *learned* over time.

## Permission modes

| Mode | Behavior |
|------|----------|
| `default` | Prompt on anything not allowlisted |
| `acceptEdits` | File edits auto-approved; Bash still prompts |
| `plan` | Read-only: no edits, no mutating commands, agent produces a plan for approval |
| `bypassPermissions` | Everything auto-approved (dangerous; for sandboxes/CI) |

Plus OS-level **sandboxing** for Bash (seatbelt on macOS, bubblewrap on Linux) restricting filesystem/network access, with escalation prompts when a command genuinely needs more.

## Hooks: user-owned interception

Hooks are shell commands the *harness* (not the model) runs at lifecycle events:

```
PreToolUse    → can block or rewrite a tool call (exit code 2 = block, stderr fed to model)
PostToolUse   → react to results (e.g. auto-run prettier after Edit)
UserPromptSubmit → validate/augment the user's prompt
Stop / SubagentStop → run when the agent finishes (e.g. force tests to pass)
SessionStart / SessionEnd / PreCompact / Notification
```

Each hook receives the event as JSON on stdin and can return JSON to alter behavior. This is the extension point for "always do X" automation — deterministic, enforced by the harness, impossible for the model to skip.

## Threat model honesty

The system defends mainly against *accidents* (the model doing something dumb) and gives users control points. Prompt injection from files/web content is mitigated by system-prompt training, `<system-reminder>` provenance markers, permission prompts on side effects, and sandboxing — but reviewing what an agent does with write access remains on you. That trade-off is inherent to every coding agent, not just this one.
