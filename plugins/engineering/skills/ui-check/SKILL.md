---
name: ui-check
description: Check a UI in a real browser through the chrome-devtools MCP (Chrome Beta). Mode `change` walks every screen a diff changed through its states and writes the evidence build, verifier and pr need. Mode `explore` plays a persona through everyday tasks and reports friction as issues. Use from build for every UI change, and for "check the UI", "click through staging", "explorative UX test", "calibrate ui-check".
argument-hint: change <url> [<base>] | explore <url> <tasks> [persona]
---

# ui-check

A test proves what someone thought of. A browser walk finds what nobody did: a click without feedback, a save that is gone after reload, a note where the user meant to log a call. `<url>` is a local server or a staging host from the world context.

## Rules (both modes)

- 🔴 **Browser: only the chrome-devtools MCP** (it starts Chrome Beta). Never start `Google Chrome.app`; a hook denies it headless or with a debugging port.
- 🔴 **Never production.** The world lists its production hosts under `browser.never` in `overlay.json`; a hook denies them. Without a world context, check only local URLs.
- **World context:** read the context file the world names for ui-check (targets, login, test personas, flows, issue repo, labels). Without one: local only, explore mode reports instead of filing issues.
- **Preflight, or abort:** the start URL (or its health path) answers 200, and after login the start page appears. If either fails, stop with exactly that message. There is no report without content.
- **Output folder in the repo:** `tmp/ui-check-<date>-<slug>/`; check `git check-ignore -q tmp/` first. The MCP saves screenshots and snapshots only below the working directory, not in the scratchpad.
- **Large pages to a file:** `take_snapshot` with `filePath`, then `grep` it. Inline snapshots of long pages flood the context.
- **Login:** read credentials in the shell from the place the world context names; enter them only with `fill`. A password never appears in a report, log, snapshot file, screenshot or issue.
- **Shared environments (staging):** change only data this run created (prefix `UI ` in its names). Write every create or change with object and URL to `changes.md`. At the end undo it backwards, reload to check each line, and name what could not be undone. A state the run cannot create is "not checkable here"; play it locally against the seed instead of touching someone else's data.
- **No personal data** from a shared environment in issues, PRs or reports: say "UI contact 1", not the name.
- **Clean up:** close every page (`close_page`) and end this run's Chrome Beta process. Check `ps -axo pid,command | grep "Google Chrome Beta" | grep -E -- "--headless|--remote-debugging" | grep -v grep`; kill a leftover of this run and name it in the report.

**After every action, three checks**, each noted:
1. **Feedback:** does the page say visibly what happened (toast, text, changed row)?
2. **Effect after reload** (`navigate_page` with `reload`): is the change still there, is the deleted thing gone?
3. **Goal reached:** did the action do what the user wanted, not only what the button says? A success message without effect is a finding.

## Mode change (from build, mandatory for every UI change)

1. **Screens.** List the diff's files that match the globs of lens `ux` (`${CLAUDE_PLUGIN_ROOT}/generated/linsen/index.json`) and map them to routes. A file that changes nothing visible (types, a hook without rendering) is named with "n/a" and why.
2. **Walk each screen** at `<url>` through its states: loading (slow network via `emulate`), empty, error, data, plus every acceptance line a user can see. Layout changed: also at 375 px width. Three checks after every action.
3. **Screenshot per state:** `<screen>-<state>.png` in the output folder.
4. **Report** `report.md`, date and commit in the head: per screen a table `state | result | screenshot`; per visible acceptance line (AE1, …) the numbered steps and the observed result. The verifier takes these lines as evidence.
5. **Findings in your own diff** are defects: fix them, then walk again. Findings outside the diff: name them in the report, do not fix them.
6. **For the PR**, one line: `Screens: <screen>: loading ✓ empty ✓ error ✓ data ✓; … · report tmp/ui-check-…/report.md`, or `Screens: n/a: <why nothing visible changed>`. Without it the PR cannot leave draft (hook).

## Mode explore (persona, before releases and after larger UI changes)

`<tasks>`: flow ids from the world's flow catalogue, `p1` for all priority-1 flows, or a free sentence ("I want to log the call with Anna"). `[persona]`: default "in a hurry, knows the app a little, reads no help".

**Play the persona.** Without this stance the run only finds what a developer finds.
1. Read only the task's title before you start, not its steps. You know what the persona wants, not how the app means it to be done.
2. Take the first plausible path, not the right one. A hurried user types into the field that is open in front of them, opens nothing they are not looking for, reads no small grey text.
3. Three checks after every action (above).
4. Only then read the flow and compare. A difference between the persona's path and the intended path is a finding when the app does not catch it.
5. Every finding gets a screenshot and the exact steps.

**Classes:**

| Class | When | Label |
|---|---|---|
| Data loss | Input or data is gone without the persona wanting it, or an action reports success without effect, or it saves something other than what the persona meant and says nothing | world's blocker label |
| Dead end | The persona reaches the goal on no path they find, or cannot get back; an error page or 4xx/5xx after a normal click | world's blocker label |
| Friction | Goal reached, but with a detour, missing feedback or guessing | world's backlog label |

**Steps:** output folder → preflight → per task: play, collect steps and screenshots → `report.md` (date head; per task goal, path, findings with class and screenshot path, or "no finding") → **only on a staging target with an issue repo in the world context:** one issue per finding. Search duplicates open and closed first (`gh issue list -R <repo> --state all --search "<keyword>"`): open → comment there; closed → new issue "Regression of #<n>". Title names the subject; body: persona, steps, expected, actual, class, flow id; screenshot paths, not uploads; no personal data. Labels from the classes plus `status:idea` → clean up → answer with one table: task · findings per class · issues with keyword · report path.

**Calibration.** A world can list known cases (an old commit, a task, the expected finding). The skill is fit when a run against that commit finds all of them. A run that knows the cases proves little: a fresh agent that gets only this skill and the world context runs it, not the issues.
