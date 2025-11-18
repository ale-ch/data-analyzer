def corr_one_year(df, time_var, num_vars):
    # no numeric vars
    if not num_vars:
        txt = "No numeric variables available for correlation analysis."
        return txt, None

    # determine most recent year
    series = df[time_var].dropna()
    if series.empty:
        txt = "Time variable contains no valid entries for correlation analysis."
        return txt, None

    year = series.max()

    # restrict to that year
    df_year = df[df[time_var] == year]

    if df_year.empty:
        txt = f"No data available for year {year}."
        return txt, None

    # numeric subset
    df_sub = df_year[num_vars].dropna(how="all")
    if df_sub.empty:
        txt = f"No usable numeric data for correlations in year {year}."
        return txt, None

    corr = df_sub.corr()

    txt = (
        f"Cross-sectional correlations for year {year}.\n\n"
        f"{corr.to_string()}"
    )

    raw = corr

    return txt, raw

