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
