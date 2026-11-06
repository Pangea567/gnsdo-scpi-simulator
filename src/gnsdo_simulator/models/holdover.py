"""Linear holdover model used by the ELECO review revision.

x(t) = x0 + y_h*t, with x and t in seconds and y_h dimensionless.
The FEE reading is a magnitude reference, not a measured signed frequency
offset. Mapping it to y_h is an explicit simulation assumption. The manual's
8e-14 Allan-deviation figure is not an ageing coefficient and is not used.
This model is not a metrological prediction of the physical oscillator.
"""

SECONDS_PER_DAY = 86400.0
NOMINAL_LOCKED_TINT_SECONDS = 0.0


def holdover_tint_seconds(
    elapsed_seconds: float,
    entry_tint_seconds: float = NOMINAL_LOCKED_TINT_SECONDS,
    freq_error_estimate: float = 0.0,
) -> float:
    """Return x0 + y_h*t; the legacy argument name denotes effective y_h.

    The caller supplies a signed effective fractional frequency offset;
    the function does not infer that offset from an Allan statistic.
    Non-positive elapsed time returns the entry phase unchanged.
    """
    return entry_tint_seconds + freq_error_estimate * max(0.0, elapsed_seconds)
