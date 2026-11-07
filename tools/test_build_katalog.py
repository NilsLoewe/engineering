#!/usr/bin/env python3
"""Selbsttest für build_katalog.py: python3 tools/test_build_katalog.py"""
from build_katalog import build, load, LINSE_MAX_REGELN

L = [{"name": "x", "titel": "X", "stack": "backend", "pfade": ["app/*"]}]
K = [{"id": "kern-a", "regel": "Short.", "abgeleitet_von": ["r1"]}]


def regel(i, linse="x"):
    return {"id": f"r{i}", "regel": f"Rule {i}.", "linse": linse, "stufe": "linse", "status": "aktiv", "belege": i}


def raises(*args):
    try:
        build(*args)
    except ValueError as e:
        return str(e)
    raise AssertionError("kein Abbruch")


def test():
    files = build(L, K, [regel(1), regel(2)])
    assert files["linsen/x.md"].index("Rule 2.") < files["linsen/x.md"].index("Rule 1.")  # nach Belegen
    assert "kern-a" in files["kern.md"]
    assert "Budget" in raises(L, K, [regel(i) for i in range(1, LINSE_MAX_REGELN + 2)])
    assert "Budget" in raises(L, [{"id": "kern-b", "regel": "x" * 3000}], [regel(1)])
    assert "doppelt" in raises(L, K, [regel(1), regel(1)])
    assert "fehlt" in raises(L, K, [regel(1, "y")])
    assert "existiert nicht" in raises(L, K, [regel(2)])
    ausgemustert = regel(3) | {"status": "ausgemustert"}
    assert "Rule 3." not in build(L, K, [regel(1), ausgemustert])["linsen/x.md"]
    build(*load())  # der echte Katalog hält seine Budgets


if __name__ == "__main__":
    test()
    print("ok")
