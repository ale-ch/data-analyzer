import logging
from bin.write_report import write_report
from bin.build_schema import build_schema
from bin.select_variables import get_relevant_variables, get_unique_spacetime
from bin.load import load_data, load_llm_model, load_user_objective
from bin.run_prompts import run_prompts
from bin.analysis.correlations import corr_one_year
from bin.analysis.regressions import regress_whole, regress_region
from bin.analysis.summaries import group_by_time, group_by_space, group_by_space_time

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
data_path = "/workspace/myfile.csv"
df = load_data(data_path)

model_path = "/Users/work/Documents/Programming/test/analyzer_test/qwen2.5-7b-instruct-q5_k_m.gguf"
# model_path = "/Users/work/Documents/Programming/test/llama_download/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
# model_path = "/Users/work/Documents/Programming/test/llama_download/qwen2.5-14b-instruct-q5_k_m.gguf"
model_path = "/workspace/tests/qwen2.5-14b-instruct-q5_k_m.gguf"
llm = load_llm_model(model_path)


# ====================================================
# 1. USER OBJECTIVE
# ====================================================
logging.info("Reading analysis objective...")

# objective_path = "objective.txt"
objective_path = "/Users/work/Documents/Programming/repos/data-analyzer/modules/analyzer/objective.txt"
objective_path = "/workspace/repos/data-analyzer/modules/analyzer/objective.txt"
user_objective = load_user_objective(objective_path)

# ====================================================
# 2. VARIABLE SKIM + RELEVANCE SELECTION
# ====================================================
relevant_vars, relevance_text = get_relevant_variables(df, llm, user_objective)

df = df[relevant_vars]
logging.info("Data filtered to relevant variables.")


# ====================================================
# 3. SCHEMA CLASSIFICATION
# ====================================================
schema, schema_text = build_schema(df, llm)

time_var = schema.get("time")
space_var = schema.get("space")
num_vars = schema.get("numeric", [])
cat_vars = schema.get("categorical", [])

logging.info("BEFORE TIMESPACE CANDIDATES")
logging.info(f"time_var={time_var}, space_var={space_var}, num_vars={num_vars}, cat_vars={cat_vars}")

# ====================================================
# 3B. HANDLE MULTIPLE TIME/SPACE CANDIDATES
# ====================================================
chosen_time, chosen_space, select_text = get_unique_spacetime(schema, df, llm)

time_var = chosen_time
space_var = chosen_space

logging.info("AFTER TIMESPACE CANDIDATES")
logging.info(f"time_var={time_var}, space_var={space_var}, num_vars={num_vars}, cat_vars={cat_vars}")


# ====================================================
# BUILD PROMPTS OBJECT
# ====================================================
prompts = {}
results = {}

# ------------------------------
# GROUP BY SPACE
# ------------------------------
prompts = {}
results_raw = {}

logging.info("Computing top categories by space...")
prompts["group_by_space_top10"] = group_by_space(df, space_var, cat_vars)

prompt_gbs, table_gbs = group_by_space(df, space_var, cat_vars)
prompts["group_by_space_top10"] = prompt_gbs
results_raw["group_by_space_top10"] = table_gbs


# logging.info("Computing time summaries and trends...")
# p_time = group_by_time(df, time_var, num_vars)
# prompts["group_by_time_summary"] = p_time["summary"]
# prompts["group_by_time_trend"] = p_time["trend"]
# 
# logging.info("Computing space–time summaries...")
# p_st = group_by_space_time(df, space_var, time_var, num_vars)
# prompts["group_by_space_time_summary"] = p_st["summary"]
# prompts["group_by_space_time_trend"] = p_st["trend"]
# 
# logging.info("Running summed-time regressions (whole dataset)...")
# prompts["lm_whole"] = regress_whole(df, time_var, num_vars)
# 
# logging.info("Running summed-time regressions per region...")
# prompts["lm_region"] = regress_region(df, space_var, time_var, num_vars)
# 
# logging.info("Computing cross-sectional correlations...")
# prompts["corr_one_year"] = corr_one_year(df, time_var, num_vars)


# ====================================================
# RUN PROMPTS THROUGH LLAMA with fail-safe
# ====================================================
logging.info("Sending analysis prompts to LLaMA (with context-window protection)...")

results = run_prompts(prompts, llm)


# ====================================================
# WRITE MARKDOWN REPORT
# ====================================================
logging.info("Writing final Markdown report...")

output_file = "analysis_report.md"

# write_report(output_file, user_objective, relevance_text, schema_text, select_text, prompts, results)
write_report(output_file, user_objective, relevance_text, schema_text, select_text, prompts, results, results_raw)

logging.info("Report written: analysis_report.md")

