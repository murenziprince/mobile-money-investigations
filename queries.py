"""queries.py - loads the paired SQL/Cypher files and builds the 61 comparison cases (Section 6.1)."""
import os

from config import SETS, ROOT, set_params

QDIR = os.path.join(ROOT, "queries")
DEPTHS = (4, 6, 8, 10)
BOUNDS = (4, 6)


def read_query(filename):
    with open(os.path.join(QDIR, filename), encoding="utf-8") as f:
        return f.read().strip()


def sql_text(case, q7="v1"):
    q = case["q"]
    if q == "Q7":
        return read_query(f"q7_{q7}.sql")
    return read_query(f"{q.lower()}.sql")


def cypher_text(case, path=False):
    q = case["q"]
    name = "q7_path.cypher" if (q == "Q7" and path) else f"{q.lower()}.cypher"
    text = read_query(name)
    # Cypher cannot parameterize path bounds: substitute validated integers into the text.
    if q == "Q4":
        text = text.replace("{depth}", str(int(case["params"]["depth"])))
    if q == "Q7":
        text = text.replace("{bound}", str(int(case["params"]["bound"])))
    return text


def params_for(case):
    return dict(case["params"])


def build_cases():
    """The 61 cases: Q1 x6, Q2 x1, Q3 x6, Q4 x24, Q5 x6, Q6 x6, Q7 x12."""
    cases = []
    def add(q, label, **extra):
        p = set_params(label) if label else {}
        p.update(extra)
        tag = f"{q}-{label}" if label else q
        if "depth" in extra:
            tag += f"-d{extra['depth']}"
        if "bound" in extra:
            tag += f"-b{extra['bound']}"
        cases.append(dict(id=tag, q=q, set=label, params=p))
    for s in SETS:
        add("Q1", s)
    add("Q2", None)
    for s in SETS:
        add("Q3", s)
    for s in SETS:
        for d in DEPTHS:
            add("Q4", s, depth=d)
    for s in SETS:
        add("Q5", s)
    for s in SETS:
        add("Q6", s)
    for s in SETS:
        for b in BOUNDS:
            add("Q7", s, bound=b)
    assert len(cases) == 61
    return cases


if __name__ == "__main__":
    cs = build_cases()
    print(len(cs), "cases;", [c["id"] for c in cs][:8], "...")
