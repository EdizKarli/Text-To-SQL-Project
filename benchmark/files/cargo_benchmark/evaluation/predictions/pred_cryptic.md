n = Number of questions in that row.
EX% = Execution accuracy
Strict% = EX but rows and columns must come out in exactly the Gold order
VER% = Valid execution rate
lat s = Latency
p95 s = 95% of questions finished within this time, so it shows the slow tail.
tok = Tokens created
ms/tok = Latency per token
tok/s = Tokens per second

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  all                   480   16.5     15.4   92.1   3.287   4.582   49.9   65.91   47.33

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  easy                  160   41.9     41.2   98.1   2.796    3.06   24.9  112.11   44.41
  moderate              160    6.2      5.0   87.5   3.216   4.106   46.4   69.31   46.95
  hard                  160    1.2      0.0   90.6   3.848    5.01   78.3   49.16   48.59

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  casual                120   10.0     10.0   89.2   3.404   4.693   55.0   61.95   47.38
  schema_aware          120   41.7     37.5   90.8   3.378   4.746   54.3   62.19   47.96
  business_executive    120   10.0     10.0   90.0   3.307   4.561   51.1   64.76   47.27
  vague                 120    4.2      4.2   98.3   3.058   4.012   39.2    78.1   46.49

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      27.5                97.5                30.0                12.5
  moderate                   2.5                22.5                 0.0                 0.0
  hard                       0.0                 5.0                 0.0                 0.0

Outcomes: {'wrong_result': 363, 'correct': 79, 'execution_error': 38}
Prompt tokens per question (mean): 3215.8
