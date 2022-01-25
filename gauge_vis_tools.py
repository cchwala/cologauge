import matplotlib.pyplot as plt
import numpy as np

# The gauge IDs which are used as column names in the DataFrames
gauge_ids = ["1", "2", "3"]

# Colors for the three individual gauge of each station
color_dict = {
    "1": (0.22335772267769388, 0.6565792317435265, 0.8171355503265633),
    "2": (0.6423044349219739, 0.5497680051256467, 0.9582651433656727),
    "3": (0.9603888539940703, 0.3814317878772117, 0.8683117650835491),
    "combo": "r",
}

# The above color dict is produced by using the seaborn library
#
# import seaborn as sns
# colors =  sns.color_palette("husl", 8)
# color_dict = {'1': colors[5],
#               '2': colors[6],
#               '3': colors[7]}

# Less aggressive colored alternative
# color_dict = {'1': (0.21044753832183283, 0.6773105080456748, 0.6433941168468681),
#              '2': (0.22335772267769388, 0.6565792317435265, 0.8171355503265633),
#              '3': (0.6423044349219739, 0.5497680051256467, 0.9582651433656727)}

# The above color dict is produced by using the seaborn library
#
# import seaborn as sns
# colors =  sns.color_palette("husl", 8)
# color_dict = {'1': colors[4],
#               '2': colors[5],
#               '3': colors[6]}


def plot_three_gauges(
    df_three_gauges,
    df_gauge_combo=None,
    linestyle="-",
    combo_linestyle="--",
    alpha=1,
    figsize=(12, 3),
    ax=None,
    legend_prefix="",
    margins=0.05,
):
    """
    Plot contents of DataFrame with data from the three gauges each station has

    Parameters
    ----------

    df_three_gauges : pandas.DataFrame
        The standard DataFrame for ScaleX gauge data at one location with the three
        columns ['1', '2', '3'] for the respective gauges
    ax : matplotlib axes object (optional)
        Axes of an existing figure

    """

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    for gauge_id in gauge_ids:
        ax.plot(
            df_three_gauges[gauge_id].index,
            df_three_gauges[gauge_id].values,
            color=color_dict[gauge_id],
            linestyle=linestyle,
            alpha=alpha,
            label=legend_prefix + "Gauge #" + gauge_id,
        )

    if df_gauge_combo is not None:
        ax.plot(
            df_gauge_combo.index,
            df_gauge_combo.values,
            color=color_dict["combo"],
            linestyle=combo_linestyle,
            label="Combination",
        )

    y_lim_max = ax.get_ylim()[1]
    ax.set_ylim(-y_lim_max * margins, y_lim_max + y_lim_max * margins)

    ax.legend(loc="best")

    return ax


def _add_patch_for_gauge(ax, x, width, gauge_id):
    from matplotlib.patches import Rectangle

    offset_dict = {"1": 2, "2": 1, "3": 0}

    color = color_dict[gauge_id]
    offset = offset_dict[gauge_id]

    ax.add_patch(
        Rectangle(
            xy=(x, offset), width=width, height=1, facecolor=color, edgecolor="none"
        )
    )


def plot_gauge_validity(df_gauges_valid, ax=None):
    """Generate plot with colored patches where gauges are valid

    Parameters
    ----------

    df_gauges_valid : pandas.DataFrame
        DataFrame with the three columns '1', '2', '3' for each gauge

    Returns
    -------

    ax : matplotlib axes object

    """
    from matplotlib import dates

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 3))

    ix_datenum = dates.date2num(df_gauges_valid.index.to_pydatetime())
    patch_width_increment = ix_datenum[1] - ix_datenum[0]

    for gauge_id in df_gauges_valid.columns:
        last_i_valid = False
        current_patch_width = 0
        t_i_start = None

        # Go along time series, derive length of valid period and
        # add patches with derived length
        for t_i, valid in df_gauges_valid[gauge_id].iteritems():
            if valid:
                if not last_i_valid:
                    t_i_start = t_i
                    current_patch_width = patch_width_increment
                else:
                    current_patch_width = current_patch_width + patch_width_increment
                last_i_valid = True
            else:
                if last_i_valid:
                    i_num = dates.date2num(t_i_start.to_pydatetime())
                    _add_patch_for_gauge(
                        ax=ax, x=i_num, width=current_patch_width, gauge_id=gauge_id
                    )
                    current_patch_width = 0
                last_i_valid = False
        # At the end of the time series, plot a last patch if there is still
        # one that has to be drawn (which is the case if the above for-loop
        # ends with a valid value
        if last_i_valid:
            i_num = dates.date2num(t_i_start.to_pydatetime())
            _add_patch_for_gauge(
                ax=ax, x=i_num, width=current_patch_width, gauge_id=gauge_id
            )
            current_patch_width = 0
            last_i_valid = False

    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_ylim([-0.1, 3.1])
    ax.set_yticklabels(["Gauge #3", "Gauge #2", "Gauge #1"])

    # ax.autoscale()

    return ax
