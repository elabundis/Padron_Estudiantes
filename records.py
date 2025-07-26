from dataclasses import dataclass

import pandas as pd


@dataclass
class YearRecord:
    """
    Keeps track, by means of a dataframe 'df', of students of a given 'major'
    in a 'faculty', whose curricula correspond to a certain 'plan' a given
    'year'.

    The dataframe must contain the columns: 'id', 'name', 'PERIODO', and
    'GRUPO'
    """
    year: int
    major: str
    faculty: str
    plan: int
    df: pd.DataFrame


