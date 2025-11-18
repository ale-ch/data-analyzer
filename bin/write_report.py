import logging

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ====================================================
# WRITE MARKDOWN REPORT
# ====================================================

#def write_report(output_file, user_objective, relevance_text, schema_text, select_text, prompts, results):
#    with open(output_file, "w") as f:
#        f.write("# Automated Analysis Report\n\n")
#
#        f.write("## Objective\n")
#        f.write("```\n" + user_objective + "\n```\n\n")
#
#        f.write("## Variable Relevance\n")
#        f.write("```\n" + relevance_text + "\n```\n\n")
#
#        f.write("## Schema Classification\n")
#        f.write("```\n" + schema_text + "\n```\n\n")
#
#        f.write("## Time/Space Variable Selection\n")
#        f.write("```\n" + select_text + "\n```\n\n")
#
#        for key in prompts:
#            f.write(f"## {key}\n\n")
#            # f.write("### Prompt\n```\n" + prompts[key] + "\n```\n\n")
#            f.write("### LLaMA Interpretation\n```\n" + results[key] + "\n```\n\n")
#
#


# ====================================================
# WRITE MARKDOWN REPORT
# ====================================================

def write_report(output_file, user_objective, relevance_text, schema_text, select_text, prompts, results, raw_results):
    with open(output_file, "w") as f:
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

            # Actual computed table / numeric output
            if key in raw_results:
                f.write("### Computed Data\n")
                f.write("```\n" + raw_results[key].to_string() + "\n```\n\n")

            # LLM interpretation
            f.write("### LLaMA Interpretation\n")
            f.write("```\n" + results[key] + "\n```\n\n")
