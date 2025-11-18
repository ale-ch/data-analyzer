import json
import logging
import re

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def get_relevant_variables(df, llm, user_objective):
    logging.info("Preparing column preview for relevance filtering...")

    col_preview = {
        col: {
            "dtype": str(df[col].dtype),
            "sample_values": df[col].dropna().unique()[:5].tolist()
        }
        for col in df.columns
    }

    logging.info("Running relevance selection prompt...")

    relevance_prompt = (
        "You are given:\n"
        "1. A user analysis objective.\n"
        "2. Column names, dtypes, and a sample of values.\n\n"
        "Identify which variables are relevant for the objective. "
        "Return JSON with keys: relevant, irrelevant, rationale.\n\n"
        f"OBJECTIVE:\n{user_objective}\n\n"
        f"VARIABLES:\n{json.dumps(col_preview, indent=2)}"
    )

    resp_relevance = llm(relevance_prompt, max_tokens=4000)
    relevance_text = resp_relevance["choices"][0]["text"]

    logging.info("Relevance selection completed. Parsing JSON...")

    m_rel = re.search(r"\{[\s\S]*\}", relevance_text)
    if not m_rel:
        logging.error("Failed to extract JSON for relevance selection.")
        raise ValueError("Model did not return JSON for relevance selection.")

    relevance_json = json.loads(m_rel.group())
    relevant_vars = relevance_json.get("relevant", [])

    logging.info(f"Relevant variables identified: {relevant_vars}")

    return relevant_vars, relevance_text


# def extract_json(text):
#     """
#     Robust JSON extraction:
#     - Finds the first '{'
#     - Finds the last '}'
#     - Returns only the substring between them
#     - Validates JSON structure
#     """
#     start = text.find("{")
#     end = text.rfind("}")
# 
#     if start == -1 or end == -1 or end < start:
#         raise ValueError("No JSON object found in model output.")
# 
#     candidate = text[start:end + 1]
# 
#     # Try to parse; if it fails, raise
#     return json.loads(candidate)
# 
# 
# def get_relevant_variables(df, llm, user_objective):
#     logging.info("Preparing column preview for relevance filtering...")
# 
#     col_preview = {
#         col: {
#             "dtype": str(df[col].dtype),
#             "sample_values": df[col].dropna().unique()[:5].tolist()
#         }
#         for col in df.columns
#     }
# 
#     logging.info("Running relevance selection prompt...")
# 
#     relevance_prompt = (
#         "SYSTEM:\n"
#         "You output ONLY valid JSON. No explanation. No commentary. "
#         "The response MUST start with '{' and end with '}'.\n\n"
# 
#         "TASK:\n"
#         "Given the analysis objective and the list of variables, "
#         "identify which variables are relevant.\n\n"
# 
#         "Return JSON with this exact schema:\n"
#         "{\n"
#         '  "relevant": ["col1", "col2"],\n'
#         '  "irrelevant": ["col3", "col4"],\n'
#         '  "rationale": "Short explanation based only on values/dtypes."\n'
#         "}\n\n"
# 
#         f"OBJECTIVE:\n{user_objective}\n\n"
#         f"VARIABLES:\n{json.dumps(col_preview, indent=2)}\n"
#     )
# 
#     resp = llm(relevance_prompt, max_tokens=4000)
#     relevance_text = resp["choices"][0]["text"]
# 
#     logging.info("Relevance selection completed. Parsing JSON...")
# 
#     try:
#         relevance_json = extract_json(relevance_text)
#     except Exception as e:
#         logging.error("Failed to parse JSON from model output.")
#         logging.error(relevance_text)
#         raise e
# 
#     relevant_vars = relevance_json.get("relevant", [])
# 
#     logging.info(f"Relevant variables identified: {relevant_vars}")
# 
#     return relevant_vars, relevance_text




# ====================================================
# 3B. HANDLE MULTIPLE TIME/SPACE CANDIDATES
# ====================================================

def get_unique_spacetime(schema, df, llm):

    logging.info("Evaluating multiple candidate time and space variables...")

    # Convert singletons to lists if needed
    if isinstance(schema.get("time"), list):
        time_candidates = schema["time"]
    else:
        time_candidates = [schema["time"]] if schema["time"] else []

    if isinstance(schema.get("space"), list):
        space_candidates = schema["space"]
    else:
        space_candidates = [schema["space"]] if schema["space"] else []

    # Count unique values for each candidate
    time_levels = {
        col: df[col].nunique() for col in time_candidates if col in df.columns
    }
    space_levels = {
        col: df[col].nunique() for col in space_candidates if col in df.columns
    }

    logging.info(f"Time candidate levels: {time_levels}")
    logging.info(f"Space candidate levels: {space_levels}")

    # Build selection prompt for LLaMA
    selection_prompt = (
        "You are given possible time variables and space variables, "
        "along with the count of unique values in each. "
        "Your job is to select ONE time variable and ONE space variable "
        "that will produce a human-interpretable, surface-level analysis. "
        "Avoid variables with extremely high cardinality unless no alternative exists. "
        "Return JSON with keys: chosen_time, chosen_space, rationale.\n\n"
        f"TIME CANDIDATES:\n{json.dumps(time_levels)}\n\n"
        f"SPACE CANDIDATES:\n{json.dumps(space_levels)}\n"
    )

    logging.info("Selecting appropriate time and space variables using LLaMA...")

    resp_select = llm(selection_prompt, max_tokens=256)
    select_text = resp_select["choices"][0]["text"]

    m_select = re.search(r"\{[\s\S]*\}", select_text)
    if not m_select:
        logging.error("Failed to extract JSON for time/space selection.")
        raise ValueError("Model did not return JSON for variable selection.")

    selection_json = json.loads(m_select.group())

    chosen_time = selection_json.get("chosen_time")
    chosen_space = selection_json.get("chosen_space")

    logging.info(
        f"Selected time variable: {chosen_time}, space variable: {chosen_space}"
    )

    return chosen_time, chosen_space, select_text