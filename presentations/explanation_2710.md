No Schema Experiment

7B Coder
We made a mistake while giving a prompt to the model during no-schema experiments.
We didn't give any schema but evidence was still given for reasoning and since some of the evidences
(like "born in 1980 refers to YEAR(BIRTHDAY) = '1980'") has some information about the database, the model was able to guess
1.80 percent of the sql queries correct. This time only the question was given to the model, no schema, no evidence. Results:

Total Questions Evaluated     : 500
Execution Accuracy (EX)       : 0.00% (0/500)
Valid Execution Rate          : 0.00% (0/500)
Average Latency / Query       : 3.216 s
Total Successful Blind Guesses: 0

Total Evidence Experiment

7B Coder
We combined the evidences given in Bird Mini Dev and put them in a dictionary. So the model doesn't get the evidence of the question it is trying to solve during the prompt creatin process, it searches the dictionary for clues. We used fuzzy string and BM25 for dictonary searching. Here are the results:

Total Questions Evaluated : 500
Execution Accuracy (EX)   : 38.80% (194/500)
Valid Execution Rate      : 84.00% (420/500)
Average Latency / Query   : 3.443 s

We also did the same experiment without fuzzy string and BM25, this way the model itself searches the entire dictionary. Here are the results:

Total Questions Evaluated : 500
Execution Accuracy (EX)   : 37.20% (186/500)
Valid Execution Rate      : 71.00% (355/500)
Average Latency / Query   : 3.375 s

Slight increase in latency, small decrease in accuracy.

----------------------------------------------------------

QUANTIZATION

7B qwen 2.5 coder with these quantization levels was used:
FP16, Q8_0, Q5_K_M, Q4_K_M

Given-Schema (improved, column names and primary-foreign keys are also given) and Pruned Vol 2 versions were used (fuzzy string and BM25 with no restrictions and all of the foreign-primary keys given).

For Q4_K_M:
Schema Given results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   61.49                43.60                27.45                45.60               

Pruned Vol2 results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   62.16                40.40                27.45                44.20               

For Q5_K_M:
Schema Given results:
                    simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   62.84                44.00                28.43                46.40               

Pruned Vol2 results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   62.16                40.40                31.37                45.00  

For Q8_0:
Schema Given Results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   62.84                42.00                32.35                46.20    

Pruned Vol2 Results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   62.84                43.20                30.39                46.40   

Then we decided to try something different. We decided to use 14B parameter model with Q4_K_M, this would reduce the storage by 70 percent (from 30 GBs to 9 GBs). 
For 14B parameter model, Q4_K_M quantization:
Schema Given Results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   69.59                47.60                37.25                52.00      

Pruned Vol2 Results:
                     simple               moderate             challenging          total               
count                148                  250                  102                  500                 
======================================    EX    =====================================
EX                   63.51                44.00                37.25                48.40               
