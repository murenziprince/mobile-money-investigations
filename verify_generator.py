"""verify_generator.py - prove mobile_money_generator.py is unchanged (Section 9.2).

  python verify_generator.py          # compares its SHA-256 with generator.sha256 (recorded from the supplied file)
Before first use: replace generator.sha256 with the hash of YOUR original download if it differs
(compute it on the untouched file:  python -c "import hashlib;print(hashlib.sha256(open('mobile_money_generator.py','rb').read()).hexdigest())").
"""
import hashlib
import os
import sys

root = os.path.dirname(os.path.abspath(__file__))
actual = hashlib.sha256(open(os.path.join(root, "mobile_money_generator.py"), "rb").read()).hexdigest()
expected = open(os.path.join(root, "generator.sha256")).read().split()[0]
print("actual  :", actual)
print("expected:", expected)
print("UNCHANGED" if actual == expected else "CHANGED - restore the original file!")
sys.exit(0 if actual == expected else 1)
