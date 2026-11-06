build_dataset.py prepares the study material. It takes our questions and their correct answers and writes them as practice examples the model can learn from. The practice examples only use training questions; the test questions are left out.
train_lora.py does the learning. You run it on the school’s GPU, and it teaches the model using those examples. The result is a small “add-on” file for the model.
predict_hf.py takes the exam. The trained model answers the test questions, and our usual evaluate.py then scores them, the same way it scores Ollama runs.

So: prepare, learn, take the exam, check the score.
pack_for_cluster.py and cargo_cluster_bundle.tar.gz just pack everything into one file so it’s easy to upload.
slurm folder is for school computers where you have to submit jobs into a queue instead of running programs directly. If the school’s machine works differently, you won’t need it.
merge_lora.py, export_gguf.sh, Modelfile.template are only needed if you want to run the trained model in Ollama on your own laptop later.
requirements.txt lists the Python packages to install on the school’s machine.