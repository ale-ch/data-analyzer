def corr_one_year(df, time_var, num_vars):
    year = df[time_var].dropna().max()
    corr = df[df[time_var] == year][num_vars].corr()
    return f"Interpret correlations for year {year}.\n\n{corr.to_string()}"
