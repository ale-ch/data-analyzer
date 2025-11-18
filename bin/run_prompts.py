import logging
from bin.call_llm import safe_llm_call

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_prompts(prompts, llm):
    results = {}

    # Run all prompts safely
    for key, prompt in prompts.items():
        logging.info(f"Processing: {key}")
        results[key] = safe_llm_call(prompt, key, llm)

    logging.info("All prompts processed with safety wrapper.")

    return results