# Expected results (deterministic)

The dataset is fixed, so every correct implementation must produce exactly these answers. Use this table to
self-check your SQL and Cypher output before screenshots. (Timings are NOT listed: they depend on your machine.)

## Q1 outgoing count / total RWF in 09:45-10:45 CAT

| Set | account | count | total RWF |
|---|---|---|---|
| A | 998 | 1 | 200,000 |
| B | 147228 | 1 | 1,050,000 |
| C | 206978 | 1 | 300,000 |
| D | 237998 | 1 | 45,000 |
| E | 144228 | 1 | 40,000 |
| F | 203978 | 1 | 30,000 |

## Q2 daily activity

30 rows; totals reconcile to capture (20,003,300 transfers; 231,482,327,870 RWF). First day: ['2026-09-01', 666667, 7683326000]; last day: ['2026-09-30', 666666, 7684945400].

## Q3 shared-device rows (other account, device, ...)

| Set | rows |
|---|---|
| A | 4 |
| B | 9 |
| C | 9 |
| D | 4 |
| E | 9 |
| F | 9 |

## Q4 distinct other accounts reached (all regions summed) by depth

| Set | 4 | 6 | 8 | 10 |
|---|---|---|---|---|
| A | 10 | 43 | 175 | 187 |
| B | 46 | 178 | 188 | 228 |
| C | 146 | 483 | 832 | 1433 |
| D | 10 | 44 | 180 | 192 |
| E | 47 | 183 | 193 | 230 |
| F | 147 | 488 | 837 | 1426 |

## Q5 rapid-onward chains and Q6 cycles

| Set | Q5 chains | Q5 transfer IDs (t1,t2,t3 -> final) | Q6 cycles | Q6 lengths |
|---|---|---|---|---|
| A | 1 | 20000001,20000002,20000003 -> 24755 | 1 | 4 |
| B | 1 | 20000092,20000093,20000094 -> 170985 | 0 | - |
| C | 1 | 20000229,20000230,20000231 -> 230735 | 1 | 6 |
| D | 0 | - | 0 | - |
| E | 0 | - | 0 | - |
| F | 0 | - | 0 | - |

## Q7 minimum transfer length (person-only route); none = no route within the bound

| Set | bound 4 | bound 6 |
|---|---|---|
| A | 3 | 3 |
| B | none | 5 |
| C | none | 5 |
| D | 3 | 3 |
| E | none | 5 |
| F | none | 5 |
