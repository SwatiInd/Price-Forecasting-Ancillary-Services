import pandas as pd

def get_query_periods(start_date, end_date):
    """
    Return the date bounds (as ISO strings) required by the NG ESO API.

    The NESO endpoint is **inclusive** of `start_date` and **exclusive** of
    `end_date`. To capture a full trading day in EFA terms:

    * **Start date** must shift back by one calendar day, because EFA-1
      begins at 23:00 on the evening *before* the requested `start_date`.
    * **End date** must shift forward by one calendar day, because the API
      stops at 00:00 (end_date); we need it to reach 23:00 of that last day
      to include EFA-6, which starts at 19:00.  
      Hence the “exclusive” bound is `end_date + 1 day`.

    Parameters
    ----------
    start_date : pandas.Timestamp
    end_date   : pandas.Timestamp
    Returns
    -------
    tuple[str, str]
        (`query_start_date`, `query_end_date`) suitable for the API,
        both formatted as `"YYYY-MM-DD"`.

    Example
    -------
    >>> get_query_periods(pd.Timestamp('2025-06-12'),
    ...                   pd.Timestamp('2025-06-13'))
    ('2025-06-11', '2025-06-14')
    """
    # Inclusive start: move back one day to hit 23:00 of the previous calendar day
    query_start_date = (start_date - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    # Exclusive end: add one day so the API window covers up to 23:59 of end_date
    query_end_date   = (end_date   + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    return query_start_date, query_end_date


def get_efa_index(start_date, end_date):
    """
    Build a **4-hourly DatetimeIndex** that exactly matches the Electricity
    Forward Agreement (EFA) block boundaries spanning the requested trading
    window.

    Why the ± offsets?
    ------------------
    * **EFA-1** starts at **23:00** on the calendar day *before*
      `start_date`.  
      → Shift the left edge **back by one hour** so the first timestamp is
      `start_date 00:00 – 1 h` = `23:00` of the previous day.

    * **EFA-6** starts at **19:00** on `end_date`.  
      → Shift the right edge **forward by nineteen hours** so this
      19:00 boundary is included.

    The resulting index therefore begins at the opening of EFA-1 for the
    first trading day and ends at the opening of EFA-6 for the last trading
    day, stepping every 4 hours.

    Parameters
    ----------
    start_date : pandas.Timestamp
        First trading date you want (00:00 of that day).
    end_date   : pandas.Timestamp
        Last trading date you want (00:00 of that day).

    Returns
    -------
    pandas.DatetimeIndex
        4-hourly points from *23:00 previous-day* through *19:00 end-day*,
        tz-naïve (or change `tz=` as needed).

    Example
    -------
    >>> idx = get_efa_index(pd.Timestamp("2025-06-12"),
    ...                     pd.Timestamp("2025-06-13"))
    >>> idx[:3]
    DatetimeIndex(['2025-06-11 23:00:00', '2025-06-12 03:00:00',
                   '2025-06-12 07:00:00'], dtype='datetime64[ns]', freq='4H')
    """

    # 23:00 of the day before EFA-1
    efa_start_time = start_date - pd.Timedelta(hours=1)

    # 19:00 of the last trading day (start of EFA-6)
    efa_end_time   = end_date + pd.Timedelta(hours=19)

    # 4-hourly boundary index (tz-naïve by default; pass tz=… if required)
    efa_index = pd.date_range(efa_start_time, efa_end_time, freq="4h", tz=None)

    return efa_index


def get_settlement_periods(start_date, end_date):
    """
    Return the **timestamp range** that brackets every 30-minute Settlement
    Period (SP) needed to cover the requested trading days in EFA terms.

    Offsets explained
    -----------------
    * **Left edge (sp_start_time)**  
      EFA-1 begins at **23:00 on the calendar day before `start_date`**.  
      To pick up the first Settlement Period that belongs to EFA-1
      (23:00-23:30), shift the start back **one hour**.

    * **Right edge (sp_end_time)**  
      The final Settlement Period in EFA-6 starts at **22:30** on `end_date`
      and ends at 23:00.  
      Adding **22 hours 30 minutes** to `end_date 00:00` lands exactly on
      that 22:30 timestamp, so every SP from EFA-1 through EFA-6 is covered.

    Parameters
    ----------
    start_date : pandas.Timestamp
        First trading date you want (interpreted at 00:00 of that day).
    end_date   : pandas.Timestamp
        Last trading date you want (00:00 that day).

    Returns
    -------
    tuple[pandas.Timestamp, pandas.Timestamp]
        (`sp_start_time`, `sp_end_time`) – the inclusive bounds you should
        feed into any half-hourly SP query.

    Example
    -------
    >>> get_settlement_periods(pd.Timestamp('2025-06-12'),
    ...                        pd.Timestamp('2025-06-13'))
    (Timestamp('2025-06-11 23:00:00'), Timestamp('2025-06-13 22:30:00'))
    """
    # 23:00 previous day → first SP in EFA-1
    sp_start_time = start_date - pd.Timedelta(hours=1)

    # 22:30 end day → last SP in EFA-6
    sp_end_time   = end_date + pd.Timedelta(hours=22.5)

    return sp_start_time, sp_end_time







