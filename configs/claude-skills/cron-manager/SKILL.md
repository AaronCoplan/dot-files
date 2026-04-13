---
name: cron-manager
description: Manages scheduled jobs via macOS launchd for recurring automated tasks. Use when creating, listing, updating, or deleting scheduled entries, or when designing reliable scheduled automations.
allowed-tools:
  - Bash(launchctl *)
  - Bash(plutil *)
  - Bash(tail *)
  - Bash(ls -la ~/.local/log/*)
  - Bash(mkdir -p ~/.local/log)
argument-hint: "[create|list|delete|debug|logs] — e.g. 'create a daily newsletter digest job' or 'list all scheduled jobs' or 'show digest logs'"
---

## Environment

PAARON runs in two environments:
- **Laptop (development):** macOS — use `launchd` for scheduled jobs
- **VM (production):** Ubuntu 24.04 LTS on GCP — use `systemd` timers

Use the appropriate mechanism for the target environment. The kill-switch and runlog contracts are identical in both.

---

## On macOS (development) — launchd

All scheduled jobs MUST use macOS `launchd` via plist files in `~/Library/LaunchAgents/`. This is the only supported approach because:

- **Catches up after sleep** — if the Mac is asleep when a job is scheduled, launchd runs it once on wake (multiple missed intervals are coalesced into a single execution)
- Survives machine reboots and app restarts
- Runs fully headless — no app or terminal session required
- Native macOS mechanism, no third-party tools

Do NOT use:
- **crontab** — does not wake the machine or catch up missed jobs after sleep
- **Claude Code's `/loop`** — session-scoped, expires after 3 days
- **Desktop scheduled tasks** — requires the app to be open
- **`launchd StartInterval`** — broken since El Capitan; missed intervals during sleep are lost

## Workflow

1. Parse the user's request to determine the action: create, list, update, or delete a job
2. For new jobs, discuss the schedule, command, and reliability requirements before creating
3. Create/edit plist files in `~/Library/LaunchAgents/` with label prefix `com.paaron.`
4. Always log output to `~/.local/log/` via `StandardOutPath`/`StandardErrorPath`
5. Validate with `plutil -lint` before loading
6. Load/unload with `launchctl` and verify

## Creating a job

```bash
# Ensure log directory exists
mkdir -p ~/.local/log
```

Create a plist at `~/Library/LaunchAgents/com.paaron.<jobname>.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.paaron.jobname</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>sleep 60 &amp;&amp; exec /usr/bin/caffeinate -i /Users/afcoplan/.local/bin/claude -p 'your prompt here'</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/afcoplan/Documents/github/paaron</string>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/afcoplan/.local/log/jobname.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/afcoplan/.local/log/jobname.err.log</string>
</dict>
</plist>
```

Key rules:
- **Always wrap with `sleep 60 && exec caffeinate -i`** — the 60-second delay avoids resource contention when macOS fires coalesced jobs after waking from sleep. `caffeinate -i` prevents idle sleep mid-execution. Use `/bin/bash -c` with the full command as a single string argument.
- **Always use absolute paths** — no `~/` in plist files
- **Always set `RunAtLoad` to true** — catches the edge case where the Mac was fully shut down (not just sleeping) and booted after the scheduled time. Safe because jobs are idempotent.
- **Always set `WorkingDirectory`** — must point to the paaron repo so `claude -p` can find project skills and CLAUDE.md
- **Label must match filename** — `com.paaron.foo` label → `com.paaron.foo.plist` file

Then validate and load:

```bash
plutil -lint ~/Library/LaunchAgents/com.paaron.jobname.plist
launchctl load ~/Library/LaunchAgents/com.paaron.jobname.plist
```

## Listing jobs

```bash
launchctl list | grep paaron
```

## Deleting a job

```bash
launchctl unload ~/Library/LaunchAgents/com.paaron.jobname.plist
rm ~/Library/LaunchAgents/com.paaron.jobname.plist
```

## Updating a job

```bash
launchctl unload ~/Library/LaunchAgents/com.paaron.jobname.plist
# Edit the plist file...
plutil -lint ~/Library/LaunchAgents/com.paaron.jobname.plist
launchctl load ~/Library/LaunchAgents/com.paaron.jobname.plist
```

## Runlog Contract

Every new cron job MUST integrate with `scripts/runlog.py`. Add `Bash(python3 scripts/runlog.py *)` to the skill's `allowed-tools`.

**At skill start:**
```bash
# 1. Check kill switch — if active, exit immediately (before doing any work)
python3 scripts/runlog.py is-killed --job <job-name> && exit 0

# 2. Start run — capture run_id; if exit code is 99, kill switch fired during start
RUN_ID=$(python3 scripts/runlog.py start --job <job-name> --trigger cron)
```

**At skill end (both success and error paths):**
```bash
# Success:
python3 scripts/runlog.py finish --run-id "$RUN_ID" --status ok --summary "..."
# Failure:
python3 scripts/runlog.py finish --run-id "$RUN_ID" --status failed --error "..."
```

**Kill switch:** To pause a job without editing cron, create a flag file:
```bash
# Pause: (optional: echo "reason" into the file)
touch ~/.local/state/paaron/kill/<job-name>.off
# Resume:
rm ~/.local/state/paaron/kill/<job-name>.off
```
Active kill switches are surfaced by `/paaron-status`. Always prefer this over `launchctl unload`.

## Reliability Best Practices

Follow these principles when designing jobs, especially on machines that may sleep or be powered off:

### Store timestamps in the destination, not fixed lookback windows

Don't use fixed lookback windows like `--days 7` — if the machine is off for 15 days, you lose 8 days of data. Instead, store the last successful run timestamp in the output system (e.g. a callout block in Notion) and fetch everything since that timestamp. Use a fixed `--days` only as a fallback for the very first run.

### Dedup at the destination

Check the output system (Notion, email, etc.) for existing entries before writing. Do not rely on local state files to track what has been processed — the destination is the source of truth.

### Store state in the output system

Avoid maintaining separate state files in local config directories. If a job writes to Notion, check Notion for what already exists. If it sends email, check sent mail. This keeps the system self-healing.

### Log output somewhere reviewable

Always use `StandardOutPath` and `StandardErrorPath` in the plist to capture output:

```xml
<key>StandardOutPath</key>
<string>/Users/afcoplan/.local/log/jobname.log</string>
<key>StandardErrorPath</key>
<string>/Users/afcoplan/.local/log/jobname.err.log</string>
```

### Store config in skills, not separate config files

Hardcode known defaults (Notion page IDs, newsletter queries, etc.) directly in the skill definition rather than maintaining separate config files. Skills are version-controlled and self-documenting.

### Design for idempotent catch-up

Assume the machine may be off when a job is scheduled. Every run should:
- Read the last-run timestamp from the destination system
- Check what has already been processed at the destination
- Process only what is new
- Update the timestamp after successful processing
- Produce the same result regardless of how many times it runs for the same data

## Debugging

### Check if a job ran

```bash
# View recent log output
tail -50 ~/.local/log/jobname.log

# Check when the log was last written to
ls -la ~/.local/log/jobname.log

# Check error log
tail -50 ~/.local/log/jobname.err.log
```

### Check job status

```bash
# List all paaron jobs and their status
# Columns: PID, last exit status, label
# PID of "-" means not currently running
launchctl list | grep paaron
```

### Verify the plist is valid

```bash
plutil -lint ~/Library/LaunchAgents/com.paaron.jobname.plist
```

### Test a job manually

Run the exact command from the plist to verify it works (skip the `sleep 60` when testing manually):

```bash
# Copy the command from the plist and run it directly (without the sleep delay)
caffeinate -i /Users/afcoplan/.local/bin/claude -p "/digest-newsletters email --query 'from:pragmaticengineer'"
```

---

## On Linux (production) — systemd

On the GCP VM, PAARON jobs run as systemd timers. Unit files live in `deploy/systemd/` in the repo and are installed to `/etc/systemd/system/`.

### Creating a new job on Linux

1. Create `deploy/systemd/paaron-<job>.service`:

```ini
[Unit]
Description=PAARON <Job Name>
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=aaron
WorkingDirectory=/home/aaron/Documents/github/paaron
ExecStart=/home/aaron/.local/bin/claude --effort max -p "/<skill>"
StandardOutput=append:/home/aaron/.local/log/<job>.log
StandardError=append:/home/aaron/.local/log/<job>.err.log
Environment=HOME=/home/aaron

[Install]
WantedBy=multi-user.target
```

2. Create `deploy/systemd/paaron-<job>.timer`:

```ini
[Unit]
Description=Run PAARON <job> on schedule

[Timer]
OnCalendar=*-*-* HH:MM:SS America/New_York
Persistent=true

[Install]
WantedBy=timers.target
```

Key rules:
- **Always include `America/New_York`** in `OnCalendar` — Ubuntu defaults to UTC, schedules would be off by 4–5 hours without it
- **Always set `Persistent=true`** — equivalent to launchd catch-up; fires once on next start if a fire was missed during downtime
- **`Type=oneshot`** — each run is a one-shot job; systemd won't start a second instance if the first is still running
- **Add `TimeoutStartSec=N`** if the job might run longer than the default 90s (newsletter digest uses 1800s)

3. Install on the VM:

```bash
sudo cp deploy/systemd/paaron-<job>.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now paaron-<job>.timer
```

### Admin commands (Linux)

```bash
# See all timers and next-run times
systemctl list-timers 'paaron-*'

# Run a job immediately
sudo systemctl start paaron-<job>.service

# View recent output
journalctl -u paaron-<job>.service -n 100

# Pause a job (kill switch — preferred over disabling)
touch ~/.local/state/paaron/kill/<job>.off
```

See `deploy/systemd/README.md` for full installation instructions.

---

## Registered Jobs

Current scheduled jobs for this project:

| Schedule | Job | Plist | Log |
|----------|-----|-------|-----|
| Daily 9am + on login | Newsletter digest (all sources) | `com.paaron.newsletter-digest.plist` | `~/.local/log/newsletter-digest.log` |
| 6x daily (6am-9pm) | Todo triage | `com.paaron.todo-triage.plist` | `~/.local/log/todo-triage.log` |
| Weekly Sunday 9am | Financial check-in | `com.paaron.financial-checkin.plist` | `~/.local/log/financial-checkin.log` |
| Weekdays 7am, Sat+first-Sun 7:30am | Morning briefing (first Sunday adds --weekly-review) | `com.paaron.briefing.plist` | `~/.local/log/briefing.log` |

Update this table when adding or removing jobs.

## Common Patterns

### Daily digest job

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### Weekly job (every Friday at 10am)

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key>
    <integer>5</integer>
    <key>Hour</key>
    <integer>10</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### Weekdays only at 9am

```xml
<key>StartCalendarInterval</key>
<array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
</array>
```

### StartCalendarInterval reference

Omitted keys act as wildcards (match all values):

| Key | Values |
|-----|--------|
| `Month` | 1–12 |
| `Day` | 1–31 |
| `Weekday` | 0–7 (Sun=0 or 7) |
| `Hour` | 0–23 |
| `Minute` | 0–59 |
