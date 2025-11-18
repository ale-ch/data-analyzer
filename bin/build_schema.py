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

# ====================================================
# 3. SCHEMA CLASSIFICATION
# ====================================================

# def build_schema(df, llm):
#     logging.info("Preparing schema classification prompt...")
# 
#     col_info = {
#         col: str(df[col].dtype)
#         for col in df.columns
#     }
# 
#     schema_prompt = (
#         "You are given column names and pandas dtypes. "
#         "Identify time, space, numeric, and categorical variables. "
#         "Return JSON with keys: time, space, numeric, categorical.\n\n"
#         f"COLUMNS:\n{json.dumps(col_info, indent=2)}"
#     )
# 
#     logging.info("Running schema classification prompt...")
# 
#     resp_schema = llm(schema_prompt, max_tokens=2000)
#     schema_text = resp_schema["choices"][0]["text"]
# 
#     m_schema = re.search(r"\{[\s\S]*\}", schema_text)
#     if not m_schema:
#         logging.error("Failed to extract JSON for schema classification.")
#         raise ValueError("Model did not return JSON in schema identification.")
# 
#     schema = json.loads(m_schema.group())
# 
#     time_var = schema.get("time")
#     space_var = schema.get("space")
#     num_vars = schema.get("numeric", [])
#     cat_vars = schema.get("categorical", [])
# 
#     logging.info(f"Schema classification: time={time_var}, space={space_var}, numeric={num_vars}, categorical={cat_vars}")
# 
#     return schema, schema_text



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def clean_schema(schema):
    time_var = schema.get("time") or []
    space_var = schema.get("space") or []
    num_vars = schema.get("numeric", [])
    cat_vars = schema.get("categorical", [])

    if isinstance(time_var, str):
        time_var = [time_var]
    if isinstance(space_var, str):
        space_var = [space_var]

    for v in time_var:
        if v in num_vars:
            num_vars.remove(v)
        if v in cat_vars:
            cat_vars.remove(v)

    for v in space_var:
        if v in num_vars:
            num_vars.remove(v)
        if v in cat_vars:
            cat_vars.remove(v)

    return {
        "time": time_var if len(time_var) > 1 else (time_var[0] if time_var else None),
        "space": space_var if len(space_var) > 1 else (space_var[0] if space_var else None),
        "numeric": num_vars,
        "categorical": cat_vars,
    }

def build_schema(df, llm):
    logging.info("Preparing schema classification prompt...")

    col_info = {col: str(df[col].dtype) for col in df.columns}

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

    schema = clean_schema(schema)

    logging.info(
        f"Cleaned schema: time={schema['time']}, space={schema['space']}, "
        f"numeric={schema['numeric']}, categorical={schema['categorical']}"
    )

    return schema, schema_text
