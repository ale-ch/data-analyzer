import pandas as pd
from llama_cpp import Llama



file = "/Users/work/Documents/Programming/test/ITA_TEST/output/firms_data.csv"
model_path = "/Users/work/Documents/Programming/test/analyzer_test/qwen2.5-7b-instruct-q5_k_m.gguf"


df = pd.read_csv(file)

colnames = df.columns

print(colnames)

prompt = f"Describe what each variable means, and provide analysis ideas. Variable names: {colnames}"


llm = Llama(
    model_path=model_path,
    n_ctx=4096,
    verbose=False
)

out = llm(
    prompt,
    max_tokens=8000,
)

print(out["choices"][0]["text"])

