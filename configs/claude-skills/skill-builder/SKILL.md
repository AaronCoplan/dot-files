---
name: skill-builder
description: Creates, reviews, and edits Claude Code skills following best practices. Use when building a new skill from scratch, reviewing an existing skill for improvements, or editing a skill to add features or fix issues.
argument-hint: [create|review|edit] [skill-name]
allowed-tools: Bash
---

## Argument Parsing

Parse `$ARGUMENTS` as `<subcommand> <skill-name> [extra context]`.

- **Subcommands**: `create`, `review`, `edit`
- If subcommand or skill-name is missing, ask the user

## Step 1: Load Reference

Read `reference.md` from this skill's directory for the full best-practices guide, frontmatter schema, and quality checklist. Use it throughout the workflow.

## Step 2: Understand Context

### create
1. Ask the user: What does the skill do? What tools does it need? When should it trigger?
2. Read 2-3 existing skills from `.claude/skills/*/SKILL.md` to match project conventions
3. Review available CLI scripts in `scripts/` for tool integration

### review
1. Read the target skill at `.claude/skills/<skill-name>/SKILL.md` and any supporting files
2. Note line count, section structure, frontmatter completeness, and tool usage

### edit
1. Read the target skill at `.claude/skills/<skill-name>/SKILL.md`
2. Ask the user what changes they want

## Step 3: Draft or Analyze

### create
1. Draft SKILL.md following project conventions (see below)
2. If the skill will exceed ~100 lines, add a table of contents
3. If it will exceed ~300 lines, split detailed content into supporting files (one level deep)

### review
1. Run through every item in the Quality Checklist from reference.md
2. Report: passes, failures with specific fixes, and priority improvements
3. Suggest concrete rewrites for any failing items

### edit
1. Identify which sections need modification
2. Draft the updated SKILL.md
3. Validate changes against the quality checklist

## Step 4: Validate

Before finalizing, verify all of these:
- `name` is kebab-case, no spaces or capitals
- `description` says what the skill does AND when to use it (third person)
- `allowed-tools` lists only non-built-in tools needed (Read/Write/Edit/Glob/Grep are built-in)
- CLI tool patterns use `Bash(python3 scripts/<name>.py *)` in `allowed-tools`
- SKILL.md body is under 500 lines
- No stale dates or time-sensitive information
- Consistent terminology throughout

## Step 5: Present and Iterate

1. Show the full draft to the user
2. Highlight key design decisions (context mode, supporting files, tool choices)
3. Ask for feedback and iterate until approved
4. Write files to `.claude/skills/<skill-name>/`

## Step 6: Post-Creation Guidance

After writing files, advise the user to:
- Test with `/<skill-name>` in a conversation
- Check that CLI tool permissions work correctly
- Iterate based on real usage (under-triggering, over-triggering, missing steps)

## Project Conventions

Patterns established by existing skills in this project:

- **Tone**: Direct, concise, no filler
- **Workflow format**: Numbered steps under a `## Workflow` or `## Protocol` heading
- **Section order**: Workflow > Commands (if CLI) > Context/domain details > Guidelines/best practices
- **Typical size**: 20-70 lines for SKILL.md body
- **Frontmatter fields used**: `name`, `description`, `allowed-tools` (add `argument-hint` when the skill takes arguments)
- **Scripts**: Place in `scripts/` at project root, not inside the skill directory
- **Skill location**: `.claude/skills/<skill-name>/SKILL.md` (project-level)
- **Available CLI scripts**: `scripts/gmail.py` (email), `scripts/gcal.py` (calendar), `scripts/todoist.py` (tasks), `scripts/notion.py` (knowledge base)
- **CLI tool pattern**: Use `Bash(python3 scripts/<name>.py *)` in `allowed-tools` for scoped Bash access
