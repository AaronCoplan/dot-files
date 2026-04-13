# Skill-Builder Reference

## Table of Contents

1. [Frontmatter Schema](#frontmatter-schema)
2. [Writing Effective Descriptions](#writing-effective-descriptions)
3. [Structuring Skills](#structuring-skills)
4. [Common Patterns](#common-patterns)
5. [Quality Checklist](#quality-checklist)
6. [Anti-Patterns](#anti-patterns)

---

## Frontmatter Schema

All fields live between `---` delimiters at the top of SKILL.md.

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `name` | string | Recommended | Directory name | Max 64 chars. Kebab-case only (lowercase, numbers, hyphens). Cannot contain "anthropic" or "claude". |
| `description` | string | Recommended | First paragraph of body | Max 1024 chars. No XML tags (`<` `>`). Must say what + when. Third person. |
| `argument-hint` | string | No | None | Shown during autocomplete. Example: `[create\|review\|edit] [skill-name]` |
| `allowed-tools` | string | No | None | Space-separated tool names. Grants permission without per-use approval. Supports patterns like `Bash(gh *)`. |
| `disable-model-invocation` | boolean | No | `false` | `true` = only user can invoke via `/name`. Keeps description out of context. |
| `user-invocable` | boolean | No | `true` | `false` = hidden from `/` menu. Use for background knowledge Claude loads automatically. |
| `model` | string | No | Current model | Override model when skill is active. |
| `context` | string | No | Main context | Set to `fork` to run in a subagent. Subagent does NOT see conversation history. |
| `agent` | string | No | `general-purpose` | Used with `context: fork`. Options: `Explore`, `Plan`, `general-purpose`, or custom from `.claude/agents/`. |
| `hooks` | object | No | None | Hooks scoped to this skill's lifecycle. See hooks documentation. |

### String Substitution Variables

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` or `$N` | Specific argument by 0-based index (e.g., `$0` = first argument) |
| `${CLAUDE_SESSION_ID}` | Current session ID for logging or session-specific files |

If `$ARGUMENTS` is not referenced in the skill content, arguments are appended automatically as `ARGUMENTS: <value>`.

### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands before the skill content is sent to Claude. Output replaces the placeholder. This is preprocessing, not something Claude executes.

```markdown
## Current branch context
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -5`
```

---

## Writing Effective Descriptions

### Rules
- **Third person**: "Processes files..." not "I help you process files..."
- **What + When**: Include both what the skill does and when to use it
- **Specific triggers**: Name the tasks, keywords, or file types that should activate this skill
- **Under 1024 characters**

### Good Examples
- "Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for 'design specs', or 'design-to-code handoff'."
- "Check availability across all calendars when scheduling events"
- "Summarize unread inbox emails with suggested actions"

### Bad Examples
- "Helps with projects." (too vague, no triggers)
- "I can help you create documents." (first person, no specifics)
- "Implements the hierarchical entity model with polymorphic relationships." (too technical, no user triggers)

---

## Structuring Skills

### Size Guidelines

| Lines | Approach |
|-------|----------|
| < 100 | Single SKILL.md, no TOC needed |
| 100-300 | Add a table of contents at the top |
| 300-500 | Split detailed content into supporting files |
| > 500 | Restructure — skill is too large for optimal performance |

### Recommended Section Order
1. Workflow / Protocol (numbered steps)
2. Context / Domain details
3. Guidelines / Best practices
4. Examples (if needed)
5. Troubleshooting (if needed)

### Progressive Disclosure
- **Level 1** (always loaded): `name` and `description` from frontmatter (~100 tokens)
- **Level 2** (on trigger): SKILL.md body (keep under 500 lines)
- **Level 3** (as needed): Supporting files read on demand

**Keep references one level deep.** SKILL.md links to supporting files directly. Never chain: SKILL.md -> file-a.md -> file-b.md.

For reference files over 100 lines, include a table of contents so Claude can see the full scope when previewing.

---

## Common Patterns

### 1. Sequential Workflow
Numbered steps with validation at each stage. Most common pattern in this project.
```markdown
## Workflow
1. Gather inputs
2. Validate inputs
3. Execute action
4. Present results for approval
5. Finalize
```

### 2. Iterative Refinement
Draft -> validate -> refine loop. Use when output quality improves with iteration.
```markdown
## Workflow
1. Create initial draft
2. Run quality checks
3. Fix any issues found
4. Repeat steps 2-3 until all checks pass
5. Present final version
```

### 3. Delegation / Subagent
Use `context: fork` for tasks that don't need conversation history. The skill content becomes the subagent's prompt.
```yaml
context: fork
agent: Explore
```
Only use fork when the skill has explicit, self-contained instructions. Guidelines-only skills need main context.

### Tool Permission Guidance
- **Built-in** (never list in `allowed-tools`): Read, Write, Edit, Glob, Grep, WebFetch, WebSearch
- **List in `allowed-tools`**: Bash, MCP tools (`mcp__*`), any tool requiring explicit permission
- **Use patterns for scoped access**: `Bash(gh *)`, `Bash(python3 scripts/*)`, `Bash(mkdir *)`
- **Fully qualify MCP tools**: `mcp__gmail__send_email`, not `send_email`

---

## Quality Checklist

### Frontmatter
- [ ] `name` is kebab-case (lowercase, numbers, hyphens only)
- [ ] `name` does not contain "anthropic" or "claude"
- [ ] `description` says what the skill does AND when to use it
- [ ] `description` is in third person
- [ ] `description` is under 1024 characters
- [ ] `description` contains no XML tags
- [ ] `argument-hint` is present if the skill takes arguments
- [ ] `allowed-tools` lists only non-built-in tools that are needed
- [ ] MCP tool names are fully qualified (e.g., `mcp__todoist__find-tasks`)

### Content
- [ ] SKILL.md body is under 500 lines
- [ ] Table of contents present if body exceeds 100 lines
- [ ] Workflow uses numbered steps
- [ ] No general knowledge Claude already has (e.g., explaining what JSON is)
- [ ] No stale dates or time-sensitive information
- [ ] Consistent terminology throughout (pick one term, stick with it)
- [ ] No XML tags anywhere in the file

### Specificity
- [ ] Degree of freedom matches task fragility (critical operations get rigid scripts, creative tasks get guidelines)
- [ ] Templates or examples provided where output format matters
- [ ] Error handling documented for common failure modes
- [ ] Scripts handle errors explicitly rather than failing silently

### Structure
- [ ] Sections follow recommended order: Workflow > Context > Guidelines
- [ ] Supporting files are one level deep from SKILL.md
- [ ] Reference files over 100 lines have a table of contents
- [ ] Scripts placed in `scripts/` at project root (not inside skill directory)
- [ ] No `README.md` inside the skill folder

### Project Conventions
- [ ] Tone is direct and concise, no filler
- [ ] Headings use `##` for major sections
- [ ] MCP tools use double-underscore naming (`mcp__service__tool`)
- [ ] Skill directory matches the `name` field

---

## Anti-Patterns

### 1. Info Dump
Explaining things Claude already knows. Challenge every paragraph: "Does Claude need this?"

### 2. Over-Specification
Micro-managing every decision when the task allows flexibility. Match rigidity to fragility.

### 3. Vague Descriptions
"Helps with projects" or "Processes data" — too generic for Claude to select from 100+ skills.

### 4. Nested References
SKILL.md -> advanced.md -> details.md causes partial reads. Keep everything one level deep.

### 5. Hardcoded Dates
"As of January 2025..." becomes stale. Use relative phrasing or omit.

### 6. Missing Tool Qualifiers
`send_email` instead of `mcp__gmail__send_email`. Claude may fail to locate the tool.

### 7. Kitchen-Sink allowed-tools
Listing every possible tool "just in case." Only list tools the skill actually uses.

### 8. No Workflow
Dumping context without actionable steps. Always include numbered workflow steps.

### 9. No Testing Guidance
Shipping a skill without advising how to test it. Always include post-creation testing steps.

### 10. Monolithic SKILL.md
500+ lines in a single file. Split into SKILL.md (overview + workflow) and supporting files (details).
