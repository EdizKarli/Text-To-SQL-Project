No Schema Experiment

We made a mistake while giving a prompt to the model during no-schema experiments.
We didn't give any schema but evidence was still given for reasoning and since some of the evidences
(like "born in 1980 refers to YEAR(BIRTHDAY) = '1980'") has some information about the database, the model was able to guess
1.80 percent of the sql queries correct. This time only the question was given to the model, no schema, no evidence. Results:

Total Questions Evaluated     : 500
Execution Accuracy (EX)       : 0.00% (0/500)
Valid Execution Rate          : 0.00% (0/500)
Average Latency / Query       : 3.216 s
Total Successful Blind Guesses: 0

