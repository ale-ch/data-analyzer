import logging

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def safe_llm_call(prompt, label, llm):
    attempts = [
        2048,   # try full size
        1024,   # smaller
        512,    # smaller
        256     # emergency
    ]

    for max_toks in attempts:
        try:
            logging.info(f"{label}: trying max_tokens={max_toks}")
            out = llm(prompt, max_tokens=max_toks)
            return out["choices"][0]["text"]
        except ValueError as e:
            if "exceed context window" in str(e):
                logging.warning(f"{label}: context window exceeded at {max_toks}. Retrying...")
                continue
            else:
                raise e

    # If still too large, truncate the prompt and retry once
    logging.warning(f"{label}: prompt still too large. Truncating prompt by 50% and retrying.")

    truncated = prompt[: len(prompt) // 2 ]

    try:
        out = llm(truncated, max_tokens=256)
        return "[TRUNCATED PROMPT USED]\n" + out["choices"][0]["text"]
    except Exception as e:
        logging.error(f"{label}: failed even after truncation: {e}")
        return "[ERROR: Failed to process this section]"