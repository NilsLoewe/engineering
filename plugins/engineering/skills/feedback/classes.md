# Classes: edge cases

Taken from a real PR (11/2026) with 41 human review threads, 8 points in review bodies and 7 QA questions.

**a bug, not d style:** a "nit" that loses an event or a trace is a bug. Example: an import task padded an e-mail address with leading zeros, so it never matched.

**b spec gap, not a bug:** the reviewer asks "should we" or "ask the PO whether". It is also b when the fix needs a number nobody set (a time window, a cap, a limit). Examples: one sender address = one property; does the mail subject reach the keyholder; how old may a mail be before it goes to History.

**b, even when it is a go-live step:** setup data and rollout that QA needs to test (defaults per device type, deploy order, poll interval). They go into the spec under **For developers** or as an acceptance precondition. The PR text does not count.

**QA questions are b by default.** QA asks because the ticket is silent. Test setup (environment, mailbox, test account) is a question for the owner. The code cannot answer it.

**c, not b:** the change sits in another repo or would need a new contract, e.g. a Message-ID in the mail line for de-duplication. The spec names it under **Not included**.

**d, but repeated:** in that PR "comment too long or carries history" came 7 times and "PR text no longer matches the code" 9 times (human and agent review together). A rule that already exists and still repeats points to a cause: the PR text carried the spec, so it grew to 31 KB and went stale.
