import pandas as pd
import numpy as np


pairs = {
    "1": ["1-2", "1-3"],
    "2": ["1-2", "2-3"],
    "3": ["1-3", "2-3"],
    "all": ["1-2", "1-3", "2-3"],
}

gauge_ids = ["1", "2", "3"]


def wmo_correction(R_raw):
    """Apply WMO calibration factor to raw rain rate

    parameters
    ----------

    R_raw : array like
        Rain rate in mm/h

    return
    ------

    R_calib : pandas.DataFrame
        Corrected rain rate in mm/h

    """

    R_calib = (R_raw / 1.16) ** (1 / 0.92)
    return R_calib


def combine_gauges(
    df_three_gauges_R_1_min,
    hours_to_average_for_diff=24,
    max_allowed_relative_diff=0.3,
    min_R=0.5,
    hours_to_average_for_zeros=1,
):
    """Combine three gauges from one location into one 'best' rainfall time series

    parameters
    ----------

    df_three_gauges_R_1min : pandas.DataFrame
        Minutely rain rate in mm/h for all three gauges (each in one column)



    return
    ------

     ts_R_1_min_combo : pandas.Series
        Time series of combined minutely rain rate in mm/h

    """

    df_temp = (
        df_three_gauges_R_1_min.rolling(
            window=60 * hours_to_average_for_diff, center=True
        )
        .mean()
        .copy()
    )
    df_gauge_valid_from_diff = validity_from_relative_diff(
        df_temp,
        max_allowed_relative_diff=max_allowed_relative_diff,
        min_R=min_R / hours_to_average_for_diff,
    )
    df_temp = df_three_gauges_R_1_min.rolling(
        window=60 * hours_to_average_for_zeros, center=True
    ).mean()

    df_gauge_valid_from_zeros = validity_from_zeros(
        df_temp, min_R=min_R / hours_to_average_for_zeros
    )

    df_valid_combo = df_gauge_valid_from_zeros & df_gauge_valid_from_diff
    ts_R_1_min_combo = df_three_gauges_R_1_min[df_valid_combo].mean(axis=1)

    return ts_R_1_min_combo


def validity_from_zeros(df_three_gauges, min_R=0.0):
    df_valid_from_zeros = pd.DataFrame(index=df_three_gauges.index)

    # Round the passed DataFrame since small offset in floating point
    # representation (e.g. stemming from rolling averages) may introduce
    # errors when e.g. comparing to zero
    df_three_gauges = df_three_gauges.round(10)

    for gauge_id in gauge_ids:
        # Get the other two gauge IDs
        other_gauge_ids = list(set(gauge_ids) - set(gauge_id))
        df_not_valid = (df_three_gauges[gauge_id] == 0) & (
            (df_three_gauges[other_gauge_ids[0]] > min_R)
            | (df_three_gauges[other_gauge_ids[1]] > min_R)
        )
        df_valid_from_zeros[gauge_id] = ~df_not_valid

    return df_valid_from_zeros


def validity_from_relative_diff(df_three_gauges, max_allowed_relative_diff, min_R):

    df_valid_from_relative_diff = pd.DataFrame(index=df_three_gauges.index)

    for gauge_id in gauge_ids:

        pair_1, pair_2 = pairs[gauge_id]

        # Check whether the current gauge ID is first or last in the
        # pair string since this will determine in which gauge has been
        # subtracted from which one to calculate the difference. This
        # is important since we need to know the sign of the difference,
        # because the gauge with the larger values will be assumed to
        # be correct.
        if pair_1[0] == gauge_id:
            sign_1 = -1
        else:
            sign_1 = 1
        if pair_2[0] == gauge_id:
            sign_2 = -1
        else:
            sign_2 = 1

        df_greater_min_R = (df_three_gauges > min_R).any(axis=1)

        df_relative_diff_three_gauges = get_gauge_relative_diff(
            df_three_gauges, min_R=min_R
        )

        # df_diff_1 = df_three_gauges[gauge_id] - df_three_gauges[other_gauge_ids[0]]
        # df_diff_2 = df_three_gauges[gauge_id] - df_three_gauges[other_gauge_ids[1]]

        # df_relative_diff_1 = df_diff_1/df_three_gauges[gauge_id]
        # df_relative_diff_2 = df_diff_2/df_three_gauges[gauge_id]

        df_not_valid = df_greater_min_R & (
            (df_relative_diff_three_gauges[pair_1] * sign_1 > max_allowed_relative_diff)
            | (
                df_relative_diff_three_gauges[pair_2] * sign_2
                > max_allowed_relative_diff
            )
        )

        df_valid_from_relative_diff[gauge_id] = ~df_not_valid

    return df_valid_from_relative_diff


def get_gauge_diff(df_three_gauges):
    df_diff = pd.DataFrame(index=df_three_gauges.index)
    # Round the passed DataFrame since small offset in floating point
    # representation (e.g. stemming from rolling averages) may introduce
    # errors in the differences
    df_three_gauges = df_three_gauges.round(10)
    for pair_str in pairs["all"]:
        id_1, id_2 = pair_str.split("-")
        df_diff[pair_str] = df_three_gauges[id_1] - df_three_gauges[id_2]
    return df_diff


def get_gauge_relative_diff(df_three_gauges, min_R):
    df_relative_diff = pd.DataFrame(index=df_three_gauges.index)
    df_diff = get_gauge_diff(df_three_gauges)
    for pair_str in pairs["all"]:
        id_1, id_2 = pair_str.split("-")
        df_relative_diff[pair_str] = df_diff[pair_str] / (
            (df_three_gauges[id_1] + df_three_gauges[id_2]) / 2
        )
        df_relative_diff[pair_str][df_three_gauges[id_1] < min_R] = np.nan
        df_relative_diff[pair_str][df_three_gauges[id_2] < min_R] = np.nan
    return df_relative_diff


def validity_from_corr(df_corr_three_pairs, min_corr=0.9):
    """Estimate validity of individual gauges using correlation with the other two

    Parameters
    ----------

    df_three_gauges :

    min_corr :

    Returns
    -------

    df_valid_from_corr :


    """

    df_valid_from_corr = pd.DataFrame(index=df_corr_three_pairs.index)
    for gauge_id in gauge_ids:
        df_corr_1 = df_corr_three_pairs[pairs[gauge_id][0]]
        df_corr_2 = df_corr_three_pairs[pairs[gauge_id][1]]
        df_valid_from_corr[gauge_id] = (df_corr_1 >= min_corr) | (df_corr_2 >= min_corr)
    return df_valid_from_corr


def gauge_corr(df_three_gauges, corr_window_length):
    """Calculate correlation between the three gauges

    Parameters
    ----------

    df_three_gauges :

    corr_window_length :

    Returns
    -------

    df_corr_three_pairs : pandas.DataFrame
       DataFrame with the correlation of the three pairs ['1-2', '1-3', '2-3']
       in each column

    """

    df_corr_three_pairs = pd.DataFrame()
    correls = df_three_gauges.rolling(window=corr_window_length, center=True).corr()
    for pair_str in pairs["all"]:
        id_1, id_2 = pair_str.split("-")
        df_corr_three_pairs[pair_str] = correls.xs(
            key=id_1,
            axis=0,
            level=1,
        ).xs(key=id_2, axis=1)
        df_corr_three_pairs[pair_str][df_corr_three_pairs[pair_str] > 1] = 0
    return df_corr_three_pairs
