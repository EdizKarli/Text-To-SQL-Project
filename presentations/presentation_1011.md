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

