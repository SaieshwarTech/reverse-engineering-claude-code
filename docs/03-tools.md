# 3. The Tool System

Tools are the model's hands. Each is a JSON schema sent with every API call, plus a client-side executor. Claude Code's built-in set:

## File tools
| Tool | Purpose | Design notes |
|------|---------|--------------|
| **Read** | Read file with line numbers | Returns `cat -n` format so the model can cite `file:line`. Truncates long files; supports images and PDFs. |
| **Write** | Create/overwrite a file | Refuses to overwrite a file the model hasn't Read — prevents blind clobbering. |
| **Edit** | Exact string replacement | Requires `old_string` to be *unique* in the file. Forces the model to read before editing. This uniqueness constraint is the key trick that makes LLM edits reliable. |
| **NotebookEdit** | Jupyter cell edits | Cell-level granularity instead of string matching. |

## Search tools
| Tool | Purpose | Design notes |
|------|---------|--------------|
| **Glob** | Filename patterns | Fast, sorted by mtime. |
| **Grep** | Content search (ripgrep) | Full regex; output modes tuned to save tokens (files-only vs content). |

## Execution
| Tool | Purpose | Design notes |
|------|---------|--------------|
| **Bash** | Run shell commands | Persistent working dir, timeouts, background mode. The permission system (ch. 5) parses commands to match allowlist rules like `Bash(git status:*)`. |

## Orchestration
| Tool | Purpose | Design notes |
|------|---------|--------------|
| **Task / Agent** | Spawn a subagent | A fresh agent loop with its own context window; returns only its final message. This is context isolation — chapter 6. |
| **TodoWrite / task tools** | Track progress | Structured plan state rendered in the UI; also keeps the model itself on track over long tasks. |
| **WebFetch / WebSearch** | Internet access | Fetched pages are converted to markdown and often summarized by a small model before entering context. |
| **AskUserQuestion** | Structured questions | Multiple-choice prompts back to the human. |
| **Skill** | Load a skill | Injects a markdown instruction file into context on demand — "progressive disclosure" of capability. |

## MCP tools

External servers (Model Context Protocol) register extra tools, namespaced `mcp__<server>__<tool>`. From the loop's perspective they are identical to built-ins: schema in, JSON result out. Claude Code can also *defer* tool schemas and load them on demand (ToolSearch) to keep the system prompt small.

## Why the design works

1. **Few, composable primitives.** ~15 tools cover everything; Bash is the escape hatch.
2. **Token-frugal outputs.** Every tool truncates, paginates, or summarizes.
3. **Failure as information.** Errors return as text for the model to react to.
4. **Read-before-write invariants.** Edit/Write enforce that the model has seen current file state, eliminating a whole class of hallucinated edits.
