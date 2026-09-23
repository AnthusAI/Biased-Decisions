"""Metrics: pure functions from recorded answers to the numbers each study reports.

No engine, no I/O beyond ``flips.write_rows``. See ``flips.py`` (flip rates, accuracy, ECE, the
gender/pairs/race-name studies), ``shifts.py`` (the second race attempt and the age-insertion
study), ``shortlist.py`` (the ranked-screen study) and ``bootstrap.py`` (the shared percentile
bootstrap CI, seeded ``random.Random(0)``, 1,000 resamples by default).
"""
