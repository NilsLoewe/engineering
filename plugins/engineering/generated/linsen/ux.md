<!-- Erzeugt von tools/build_katalog.py aus katalog/. Nicht von Hand ändern. -->
# Lens: UX: states, feedback, controls and wording

Intent: a user always knows what the screen shows, what just happened and what to do next. A finding names the user, the moment and what they miss or misread; a matter of taste is not a finding. Missing outcome, error or empty state is major; layout and wording are minor.

- Every user-triggered async action shows visible feedback within 400 ms, blocks a second submit while pending and reports success or failure; a click that changes nothing visible is a bug. (severity: major) `[ux-async-feedback]`
- Every list, table and detail view handles loading, empty (says why, offers the way out, shows the active search and filters), error (what failed, what to do, retry) and data. (severity: major) `[ux-four-states]`
- An error the user must read does not disappear on its own; success and routine news never open a modal dialog. (severity: major) `[ux-errors-stay]`
- The end of a flow states the outcome (what was saved or sent, where it is now) and offers the next step. (severity: minor) `[ux-end-of-flow]`
- Solve a known interaction (filters, row actions, dialogs, save/cancel) with the same component, wording, position and order as the existing screens, and name the screen you followed. (severity: minor) `[ux-like-the-siblings]`
- Never carry meaning (status, priority, validation error) by colour alone; add text or an icon. (severity: minor) `[ux-not-colour-alone]`
- Texts the user reads use domain language, never enum keys, HTTP codes or model names; a button is verb plus object; every number carries its unit. (severity: minor) `[ux-domain-words]`
- A dialog shows the object it acts on by name, not only an id; filters, sorting, page and form input survive navigating away and back. (severity: minor) `[ux-context-in-dialog]`
- One primary action per dialog or form; a destructive action uses the destructive style, never the primary one, and never sits directly beside a frequent action. (severity: minor) `[ux-one-primary-action]`
- An irreversible action needs a confirmation that names the object and the action, or an undo; a recoverable routine action gets no confirmation. (severity: major) `[ux-confirm-only-irreversible]`
- Accept input as people type it (spaces, dashes, decimal comma, surrounding whitespace), prevent invalid input with bounded controls, and keep the input after a failed submit. (severity: minor) `[ux-forgiving-input]`
- A disabled control says why it is disabled, next to it or in a tooltip. (severity: minor) `[ux-disabled-says-why]`
- Icon-only buttons have an accessible name; click targets are at least 24x24 px; links navigate and buttons act. (severity: minor) `[ux-accessible-controls]`
- Colours, spacing and font sizes come from the app's design tokens or theme; no hard-coded values and no token marked deprecated. (severity: minor) `[ux-design-tokens]`
