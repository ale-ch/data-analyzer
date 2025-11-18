from llama_cpp import Llama

model_path = "/Users/work/Documents/Programming/test/hf_test2/merged.gguf"
# model_path="qwen2.5-7b-instruct-q5_k_m.gguf"
model_path = "/Users/work/Documents/Programming/test/analyzer_test/qwen2.5-7b-instruct-q5_k_m.gguf"

llm = Llama(
    model_path=model_path,
    n_ctx=4096,
)

out = llm(
    "What is the capital of France?",
    max_tokens=200,
)

print(out["choices"][0]["text"])

