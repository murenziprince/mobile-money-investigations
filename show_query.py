"""show_query.py - print the paired SQL and Cypher text for one question (screenshot: "query pair").

  python show_query.py q4            # also: q1 q2 q3 q5 q6 q7 (q7 shows baseline v1, improved v2 and path queries)
"""
import sys

from queries import read_query

NAMES = {"q7": ["q7_v1.sql", "q7_v2.sql", "q7_path.sql", "q7.cypher", "q7_path.cypher"],
         "q4": ["q4.sql", "q4.cypher", "q4_path.sql", "q4_path.cypher"]}

q = (sys.argv[1] if len(sys.argv) > 1 else "q1").lower()
for name in NAMES.get(q, [f"{q}.sql", f"{q}.cypher"]):
    print(f"\n{'=' * 8} {name} {'=' * 8}\n{read_query(name)}")
