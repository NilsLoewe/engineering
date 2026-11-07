# Worlds and personal layers

The core knows no company. Everything specific lives in **overlays**: plugins that add rules, tracker config, lenses and context, but only inside the repos they name.

| Kind | Applies in | Holds | Owner |
|---|---|---|---|
| **Core** | every git repo | process skills, verifier, core rules | core maintainers |
| **World overlay** | the repos of one team or company | team rules, tracker config, process, owners, review lenses | the team |
| **Personal layer** | every repo you work in (or a list) | your own working style, your methods, pointers to your notes | you |

Rules add up: core + world + personal. **In a team repo the world rules win** over personal ones; a personal layer adds habits, it never relaxes a team rule.

## Create a personal layer

Ask Claude Code: `/engineering:world new personal` and answer its questions. By hand:

1. `cp -R <core clone>/templates/overlay ~/engineering-<you>` and rename `engineering-WORLD` (folder, `plugin.json`, `marketplace.json`) to `engineering-<you>`.
2. `overlay.json`: `"world": "<you> (personal)"`, `"repos": [".*"]` for every repo, or a list of regexes on `git remote get-url origin`. Personal layers usually leave `"tracker"` empty.
3. `rules.md`: your rules, one line each, ending in an id: ``- Write the test before the fix. `[<you>-test-first]` ``. Keep it short; the file is loaded into every session (budget ~2 KB).
4. `context/`: pointers instead of copies. A methods wiki is a context entry, not pasted text:
   ```json
   "context": {"context/methods.md": "before planning or reviewing, for my own best practices"}
   ```
   with `context/methods.md` saying where the wiki is and how to read it (an MCP server name, a URL, a search tool).
5. Put it in a **private** GitHub repo, then `claude plugin marketplace add <you>/engineering-<you>` and `claude plugin install engineering-<you>@engineering-<you>`.
6. Check as in `docs/setup.md` §4: the context shows two `# World:` lines inside a team repo (team and personal).

## Maintain a world overlay

- Change `rules.md` and `context/` by pull request to the overlay repo; the team reviews it like code.
- **Bump `version` in `plugins/<overlay>/.claude-plugin/plugin.json` with every change**, or installed copies do not refresh.
- A rule enters when it holds in every repo of the world and was seen more than once (a review finding, a QA return, an incident). Write the rule, the reason in one sentence and where it was seen.
- Review lenses (optional): a `katalog/` with YAML rules, built with `python3 <core>/tools/build_katalog.py --katalog katalog --out plugins/<overlay>/generated --titel "World rules (<world>)"`; point `"lenses"` in `overlay.json` at `generated/linsen/index.json`.

## Give back upward

A rule that turns out true in several worlds, or a personal method that would help everyone, goes up one level:
personal → world (PR to the world overlay) → core (PR to `NilsLoewe/engineering`). Name where it was seen in each world.

## Create a team world

Same as a personal layer, but: `"repos"` lists the team's repos, `"tracker"` holds the board config if it is not GitHub, `context/process.md` says who owns issues, who reviews, when a PR may merge and where reports go. Then add the checked-in `.claude/settings.json` from `docs/setup.md` §3 to each team repo.
