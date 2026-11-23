1. The split: which questions are for studying, which are for the test

File	What it is
splits/split_80_20.json	A list. It says which questions the model studies (80%) and which are kept for the test (20%).
splits/make_split.py	Makes that list.
splits/check_split.py	Checks that no test question is also a study question.

2. The fine-tuning files: the steps on the school’s computer

File	What it does
finetune/build_dataset.py	Turns our questions into study material for the model.
finetune/train_lora.py	The model studies. This runs on the school’s computer.
finetune/predict_hf.py	The model takes the test. It writes its answers to a file.

After that, our old file evaluation/evaluate.py gives the score, the same as before.

3. Helper files: you don’t need them now

File	Why it exists
finetune/cargo_cluster_bundle.tar.gz	All the files packed into one, so you upload only one file.
finetune/pack_for_cluster.py	Makes that packed file.
finetune/requirements.txt	The list of Python packages to install on the school’s computer.
finetune/slurm/ (3 files)	Only needed if the school’s computer uses a job queue called SLURM.
finetune/merge_lora.py, finetune/export_gguf.sh, finetune/Modelfile.template	Only needed if you later want to run the trained model in Ollama on your laptop.
finetune/README.md	Instructions.

4. Small changes to old files

evaluation/run_ollama.py and evaluation/evaluate.py can now run or score only the test questions, using --split test.
.gitignore stops big generated files from being committed.

The short version: the split decides study vs test questions, build_dataset.py makes the study material, train_lora.py makes the model study, predict_hf.py makes it take the test, and evaluate.py scores it.

PASS 1 AND PASS 2

Pass 1, Option 1: a model reads the question, the full schema and the data dictionary. It answers with the relevant tables, the relevant columns and a short hint (how to join, filter, group). It doesn’t write SQL. The model can make hints.
Pass 1, Option 2: no model, just search.
BM25 searches the data dictionary for words from the question.
Fuzzy matching finds question words that are real values in the database, for example “Japan” or “FRA”, and which column they’re in.
Pass 2: a second model gets the question and only the chosen tables (with the dictionary), plus the relevant columns, the values found and the hint (Option 1 only). It writes the SQL.
Each attempt has an 8-second limit (--timeout 8).
If the SQL doesn’t run, or the attempt times out, the model gets one more try with the error message.

OPTION 1

Pass 1 with a model (7B coder), Pass 2 a smaller model (1.5B coder) writes the SQL (cryptic):

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   22.5     20.0   90.0    1.57   2.664   89.7  178.88

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   47.5     45.0   97.5   1.102   1.575   50.7  178.93
  moderate               40   20.0     15.0   90.0   1.511   2.109   90.0  179.23
  hard                   40    0.0      0.0   82.5   2.096   3.146  128.3  178.61

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   30.0     26.7   93.3   1.679   3.186   90.8  178.48
  schema_aware           30   40.0     36.7   90.0   1.565   2.541   92.5  179.06
  business_executive     30   13.3     13.3   90.0   1.652   2.893   94.6  179.05
  vague                  30    6.7      3.3   86.7   1.383   1.871   80.8  178.91

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      50.0                90.0                40.0                10.0
  moderate                  40.0                30.0                 0.0                10.0
  hard                       0.0                 0.0                 0.0                 0.0

Outcomes: {'correct': 27, 'wrong_result': 81, 'execution_error': 12}
Prompt tokens per question (mean): 827.8

Pass 1 with a model (7B coder), Pass 2 a smaller model (1.5B coder) writes the SQL (mixed):

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   27.5     21.7   62.5   1.841   3.486  127.1  177.23

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   55.0     47.5   80.0   1.305   1.952   62.1  176.12
  moderate               40   27.5     17.5   65.0   1.676   2.265  121.0  178.77
  hard                   40    0.0      0.0   42.5   2.541    4.03  198.3  176.66

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   30.0     23.3   63.3   1.831   3.379  118.6  177.81
  schema_aware           30   43.3     36.7   76.7   1.778   3.707  122.9  177.95
  business_executive     30   20.0     13.3   50.0   1.969    4.03  156.6  177.04
  vague                  30   16.7     13.3   60.0   1.785   3.009  110.5  176.11

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      70.0                80.0                40.0                30.0
  moderate                  20.0                50.0                20.0                20.0
  hard                       0.0                 0.0                 0.0                 0.0

Outcomes: {'correct': 33, 'wrong_result': 42, 'execution_error': 45}
Prompt tokens per question (mean): 932.4

Pass 1 with a model (7B coder), Pass 2 a smaller model (1.5B coder) writes the SQL (normal):

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   26.7     21.7   72.5   1.406   2.654   88.6  174.14

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   45.0     42.5   92.5   0.866   1.353   39.6  176.66
  moderate               40   35.0     22.5   70.0   1.391   1.985   90.8  175.08
  hard                   40    0.0      0.0   55.0   1.961   2.747  135.5  172.79

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   26.7     20.0   70.0   1.478   2.747   96.2  174.16
  schema_aware           30   40.0     33.3   76.7   1.359   2.573   85.1  174.64
  business_executive     30   20.0     16.7   66.7   1.529   2.829   97.5  173.13
  vague                  30   20.0     16.7   76.7   1.258   2.408   75.7  174.85

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      40.0                60.0                40.0                40.0
  moderate                  40.0                60.0                20.0                20.0
  hard                       0.0                 0.0                 0.0                 0.0

Outcomes: {'correct': 32, 'wrong_result': 55, 'execution_error': 33}
Prompt tokens per question (mean): 869.7


Pass 1 with a model (7B coder), 7B coder writes the SQL (cryptic):

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   38.3     34.2   98.3   2.873   4.893   89.7    51.8

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   77.5     70.0  100.0   1.665   2.604   43.8   52.59
  moderate               40   35.0     32.5  100.0   2.869   4.001   92.0   51.86
  hard                   40    2.5      0.0   95.0   4.085   5.643  133.4   51.51

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   46.7     43.3  100.0   2.919   4.832   88.5   51.74
  schema_aware           30   53.3     46.7   93.3   3.089   6.076  101.5    51.8
  business_executive     30   36.7     33.3  100.0   2.939   5.536   89.6   51.79
  vague                  30   16.7     13.3  100.0   2.545   3.628   79.3   51.88

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      90.0               100.0                90.0                30.0
  moderate                  50.0                50.0                20.0                20.0
  hard                       0.0                10.0                 0.0                 0.0

Outcomes: {'correct': 46, 'wrong_result': 72, 'execution_error': 2}
Prompt tokens per question (mean): 827.8

Pass 1 with a model (7B coder), 7B coder writes the SQL (mixed):

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   42.5     34.2   76.7   3.589   8.431  121.6   51.47

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   82.5     75.0   95.0   1.755   2.291   45.4   52.51
  moderate               40   37.5     22.5   70.0    3.56   6.962  125.3   51.74
  hard                   40    7.5      5.0   65.0   5.452   9.664  194.0   51.06

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   40.0     30.0   73.3   3.745   9.664    126   51.45
  schema_aware           30   66.7     56.7   86.7   3.722   8.431  128.8   51.47
  business_executive     30   36.7     26.7   73.3   3.403   8.962  112.8   51.53
  vague                  30   26.7     23.3   73.3   3.486    7.47  118.6   51.43

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      90.0               100.0                80.0                60.0
  moderate                  30.0                70.0                30.0                20.0
  hard                       0.0                30.0                 0.0                 0.0

Outcomes: {'correct': 51, 'wrong_result': 41, 'execution_error': 28}
Prompt tokens per question (mean): 932.4

Pass 1 with a model (7B coder), 7B coder writes the SQL (normal):

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   45.8     39.2   83.3   2.663   6.236   85.1   51.59

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   87.5     82.5  100.0   1.256   1.695   31.0   52.96
  moderate               40   40.0     27.5   82.5   2.704   4.529   89.8   51.73
  hard                   40   10.0      7.5   67.5   4.028   6.939  134.5   51.19

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   50.0     43.3   76.7   2.768   6.602   90.6   51.58
  schema_aware           30   66.7     56.7   93.3   2.589   6.024   85.2   51.69
  business_executive     30   40.0     33.3   80.0   2.876   6.747   90.7   51.44
  vague                  30   26.7     23.3   83.3   2.419   5.208   73.9   51.65

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                     100.0               100.0                90.0                60.0
  moderate                  40.0                70.0                30.0                20.0
  hard                      10.0                30.0                 0.0                 0.0

Outcomes: {'correct': 55, 'wrong_result': 45, 'execution_error': 20}
Prompt tokens per question (mean): 869.7



OPTION 2

Pass 1 Fuzzy String and BM25 Experiment(cryptic), coder 7B writes the SQL:

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   36.7     31.7   95.0   2.386   5.029   89.2   50.92

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   80.0     75.0  100.0   1.339   1.931   40.4   51.78
  moderate               40   25.0     17.5   97.5   2.246   3.458   86.6   51.08
  hard                   40    5.0      2.5   87.5   3.574   6.649  140.7   50.59

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   43.3     36.7   90.0   2.472   5.029   91.8    50.9
  schema_aware           30   46.7     40.0   90.0     2.8   6.649   98.7   50.61
  business_executive     30   30.0     26.7  100.0   2.365   5.342   91.6   50.86
  vague                  30   26.7     23.3  100.0   1.907   3.416   74.9   51.46

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      90.0               100.0                70.0                60.0
  moderate                  30.0                30.0                20.0                20.0
  hard                      10.0                10.0                 0.0                 0.0

Outcomes: {'correct': 44, 'wrong_result': 70, 'execution_error': 6}
Prompt tokens per question (mean): 2119.6

Pass 1 Fuzzy String and BM25 Experiment(mixed), coder 7B writes the SQL:

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   39.2     32.5   85.0   2.749   7.217  104.5   50.69

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   75.0     72.5   95.0   1.387    3.01   45.1   51.43
  moderate               40   32.5     20.0   80.0   2.593   4.686  101.7   50.85
  hard                   40   10.0      5.0   80.0   4.266    8.44  166.8   50.39

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   50.0     40.0   76.7   2.757   6.065  103.4   50.68
  schema_aware           30   50.0     43.3   93.3   2.772   7.381  104.1    50.5
  business_executive     30   30.0     23.3   80.0   3.207    8.44  118.3   50.56
  vague                  30   26.7     23.3   90.0   2.258   5.036   92.3   51.07

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      80.0               100.0                60.0                60.0
  moderate                  40.0                40.0                30.0                20.0
  hard                      30.0                10.0                 0.0                 0.0

Outcomes: {'correct': 47, 'execution_error': 18, 'wrong_result': 55}
Prompt tokens per question (mean): 2015.2

Pass 1 Fuzzy String and BM25 Experiment(normal), coder 7B writes the SQL:

Overall
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  all                   120   35.8     32.5   83.3   2.124   5.341   80.8   51.16

By difficulty
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  easy                   40   77.5     75.0  100.0   0.997     1.6   31.1   52.47
  moderate               40   30.0     22.5   82.5    2.17    3.93   82.5   51.27
  hard                   40    0.0      0.0   67.5   3.231   5.892  130.1   50.79

By style
                          n    EX%  strict%   VER%   lat s   p95 s    tok   tok/s
  casual                 30   36.7     33.3   76.7   2.287   4.944   83.8   51.12
  schema_aware           30   53.3     46.7   90.0   2.267   5.383   84.1   50.87
  business_executive     30   30.0     26.7   80.0   2.268   5.631   89.7   51.09
  vague                  30   23.3     23.3   86.7   1.678   4.029   65.9    51.7

EX % by difficulty x style
                          casual        schema_aware  business_executive               vague
  easy                      80.0               100.0                70.0                60.0
  moderate                  30.0                60.0                20.0                10.0
  hard                       0.0                 0.0                 0.0                 0.0

Outcomes: {'correct': 43, 'wrong_result': 57, 'execution_error': 19, 'missing': 1}
Model calls that failed or timed out (1, scored as missing, left out of latency/token metrics): H08-BIZ
Prompt tokens per question (mean): 1895.2
