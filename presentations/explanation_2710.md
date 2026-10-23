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