n = Number of questions in that row.
EX% = Execution accuracy
Strict% = EX but rows and columns must come out in exactly the Gold order
VER% = Valid execution rate
lat s = Latency
p95 s = 95% of questions finished within this time, so it shows the slow tail.
tok = Average of the tokens created for the answer
tok/s = Tokens per second

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok    tok/s
  all                   120   41.7     35.8   90.0   3.554     4.9   59.5    46.71

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   90.0     82.5  100.0   2.841   2.924   23.2   44.06
  moderate               40   27.5     20.0   87.5   3.769   5.112   70.7   46.94
  hard                   40    7.5      5.0   82.5   4.051   4.853   84.5   47.31

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   46.7     40.0   93.3   3.737   4.876   65.8   47.08
  schema_aware           30   50.0     43.3   80.0   3.559   5.289   60.5   47.21
  business_executive     30   40.0     33.3   96.7   3.584   5.112   61.5   46.51
  vague                  30   30.0     26.7   90.0   3.336   4.772   50.1   45.92
