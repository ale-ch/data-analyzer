# def group_by_space(df, space_var, cat_vars):
#     top10 = df.groupby(space_var).apply(
#         lambda g: g[cat_vars].value_counts().head(10)
#     )
# 
#     prompt = (
#         "Interpret the top categories for each spatial unit.\n\n"
#         "Use only the information provided in the table. Do not assume or invent external facts.\n\n"
#         "Return the output in the following standardized structure:\n\n"
#         "1. Variables Explanation\n"
#         "   - Briefly explain each categorical variable based solely on the table values.\n\n"
#         "2. Key Insights\n"
#         "   - Summarize the essential patterns observed across spatial units.\n\n"
#         "3. Further Analysis\n"
#         "   - Suggest follow-up analyses that remain grounded strictly in the provided data.\n\n"
#         f"{top10.to_string()}"
#     )
# 
#     return prompt, top10

def group_by_space(df, space_var, cat_vars):
    # Compute top 10 counts per group with column named "count"
    top10 = (
        df.groupby(space_var)
          .apply(lambda g: g[cat_vars].value_counts()
                            .head(10)
                            .rename("count")
                            .to_frame())
    )

    # Extract column names dynamically
    colnames = list(top10.reset_index().columns)
    colname_string = ", ".join(str(c) for c in colnames)

    # Final structured prompt for Llama 3.1
    prompt = (
        "You will output ONLY valid JSON using the structure below. "
        "All reasoning must be grounded entirely in the visible table values. "
        "Do not introduce values, rows, labels, or meaning not present in the table. "
        "Patterns must be strictly verifiable from the numbers and labels shown.\n\n"

        "JSON OUTPUT TEMPLATE:\n"
        "{\n"
        '  "variables_explanation": [\n'
        '    {"column": "COLUMN_NAME", "type": "VALUE_TYPE"}\n'
        '  ],\n'
        '  "visible_patterns": [\n'
        '    "A grounded comparison or ordering based ONLY on visible values."\n'
        '  ],\n'
        '  "next_checks": [\n'
        '    "Simple operations that can be applied to this table."\n'
        '  ]\n'
        "}\n\n"

        "INSTRUCTIONS:\n"
        "1. variables_explanation:\n"
        "   - Use each column name exactly as printed.\n"
        "   - VALUE_TYPE must be one of: \"text\", \"number\".\n"
        "   - Decide type by looking at the values in that column.\n\n"

        "2. visible_patterns:\n"
        "   - Describe ONLY patterns directly visible in the table.\n"
        "   - Use explicit numeric comparisons (e.g., \"6240 > 5460\").\n"
        "   - Allowed patterns:\n"
        "       • highest/lowest values inside a group\n"
        "       • ascending/descending ordering\n"
        "       • repeated values\n"
        "       • shared values across groups\n"
        "   - Must cite the exact values from the table.\n\n"

        "3. next_checks:\n"
        "   - Suggest simple table operations the user could perform.\n"
        "   - Examples: \"sort by count\", \"compare two values\", \"count rows per group\".\n\n"

        "GROUNDING RULE:\n"
        "Everything in your answer must come directly from the table values. "
        "No invented categories. No external meaning. No new labels.\n\n"

        f"TABLE COLUMNS: {colname_string}\n\n"
        "TABLE:\n"
        f"{top10.reset_index().to_string(index=False)}"
    )

    return prompt, top10













def group_by_time(df, time_var, num_vars):
    summary = df.groupby(time_var)[num_vars].describe()
    trend = df.groupby(time_var)[num_vars].mean()
    return {
        "summary": "Interpret summary statistics over time.\n\n" + summary.to_string(),
        "trend": "Interpret temporal trends.\n\n" + trend.to_string(),
    }

def group_by_space_time(df, space_var, time_var, num_vars):
    summary = df.groupby([space_var, time_var])[num_vars].describe()
    trend = df.groupby([space_var, time_var])[num_vars].mean().unstack(space_var)
    return {
        "summary": "Interpret space-time summary statistics.\n\n" + summary.to_string(),
        "trend": "Interpret space-time trends.\n\n" + trend.to_string(),
    }
