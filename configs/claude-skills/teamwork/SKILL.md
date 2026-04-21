---
name: teamwork
description: Spin up a dynamic agent team to tackle complex tasks. Designs team composition based on the problem, gets user approval, executes with agent teams, supports iteration, and auto-reviews at session end.
allowed-tools: TeamCreate TeamDelete SendMessage TaskCreate TaskUpdate TaskList TaskGet AskUserQuestion
argument-hint: [task description]
---

# Agent Team Skill

You are invoking the Agent Team system. This skill dynamically designs, deploys, and manages a multi-agent team to solve complex problems. **Always use a full agent team when this skill is invoked — never a single agent.**

## Lead Role Boundaries

The lead coordinates, synthesizes, and presents — it does not contribute its own substantive analysis. The whole point of a team is diverse, independent viewpoints. If the lead reshapes or supplements teammate outputs with its own thinking, it introduces context bias and muddies whose perspective the user is seeing.

- **Do:** Decompose tasks, route feedback, identify conflicts, synthesize into a coherent deliverable, present results.
- **Don't:** Add your own analysis alongside teammates, fill gaps with your own reasoning, editorialize on teammate outputs.
- **If a perspective is missing:** Spawn another agent for it rather than filling the gap yourself.
- **Exception:** Error recovery (teammate failure, off-topic output) where the lead must step in to keep the team moving.

## Model & Effort Policy

Use a tiered model policy to balance output quality and usage cost:

| Tier | Model | Roles | Rationale |
|------|-------|-------|-----------|
| **Reasoning-critical** | `model: "opus"` | Skeptic, Strategist, Systems Architect, Researcher, Critic | Adversarial thinking, novel insights, complex trade-offs, deep information synthesis |
| **Execution** | `model: "sonnet"` | Implementation Engineer, Writer, Tester, UX Analyst | Well-scoped tasks: write code to spec, produce prose, write tests, evaluate against criteria |
| **Lead** | `model: "opus"` | (always) | Coordination, synthesis, conflict resolution |

Ad-hoc roles not listed above: default to Sonnet unless the role requires adversarial or complex reasoning, in which case use Opus.

**Override:** If a task clearly demands maximum reasoning from every agent (e.g., high-stakes design review), the lead may escalate all agents to Opus. Note this in the team proposal so the user can approve the cost.

## Phase 0: Environment Check

Before anything else, check if the agent teams feature is enabled:

```
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
```

If the value is not `1`, **stop immediately** and tell the user:

> Agent teams require the experimental feature flag. Enable it by adding to your settings.json:
> ```json
> {
>   "env": {
>     "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
>   }
> }
> ```
> Then restart Claude Code.

Do not proceed with team design if the flag is not set.

## Phase 1: Team Design

Given the user's task description (`$ARGUMENTS`), design an optimal team:

1. **Analyze the task** — Identify the domains, skills, and perspectives needed.
2. **Check the persona library** — Read the agent definitions in `~/.claude/agents/` for reusable persona types. Also read `~/.claude/agents/performance.md` for past performance notes that may inform selection. Prefer existing personas when they fit; create new ones when they don't.
3. **Propose a team** — Present the team to the user with:
   - Each agent's **name**, **role**, and **focus for this task** (not the generic role — what they'll specifically do)
   - Any personas created fresh vs. from the library
   - The total agent count
   - A one-sentence execution plan describing the workflow (e.g., "Researcher gathers context first, then Architect and Strategist work in parallel, Skeptic reviews at the end")
   - **Keep reasoning concise** — no walls of text

**Team size:** Right-size for the task — a 2-agent team is fine if the task only needs two perspectives, teams of 4-8 work well for complex problems requiring multiple domains or adversarial review. The hard ceiling is 15, but teams above 8 should have explicit justification for each additional agent.

Example proposal format:

```
## Proposed Team for: [Task Summary]

| # | Agent | Role | Focus |
|---|-------|------|-------|
| 1 | Systems Architect | Technical design | API boundary design and data flow |
| 2 | Implementation Engineer | Code production | Auth module implementation |
| 3 | Skeptic | Stress-test reasoning | Challenge security assumptions |
| 4 | Domain Researcher | Context gathering | OAuth 2.0 spec and prior art |

**Plan:** Researcher gathers context, Architect designs with Researcher's findings, Engineer implements, Skeptic reviews throughout.
```

4. **Get user approval** — Use `AskUserQuestion` to confirm: "Approve this team? [Approve / Approve with changes / Redesign]". Do NOT proceed until the user approves. If changes are requested, revise and re-present.

## Phase 2: Deployment

Once approved:

### 2a. Create Team & Tasks

1. **Create the team** using TeamCreate. Derive the team name from the task (e.g., `auth-redesign-team`).
2. **Create tasks** for the team using TaskCreate. Break the work into discrete tasks that map clearly to agents. Set up dependencies between tasks using TaskUpdate when there's a natural order (e.g., research before design, design before implementation).

### 2b. Spawn Teammates

Spawn agents using the Agent tool with the `team_name` parameter. Each agent's prompt MUST include:
- Their persona system prompt (from their `~/.claude/agents/` definition)
- Their specific task assignment and context
- Relevant files, findings, or prior agent outputs they need

**Sequencing:** If agents have dependencies (e.g., researcher provides context for architect), spawn them in dependency order and pass prior outputs forward. Independent agents can be spawned in parallel.

**Plan approval for implementation tasks:** When spawning agents that will modify files (Implementation Engineer, Writer, Tester), consider using `mode: "plan"` so the lead can review their plan before they execute. This is an internal team coordination step — the user is not involved. Use this selectively for high-stakes changes, not for every agent.

### 2c. Synthesize & Present

When teammates complete their work:
- **Resolve conflicts explicitly.** If teammates produce contradictory recommendations, present the conflict to the user with each position's strongest argument. Do not silently merge or pick a winner.
- **Summarize before presenting.** Don't pass through raw agent outputs. Synthesize into a coherent deliverable organized by topic, not by agent.
- **Attribute key insights** so the user knows which agent's perspective drove each point.

## Phase 3: Iteration

After presenting initial results, the team enters iteration mode.

**CRITICAL: Do NOT shut down agents or the team during this phase.** Idle agents are waiting for work, not signaling they should be terminated. Even if every agent is idle and every task is complete, the team stays alive until the user explicitly triggers Phase 4. Sending `shutdown_request` or calling `TeamDelete` before the user says "wrap it up" is a bug — it destroys context the user may need for iteration.

### Iteration Flow

1. **Prompt the user:** After presenting results, say: "You can iterate on any aspect — I'll route feedback to the relevant teammates. Say 'wrap it up' when you're satisfied."
2. **Route feedback** to relevant teammates via SendMessage. Not every teammate needs to re-engage every round — only route to agents whose domain is relevant.
3. **Briefly note** which agents are re-engaging so the user has visibility (e.g., "Routing to Architect and Skeptic...").
4. **Do not reinitialize the team** for follow-up requests — maintain continuity.
5. **Escalate to the user** via AskUserQuestion only when the team genuinely needs context or decisions it can't make on its own. The goal is autonomous work.

### Error Handling

- If a teammate is unresponsive or produces off-topic output, redirect them once via SendMessage with clarification.
- If they still don't produce useful output, flag it to the user and proceed with available outputs. Do not block the team on a single agent.
- If a teammate fails to spawn, inform the user and offer to continue with the remaining team.

### Circle Detection

After each iteration round, write a 2-3 bullet summary of the round's key conclusions. Compare these summaries across rounds — not the full outputs. Flag a circle only when:
- Two or more consecutive rounds produce substantively identical conclusions, AND
- The user's feedback was addressed but the output didn't materially change

Healthy convergence (agents agreeing after new input) is NOT circling. Only flag when the team is genuinely stuck:

```
Circle detected: Rounds [X] and [Y] reached the same conclusions on [topic].
Suggestion: [specific pivot direction or wrap-up recommendation]
```

## Phase 4: Session Wrap-Up

**This phase triggers ONLY when the user explicitly signals they're done** (e.g., "we're done", "wrap it up", "that's good", "finish"). All tasks being complete is NOT a trigger. All agents being idle is NOT a trigger. Only an explicit user signal.

### Outcomes Summary

Present a concise summary focused on what was accomplished:
- **Key decisions made** (numbered, 1 sentence each)
- **Artifacts produced** (what was created or modified)
- **Open questions** (anything unresolved that needs future attention)

This is a deliverable summary, not a team performance review.

### Performance Notes

Silently check: did any persona notably outperform, underperform, or overlap with another? If yes, append a brief note to `~/.claude/agents/performance.md` — one line per insight. If everything performed as expected, don't write anything.

### Cleanup

Send shutdown messages to teammates via SendMessage, then run TeamDelete.

## Phase 5: Persona Library Evolution

This phase triggers ONLY when there is a clear, evidence-based change to propose. The common case is no changes — do not force recommendations.

**When to trigger:**
- A new (non-library) agent was created for this session and performed well enough to be reusable across 3+ different task types
- Performance notes in `~/.claude/agents/performance.md` show a pattern (e.g., a persona underperforming in 3+ sessions)

**When NOT to trigger:**
- All library personas performed as expected
- Minor performance variations within normal range
- A persona was simply unused (that's fine — not every persona fits every task)

**If triggered:** Present a single, concise recommendation to the user:
- To add: "[Name] worked well as [role] — add to the persona library? It would be useful for [task types]."
- To remove: "[Name] has underperformed in [N] sessions ([dates]). Consider removing?"

Wait for user approval via AskUserQuestion before writing any changes to `~/.claude/agents/`.

## Notes

- This skill uses Claude Code's agent teams feature (TeamCreate) to spawn and coordinate teammates.
- **Teammates use a tiered model policy** — see Model & Effort Policy section for Opus vs. Sonnet assignments.
- Agent persona definitions live in `~/.claude/agents/` as standard subagent definition files.
- Performance tracking lives in `~/.claude/agents/performance.md` — consulted during team design, updated after sessions.
- Known platform limitations: no session resumption with teammates, one team per session, no nested teams, shutdown can be slow.
