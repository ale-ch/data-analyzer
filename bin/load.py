import logging
import pandas as pd
from llama_cpp import Llama

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def load_data(data_path):
    df = pd.read_csv(data_path)
    logging.info(f"Data loaded with {df.shape[0]} rows and {df.shape[1]} columns.")

    return df

def load_llm_model(model_path):
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,
        verbose=False
    )

    logging.info("LLaMA model loaded.")

    return llm

def load_user_objective(objective_path):
    with open(objective_path) as f:
        user_objective = f.read().strip()

    logging.info("Objective loaded.")

    return user_objective