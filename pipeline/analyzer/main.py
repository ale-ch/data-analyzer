import pandas as pd
import statsmodels.formula.api as smf
from llama_cpp import Llama
import json
import re
import logging

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
logging.info("Loading data...")

data_path = "/Users/work/Documents/Programming/test/ITA_TEST/output/firms_data.csv"
model_path = "/Users/work/Documents/Programming/test/analyzer_test/qwen2.5-7b-instruct-q5_k_m.gguf"

df = pd.read_csv(data_path)

logging.info(f"Data loaded with {df.shape[0]} rows and {df.shape[1]} columns.")

llm = Llama(
    model_path=model_path,
    n_ctx=4096,
    verbose=False
)

# llm = Llama(model_path=model_path, verbose=False)

logging.info("LLaMA model loaded.")


# ====================================================
# 1. USER OBJECTIVE
# ====================================================
logging.info("Reading analysis objective...")

with open("objective.txt") as f:
    user_objective = f.read().strip()

logging.info("Objective loaded.")


# ====================================================
# 2. VARIABLE SKIM + RELEVANCE SELECTION
# ====================================================
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

df = df[relevant_vars]
logging.info("Data filtered to relevant variables.")


# ====================================================
# 3. SCHEMA CLASSIFICATION
# ====================================================
logging.info("Preparing schema classification prompt...")

col_info = {
    col: str(df[col].dtype)
    for col in df.columns
}

schema_prompt = (
    "You are given column names and pandas dtypes. "
    "Identify time, space, numeric, and categorical variables. "
    "Return JSON with keys: time, space, numeric, categorical.\n\n"
    f"COLUMNS:\n{json.dumps(col_info, indent=2)}"
)

logging.info("Running schema classification prompt...")

resp_schema = llm(schema_prompt, max_tokens=2000)
schema_text = resp_schema["choices"][0]["text"]

m_schema = re.search(r"\{[\s\S]*\}", schema_text)
if not m_schema:
    logging.error("Failed to extract JSON for schema classification.")
    raise ValueError("Model did not return JSON in schema identification.")

schema = json.loads(m_schema.group())

time_var = schema.get("time")
space_var = schema.get("space")
num_vars = schema.get("numeric", [])
cat_vars = schema.get("categorical", [])

logging.info(f"Schema classification: time={time_var}, space={space_var}, numeric={num_vars}, categorical={cat_vars}")

# ====================================================
# 3B. HANDLE MULTIPLE TIME/SPACE CANDIDATES
# ====================================================
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

# Replace the original variables with chosen ones
time_var = chosen_time
space_var = chosen_space

# ====================================================
# BUILD PROMPTS OBJECT
# ====================================================
prompts = {}
results = {}

# ------------------------------
# GROUP BY SPACE
# ------------------------------
logging.info("Computing top categories by space...")
top10_space = (
    df.groupby(space_var)
      .apply(lambda g: g[cat_vars].value_counts().head(10))
)

prompts["group_by_space_top10"] = (
    "Interpret top categories per spatial unit.\n\n"
    f"{top10_space.to_string()}"
)

# ------------------------------
# GROUP BY TIME — summary + trends
# ------------------------------
logging.info("Computing time summaries and trends...")
summary_time = df.groupby(time_var)[num_vars].describe()
trend_time = df.groupby(time_var)[num_vars].mean()

prompts["group_by_time_summary"] = (
    "Interpret summary statistics over time.\n\n"
    f"{summary_time.to_string()}"
)

prompts["group_by_time_trend"] = (
    "Interpret temporal trends.\n\n"
    f"{trend_time.to_string()}"
)

# ------------------------------
# GROUP BY SPACE & TIME
# ------------------------------
logging.info("Computing space–time summaries...")
summary_space_time = df.groupby([space_var, time_var])[num_vars].describe()
trend_space_time = (
    df.groupby([space_var, time_var])[num_vars]
      .mean()
      .unstack(space_var)
)

prompts["group_by_space_time_summary"] = (
    "Interpret space-time summary statistics.\n\n"
    f"{summary_space_time.to_string()}"
)

prompts["group_by_space_time_trend"] = (
    "Interpret space-time trends.\n\n"
    f"{trend_space_time.to_string()}"
)

# ====================================================
# LINEAR MODELS USING SUMS BY TIME (WHOLE DATASET)
# ====================================================
logging.info("Running summed-time regressions (whole dataset)...")

lm_whole = {}
txt_whole = "Interpret linear trends using summed values by time.\n\n"

for var in num_vars:
    d = df[[time_var, var]].dropna()
    summed = d.groupby(time_var)[var].sum().reset_index()

    model = smf.ols(f"{var} ~ {time_var}", data=summed).fit()

    lm_whole[var] = {"model": model, "summed": summed}

    txt_whole += (
        f"VARIABLE: {var}\n"
        f"SUMS:\n{summed.to_string(index=False)}\n\n"
        f"COEFFICIENTS:\n{model.params.to_string()}\n"
        f"R2: {model.rsquared}\n\n"
    )

prompts["lm_whole"] = txt_whole

# ====================================================
# REGIONAL SUMMED-TIME REGRESSIONS
# ====================================================
logging.info("Running summed-time regressions per region...")

lm_region = {}
txt_region = "Interpret summed-time regressions per region.\n\n"

for region in df[space_var].dropna().unique():
    d_region = df[df[space_var] == region]

    for var in num_vars:
        d = d_region[[time_var, var]].dropna()
        if d.empty:
            continue

        summed = d.groupby(time_var)[var].sum().reset_index()
        model = smf.ols(f"{var} ~ {time_var}", data=summed).fit()

        lm_region[(region, var)] = {"model": model, "summed": summed}

        txt_region += (
            f"REGION: {region}, VARIABLE: {var}\n"
            f"SUMS:\n{summed.to_string(index=False)}\n\n"
            f"COEFFICIENTS:\n{model.params.to_string()}\n"
            f"R2: {model.rsquared}\n\n"
        )

prompts["lm_region"] = txt_region

# ====================================================
# CROSS-SECTION CORRELATIONS
# ====================================================
logging.info("Computing cross-sectional correlations...")

one_year = df[time_var].dropna().max()
corr = df[df[time_var] == one_year][num_vars].corr()

prompts["corr_one_year"] = (
    f"Interpret correlations for year {one_year}.\n\n"
    f"{corr.to_string()}"
)

# ====================================================
# RUN PROMPTS THROUGH LLAMA with fail-safe
# ====================================================
logging.info("Sending analysis prompts to LLaMA (with context-window protection)...")

results = {}

def safe_llm_call(prompt, label):
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


# Run all prompts safely
for key, prompt in prompts.items():
    logging.info(f"Processing: {key}")
    results[key] = safe_llm_call(prompt, key)

logging.info("All prompts processed with safety wrapper.")


# ====================================================
# WRITE MARKDOWN REPORT
# ====================================================
logging.info("Writing final Markdown report...")

with open("analysis_report.md", "w") as f:
    f.write("# Automated Analysis Report\n\n")

    f.write("## Objective\n")
    f.write("```\n" + user_objective + "\n```\n\n")

    f.write("## Variable Relevance\n")
    f.write("```\n" + relevance_text + "\n```\n\n")

    f.write("## Schema Classification\n")
    f.write("```\n" + schema_text + "\n```\n\n")

    f.write("## Time/Space Variable Selection\n")
    f.write("```\n" + select_text + "\n```\n\n")

    for key in prompts:
        f.write(f"## {key}\n\n")
        f.write("### Prompt\n```\n" + prompts[key] + "\n```\n\n")
        f.write("### LLaMA Interpretation\n```\n" + results[key] + "\n```\n\n")

logging.info("Report written: analysis_report.md")

