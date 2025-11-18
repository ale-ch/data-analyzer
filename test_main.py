import logging

from bin.write_report import write_report
from bin.build_schema import build_schema
from bin.select_variables import get_relevant_variables, get_unique_spacetime
from bin.load import load_data, load_llm_model, load_user_objective
from bin.run_prompts import run_prompts

from bin.analysis.summaries import (
    group_by_space,
    group_by_time,
    group_by_space_time,
)

from bin.analysis.correlations import corr_one_year

# regressions imported but unused
from bin.analysis.regressions import (
    regress_whole,
    regress_region,
    prepare_panel,
    pooled_regression,
    fixed_effects_regression,
    random_effects_regression,
    hausman_test,
)

from bin.analysis.data_quality import (
    qc_structure,
    qc_missing,
    qc_duplicates,
    qc_outliers,
    qc_ranges,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("Loading data...")

data_path = "/workspace/myfile.csv"
df = load_data(data_path)

model_path = "/workspace/tests/qwen2.5-14b-instruct-q5_k_m.gguf"
llm = load_llm_model(model_path)

logging.info("Reading analysis objective...")

objective_path = "/workspace/repos/data-analyzer/modules/analyzer/objective.txt"
user_objective = load_user_objective(objective_path)

logging.info("Selecting relevant variables...")

relevant_vars, relevance_text = get_relevant_variables(df, llm, user_objective)
df = df[relevant_vars]

logging.info("Running data quality checks...")

prompts = {}
results_raw = {}

txt_struct, raw_struct = qc_structure(df)
prompts["qc_structure"] = txt_struct
results_raw["qc_structure"] = raw_struct

txt_missing, raw_missing = qc_missing(df)
prompts["qc_missing"] = txt_missing
results_raw["qc_missing"] = raw_missing

txt_dups, raw_dups = qc_duplicates(df)
prompts["qc_duplicates"] = txt_dups
results_raw["qc_duplicates"] = raw_dups

numeric_guess = df.select_dtypes(include=["int", "float"]).columns.tolist()

txt_out, raw_out = qc_outliers(df, numeric_guess)
prompts["qc_outliers"] = txt_out
results_raw["qc_outliers"] = raw_out

txt_ranges, raw_ranges = qc_ranges(df, numeric_guess)
prompts["qc_ranges"] = txt_ranges
results_raw["qc_ranges"] = raw_ranges

logging.info("Building schema...")

schema, schema_text = build_schema(df, llm)

time_var = schema.get("time")
space_var = schema.get("space")
num_vars = schema.get("numeric", [])
cat_vars = schema.get("categorical", [])

logging.info("Selecting unique time/space variables...")

chosen_time, chosen_space, select_text = get_unique_spacetime(schema, df, llm)
time_var = chosen_time
space_var = chosen_space

logging.info("Computing group-by-space summary...")

prompt_gbs, table_gbs = group_by_space(df, space_var, cat_vars)
prompts["group_by_space_top10"] = prompt_gbs
results_raw["group_by_space_top10"] = table_gbs

logging.info("Computing group-by-time summary...")

p_time = group_by_time(df, time_var, num_vars)
prompts["group_by_time_summary"] = p_time["summary"]
prompts["group_by_time_trend"] = p_time["trend"]

logging.info("Computing space-time summary...")

p_st = group_by_space_time(df, space_var, time_var, num_vars)
prompts["group_by_space_time_summary"] = p_st["summary"]
prompts["group_by_space_time_trend"] = p_st["trend"]

# ----------------------------------------------------
# REGRESSIONS DISABLED
# ----------------------------------------------------

# logging.info("Running whole-data regressions...")
# txt_whole, raw_whole = regress_whole(df, time_var, num_vars)
# prompts["lm_whole"] = txt_whole
# results_raw["lm_whole"] = raw_whole

# logging.info("Running region-level regressions...")
# txt_reg, raw_reg = regress_region(df, space_var, time_var, num_vars)
# prompts["lm_region"] = txt_reg
# results_raw["lm_region"] = raw_reg

# logging.info("Running panel regressions...")
# if len(num_vars) >= 2:
#     y = num_vars[0]
#     xvars = num_vars[1:]
#
#     txt_panel, df_panel = prepare_panel(df, space_var, time_var)
#     prompts["panel_prepare"] = txt_panel
#     results_raw["panel_prepare"] = "panel_prepared"
#
#     txt_pooled, raw_pooled = pooled_regression(df_panel, y, xvars)
#     prompts["panel_pooled"] = txt_pooled
#     results_raw["panel_pooled"] = raw_pooled
#
#     txt_fe, raw_fe = fixed_effects_regression(df_panel, y, xvars)
#     prompts["panel_fe"] = txt_fe
#     results_raw["panel_fe"] = raw_fe
#
#     txt_re, raw_re = random_effects_regression(df_panel, y, xvars)
#     prompts["panel_re"] = txt_re
#     results_raw["panel_re"] = raw_re
#
#     txt_haus, raw_haus = hausman_test(raw_fe, raw_re)
#     prompts["panel_hausman"] = txt_haus
#     results_raw["panel_hausman"] = raw_haus
# else:
#     prompts["panel_warning"] = "Panel regressions require at least two numeric variables."
#     results_raw["panel_warning"] = None

logging.info("Computing cross-sectional correlations...")

txt_corr, raw_corr = corr_one_year(df, time_var, num_vars)
prompts["corr_one_year"] = txt_corr
results_raw["corr_one_year"] = raw_corr

logging.info("Running LLM analysis...")

results = run_prompts(prompts, llm)

logging.info("Writing report...")

output_file = "analysis_report.md"

write_report(
    output_file,
    user_objective,
    relevance_text,
    schema_text,
    select_text,
    prompts,
    results,
    results_raw
)

logging.info("Report complete.")

