#!/usr/bin/env python3
"""Self-test for ready_check.py and pr_check.py."""
import json, os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import pr_check, ready_check  # noqa: E402

SPEC = """[engineering:spec]
Problem: Controllers cannot see intervention times, so SLA disputes take a day.
Acceptance examples:
- AE1: Given an event with two interventions, When the controller opens it, Then both times are listed.
- AE2 (edge): Given an event without interventions, When opened, Then the column is empty.
Open questions: none
Repos/interfaces: api-repo (GraphQL Alarm.interventions), web-repo
"""


class Ready(unittest.TestCase):
    def test_complete_spec_is_ready(self):
        self.assertEqual(ready_check.check(ready_check.latest_block(SPEC)), [])

    def test_missing_edge_and_open_question(self):
        s = SPEC.replace(" (edge)", "").replace("Open questions: none",
                                                  "Open questions:\n- Q1: How many types? Proposal: one.")
        m = ready_check.check(s)
        self.assertEqual(len(m), 2, m)

    def test_wrapped_question_counts_once(self):
        s = SPEC.replace("Open questions: none", "Open questions:\n- Q1: How many types,\n  and which codes? Proposal: one.")
        self.assertIn("1 open question(s)", ready_check.check(s))

    def test_table_examples_count_rows_not_header(self):
        s = SPEC.split("Acceptance")[0] + ("Acceptance examples:\n| case | input | result |\n|---|---|---|\n"
                                           "| (error) unknown id | 999 | 404 |\nOpen questions: none\nRepos: web-repo\n")
        self.assertEqual(ready_check.check(s), [])

    def test_latest_block_from_tracker_json(self):
        old = SPEC.replace("Open questions: none", "Open questions:\n- Q1: x")
        j = json.dumps({"body": "desc", "comments": [{"body": old}, {"body": "noise"}, {"body": SPEC}]})
        self.assertEqual(ready_check.check(ready_check.latest_block(j)), [])
        self.assertIsNone(ready_check.latest_block(json.dumps({"body": "x", "comments": []})))

    def test_markdown_headings(self):
        s = SPEC.replace("Problem:", "**Problem:**").replace("Acceptance examples:", "### Acceptance examples:")
        self.assertEqual(ready_check.check(s), [])


GOOD_PR = """Closes https://github.com/o/r/issues/7

Adds intervention times to the event view; controllers asked for SLA evidence.

Evidence
- AE1: spec/requests/event_spec.rb:40 passes
- AE2: not proven (no fixture)

Risk: new N+1 on event list, covered by bullet gem in CI.
"""


class PR(unittest.TestCase):
    def test_good(self):
        self.assertEqual(pr_check.check(GOOD_PR), [])

    def test_monday_and_short_refs(self):
        for ref in ("https://example.monday.com/boards/100/pulses/200300400", "o/r#7", "#7"):
            self.assertEqual(pr_check.check(GOOD_PR.replace("https://github.com/o/r/issues/7", ref)), [])

    def test_budget_link_evidence_spec_copy(self):
        bad = "\n".join(f"line {i}" for i in range(20)) + "\nOpen questions: none"
        self.assertEqual(len(pr_check.check(bad)), 4)

    def test_html_comments_do_not_count(self):
        body = GOOD_PR + "\n".join("<!-- template hint -->" for _ in range(20))
        self.assertEqual(pr_check.check(body), [])


NEW = """🤖 clarify · spec · 06.11.2026 18:00

**Goal:** The free text of a device message shows in the event, as in the old system.

**Acceptance**
1. Signal with text → "Meldergruppe 1 · MK Tuere"
2. (edge) Signal without text → line as today

**Not included:** wrong event mapping, own ticket

**Open questions:** none

**For developers:** vds-box-manager (provider), api-repo, web-repo
"""


class ReadyNewFormat(unittest.TestCase):
    def test_new_format_is_ready(self):
        self.assertEqual(ready_check.check(ready_check.latest_block(NEW)), [])

    def test_heading_after_questions_is_not_a_question(self):
        s = SPEC.replace("Open questions: none", "Open questions: none\nOut of scope: x\nVerification: y")
        self.assertEqual(ready_check.check(ready_check.latest_block(s)), [])

    def test_chained_acceptance_line(self):
        s = NEW.replace("2. (edge) Signal without text", "2. (edge) Operator opens it and then closes it, signal without text")
        self.assertTrue(any("chain steps" in m for m in ready_check.check(ready_check.latest_block(s))))

    def test_answered_questions_are_not_open(self):
        s = NEW.replace("**Open questions:** none", "**Open questions for Bob**\n1. Where? Proposal: here → yes\n2. How long? → no: 80")
        self.assertEqual(ready_check.check(ready_check.latest_block(s)), [])

    def test_two_decisions_in_one_question(self):
        s = NEW.replace("**Open questions:** none", "**Open questions for Ada**\n4. **What is the callback? And alert on loss?** Proposal: x")
        self.assertTrue(any("ask two things" in m for m in ready_check.check(ready_check.latest_block(s))))

    def test_open_question_in_new_format(self):
        s = NEW.replace("**Open questions:** none", "**Open questions:**\n1. Where? Proposal: here")
        self.assertIn("1 open question(s)", ready_check.check(ready_check.latest_block(s)))


DE = """🤖 clarify · spec · 07.11.2026 12:21

**Spec v2** · wartet auf Nils

**Befund:** Der Plan fehlt in „Heute“.

**Ziel:** Nils sieht um 06:30 einen begründeten Tagesplan.

**Akzeptanz**
1. Agent läuft 06:30 → `GET /heute` liefert `plan` mit 3–5 Blöcken.
2. (Grenze) Kalender hat 6 Blocker → Plan hat genau 5 Blöcke.
3. (Fehler) Kalender nicht lesbar → „Heute“ zeigt „kein Plan: <Grund>“.

**Nicht enthalten:** Schreiben in den Kalender.

**Für Entwickler:** lifeOS zuerst, dann 10x, dann die App.

**Offene Fragen an Nils** · bitte auf diesen Kommentar antworten
1. **Was zählt N?** Vorschlag: die geparkten Items. → ja
"""


class ReadyGerman(unittest.TestCase):
    def test_heading_tail_is_not_a_question_when_all_answered(self):
        en = ("🤖 clarify · spec\n**Goal:** x.\n**Acceptance**\n1. (edge) a → b\n**For developers:** repo\n"
              "**Open questions for Nils** · please reply to this comment\n1. **How many?** Proposal: one. → yes\n")
        self.assertEqual(ready_check.check(ready_check.latest_block(en)), [])

    def test_german_spec_is_ready(self):
        self.assertEqual(ready_check.check(ready_check.latest_block(DE)), [])

    def test_german_open_question_and_missing_edge(self):
        s = DE.replace(" → ja", "").replace("(Grenze) ", "").replace("(Fehler) ", "")
        m = ready_check.check(ready_check.latest_block(s))
        self.assertIn("1 open question(s)", m)
        self.assertTrue(any("edge or error" in x for x in m), m)

    def test_german_two_decisions_in_one_question(self):
        s = DE.replace("Was zählt N?** Vorschlag:", "Was zählt N? Und wann?** Vorschlag: x?").replace(" → ja", "")
        self.assertTrue(any("ask two things" in x for x in ready_check.check(ready_check.latest_block(s))))


if __name__ == "__main__":
    unittest.main()
