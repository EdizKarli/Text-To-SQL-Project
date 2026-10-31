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
  all                   480   39.0     33.1   77.1     4.0   4.695   53.2   63.46   47.49

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  easy                  160   78.8     76.2   97.5   2.817   3.052   23.4  120.36   44.08
  moderate              160   33.8     21.9   75.0   3.292   4.016   50.5   65.15    47.6
  hard                  160    4.4      1.2   58.8   5.892   5.753   85.9   46.88   48.45

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok  ms/tok   tok/s
  casual                120   41.7     35.0   78.3   3.499   4.725   55.8   62.73   47.52
  schema_aware          120   59.2     50.0   72.5   3.467   4.712   58.7   59.08   48.05
  business_executive    120   35.0     29.2   76.7   3.358   4.496   53.4   62.91    47.5
  vague                 120   20.0     18.3   80.8   5.676    4.31   45.0   70.82   46.73

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      90.0                97.5                77.5                50.0
  moderate                  32.5                67.5                25.0                10.0
  hard                       2.5                12.5                 2.5                 0.0

Outcomes: {'correct': 187, 'wrong_result': 183, 'execution_error': 110}
Prompt tokens per question (mean): 3013.0