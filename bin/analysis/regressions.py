# regressions.py
import statsmodels.formula.api as smf

def regress_whole(df, time_var, num_vars):
    lm_whole = {}
    txt = "Interpret linear trends using summed values by time.\n\n"

    for var in num_vars:
        d = df[[time_var, var]].dropna()
        if d.empty:
            continue

        summed = d.groupby(time_var)[var].sum().reset_index()
        model = smf.ols(f"{var} ~ {time_var}", data=summed).fit()

        lm_whole[var] = {"model": model, "summed": summed}
        txt += (
            f"VARIABLE: {var}\n"
            f"SUMS:\n{summed.to_string(index=False)}\n\n"
            f"COEFFICIENTS:\n{model.params.to_string()}\n"
            f"R2: {model.rsquared}\n\n"
        )

    return lm_whole, txt


def regress_region(df, space_var, time_var, num_vars):
    lm_region = {}
    txt = "Interpret summed-time regressions per region.\n\n"

    for region in df[space_var].dropna().unique():
        d_region = df[df[space_var] == region]

        for var in num_vars:
            d = d_region[[time_var, var]].dropna()
            if d.empty:
                continue

            summed = d.groupby(time_var)[var].sum().reset_index()
            model = smf.ols(f"{var} ~ {time_var}", data=summed).fit()

            lm_region[(region, var)] = {"model": model, "summed": summed}
            txt += (
                f"REGION: {region}, VARIABLE: {var}\n"
                f"SUMS:\n{summed.to_string(index=False)}\n\n"
                f"COEFFICIENTS:\n{model.params.to_string()}\n"
                f"R2: {model.rsquared}\n\n"
            )

    return lm_region, txt

# ============================================
# PANEL-DATA FUNCTIONS (MAIN-LOGIC COMPLIANT)
# ============================================
import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS, RandomEffects, PooledOLS


def _add_const(df, cols):
    X = df[cols].copy()
    if "const" not in X.columns:
        X["const"] = 1.0
    return X


# ----------------------------------------------------
# PANEL PREP
# ----------------------------------------------------
def prepare_panel(df, entity_var, time_var):
    df_panel = df.set_index([entity_var, time_var]).sort_index()
    prompt = (
        "Panel structure prepared using entity and time identifiers.\n"
        f"ENTITY={entity_var}, TIME={time_var}\n"
        "Data indexed and sorted.\n"
    )
    return prompt, df_panel


# ----------------------------------------------------
# POOLED OLS
# ----------------------------------------------------
def pooled_regression(df_panel, y, xvars):
    X = _add_const(df_panel, xvars)

    model = PooledOLS(df_panel[y], X).fit(
        cov_type="clustered",
        cluster_entity=True
    )

    txt = (
        "Pooled OLS regression.\n\n"
        f"Model: {y} ~ {', '.join(xvars)}\n\n"
        f"Coefficients:\n{model.params.to_string()}\n\n"
        f"R2: {model.rsquared}\n"
    )

    raw = {
        "coefficients": model.params,
        "cov": model.cov,
        "r2": model.rsquared,
        "nobs": model.nobs,
    }

    return txt, raw


# ----------------------------------------------------
# FIXED EFFECTS (WITHIN)
# ----------------------------------------------------
def fixed_effects_regression(df_panel, y, xvars):
    X = _add_const(df_panel, xvars)

    model = PanelOLS(
        df_panel[y],
        X,
        entity_effects=True
    ).fit(
        cov_type="clustered",
        cluster_entity=True
    )

    txt = (
        "Fixed Effects regression (entity FE).\n\n"
        f"Model: {y} ~ {', '.join(xvars)} + entity FE\n\n"
        f"Coefficients:\n{model.params.to_string()}\n\n"
        f"Within-R2: {model.rsquared_within}\n"
    )

    raw = {
        "coefficients": model.params,
        "cov": model.cov,
        "r2_within": model.rsquared_within,
        "nobs": model.nobs,
    }

    return txt, raw


# ----------------------------------------------------
# RANDOM EFFECTS
# ----------------------------------------------------
def random_effects_regression(df_panel, y, xvars):
    X = _add_const(df_panel, xvars)

    model = RandomEffects(df_panel[y], X).fit()

    txt = (
        "Random Effects regression.\n\n"
        f"Model: {y} ~ {', '.join(xvars)}\n\n"
        f"Coefficients:\n{model.params.to_string()}\n\n"
        f"R2: {model.rsquared}\n"
    )

    raw = {
        "coefficients": model.params,
        "cov": model.cov,
        "r2": model.rsquared,
        "nobs": model.nobs,
    }

    return txt, raw


# ----------------------------------------------------
# HAUSMAN TEST (FE vs RE)
# ----------------------------------------------------
def hausman_test(fe_raw, re_raw):
    import numpy.linalg as la
    from scipy.stats import chi2

    b_fe = fe_raw["coefficients"]
    b_re = re_raw["coefficients"]

    common = list(set(b_fe.index).intersection(b_re.index))
    b_fe = b_fe[common]
    b_re = b_re[common]

    V_fe = fe_raw["cov"].loc[common, common]
    V_re = re_raw["cov"].loc[common, common]

    diff = b_fe - b_re
    V_diff = V_fe - V_re

    try:
        stat = float(diff.T @ la.inv(V_diff) @ diff)
        df = len(diff)
        p = 1 - chi2.cdf(stat, df)

        txt = (
            "Hausman test comparing FE and RE.\n\n"
            f"Chi2({df}) = {stat:.4f}\n"
            f"p-value = {p:.4f}\n"
        )

        raw = {"stat": stat, "df": df, "p": p}
        return txt, raw

    except la.LinAlgError:
        txt = "Hausman test failed due to singular covariance matrix."
        raw = None
        return txt, raw

