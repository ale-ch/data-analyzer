def write_report(output_file, user_objective, relevance_text, schema_text, select_text, prompts, results, raw_results):
    def format_raw(value):
        if value is None:
            return "None"

        # pandas objects
        if hasattr(value, "to_string"):
            return value.to_string()

        # dict
        if isinstance(value, dict):
            import json
            return json.dumps(value, indent=2)

        # list/tuple
        if isinstance(value, (list, tuple)):
            return "\n".join([str(x) for x in value])

        # fallback
        return str(value)

    with open(output_file, "w") as f:
        f.write("# Automated Analysis Report\n\n")

        f.write("## Objective\n")
        f.write("```\n" + str(user_objective) + "\n```\n\n")

        f.write("## Variable Relevance\n")
        f.write("```\n" + str(relevance_text) + "\n```\n\n")

        f.write("## Schema Classification\n")
        f.write("```\n" + str(schema_text) + "\n```\n\n")

        f.write("## Time/Space Variable Selection\n")
        f.write("```\n" + str(select_text) + "\n```\n\n")

        for key in prompts:
            f.write(f"## {key}\n\n")

            # Computed raw data
            if key in raw_results:
                f.write("### Computed Data\n")
                f.write("```\n" + format_raw(raw_results[key]) + "\n```\n\n")

            # LLM interpretation
            f.write("### LLM Interpretation\n")
            f.write("```\n" + str(results.get(key, "")) + "\n```\n\n")

