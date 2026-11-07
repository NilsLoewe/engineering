# Setup

Written for people and for Claude Code: each step says what to run and how to check it worked.

## 1. Prerequisites

| Need | Check |
|---|---|
| Claude Code | `claude --version` |
| GitHub CLI, signed in | `gh auth status` |
| Python 3 (tools and hooks) | `python3 --version` |
| Read access to every private overlay you will use | `gh repo view <owner>/<overlay>` |

## 2. Install the core

```
claude plugin marketplace add NilsLoewe/engineering
claude plugin install engineering@engineering
```

## 3. Install the overlays of your worlds

A world is a team or a company with its own rules (for example `engineering-fump`). Ask its maintainer which overlay repo it is, then:

```
claude plugin marketplace add <owner>/<overlay-repo>
claude plugin install <overlay>@<overlay>
```

A team repo can do this for you: when it carries a checked-in `.claude/settings.json` with `extraKnownMarketplaces` and `enabledPlugins`, Claude Code offers both plugins when you open the repo.

```json
{
  "extraKnownMarketplaces": {
    "engineering": {"source": {"source": "github", "repo": "NilsLoewe/engineering"}},
    "engineering-<world>": {"source": {"source": "github", "repo": "<owner>/engineering-<world>"}}
  },
  "enabledPlugins": {"engineering@engineering": true, "engineering-<world>@engineering-<world>": true}
}
```

## 4. Check

Start a new session inside a repo of the world and ask:

> Which text follows "# World:" in your context, which id has the first core rule, and are the skills engineering:clarify and engineering:review available?

Expected: the world's name, `kern-test-fails-without-fix`, yes. Outside the world's repos the world line is missing; that is correct.

## 5. Keep it current

```
claude plugin marketplace update engineering && claude plugin update engineering@engineering
claude plugin marketplace update <overlay> && claude plugin update <overlay>@<overlay>
```

Then restart or resume the session (`claude --resume`): a running session keeps the plugins it started with.

## 6. Trackers

- **GitHub issues** need nothing: states are labels `status:idea|clarifying|ready|in-progress|review|done`, created on first use.
- **Monday** needs the board's states from the overlay or a repo's `.engineering.json` (`{"tracker": {"monday": {"states": {...}}}}`) and a token in `MONDAY_TOKEN`, `MONDAY_TOKEN_FILE` or `./.env`.

## Next

- Work with it: `README.md` (skills and flow).
- Maintain a world or add your own personal layer: `docs/worlds.md`.
