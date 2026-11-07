---
name: world
description: Create or maintain a world overlay or a personal layer for the engineering plugin - scaffold it from the template, write rules and context pointers, publish it as a private repo and install it; or add a rule or context file to an existing one and bump its version. Use for "new world", "my own rules", "personal layer", "add a rule to the <world> world", "set up engineering for our team".
argument-hint: new personal | new team | add-rule <overlay> | add-context <overlay>
---

# world

Guide: `${CLAUDE_PLUGIN_ROOT}/../../docs/worlds.md` if present, else https://github.com/NilsLoewe/engineering/blob/main/docs/worlds.md. Template: `templates/overlay/` in the core repo (clone `NilsLoewe/engineering` into a scratch folder if it is not on this machine).

## new personal | new team

1. Ask once, bundled (AskUserQuestion): name (`engineering-<name>`), GitHub owner, which repos it applies in (personal: all or a list; team: the team's repos), tracker (GitHub default, or the board's states), what rules the person already knows they want, where their notes or methods live (wiki, MCP server, folder).
2. Copy the template, rename `engineering-WORLD` everywhere, fill `overlay.json`, `rules.md` (one line per rule, id at the end, ≤ ~2 KB), `context/*.md` as **pointers** to the notes, never copies.
3. `claude plugin validate <path>`. Test the hook in a matching repo: `cd <repo> && python3 <overlay>/plugins/<name>/hook.py` must print `# World: …`; in a non-matching repo it prints nothing.
4. Show the user the files, then on their OK: `git init`, commit, `gh repo create <owner>/<name> --private --source . --push`, `claude plugin marketplace add <owner>/<name>`, `claude plugin install <name>@<name>`.
5. Team world: offer a PR per team repo with the checked-in `.claude/settings.json` from `docs/setup.md` §3.
6. Tell the user to restart the session and run the check from `docs/setup.md` §4.

## add-rule | add-context

1. Read the overlay's `rules.md` / `context/`. A new rule needs: one imperative line, an id, one sentence why, where it was seen. Reject a rule that only restates a core rule; say which core rule covers it.
2. Edit, bump the patch version in `plugins/<name>/.claude-plugin/plugin.json`, commit on a branch, open a PR to the overlay repo (a team world is reviewed by the team).
3. If the rule holds beyond this world, say so and offer a PR one level up (world → core).
