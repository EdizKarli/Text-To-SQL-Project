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
  all                   480   34.2     29.4   70.8     3.5    5.19   59.6   58.71   47.58

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  easy                  160   74.4     71.2   97.5   2.844   3.259   26.2  108.64   44.95
  moderate              160   23.1     15.0   61.2   3.479   4.362   59.2   58.81   47.63
  hard                  160    5.0      1.9   53.8   4.178   5.592   93.5   44.67   48.35

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  casual                120   36.7     30.8   68.3   3.599   5.375   62.8   57.35   47.51
  schema_aware          120   53.3     45.0   68.3   3.577   5.299   63.6   56.23   47.98
  business_executive    120   32.5     27.5   70.0   3.515   4.988   61.0   57.65   47.58
  vague                 120   14.2     14.2   76.7    3.31   4.475   51.1   64.72   47.19

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      85.0                92.5                80.0                40.0
  moderate                  22.5                55.0                12.5                 2.5
  hard                       2.5                12.5                 5.0                 0.0

Outcomes: {'correct': 164, 'wrong_result': 176, 'execution_error': 140}
Prompt tokens per question (mean): 3293.7