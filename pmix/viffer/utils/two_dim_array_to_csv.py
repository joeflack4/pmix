"""2d array to csv."""
import pandas as pd
from io import StringIO


def two_dim_arr_to_csv(_2d_array):
    """2d array to csv."""
    df = pd.DataFrame(_2d_array[1:], columns=_2d_array[0])
    csv_str_io = StringIO()
    df.to_csv(csv_str_io)
    csv_str = csv_str_io.getvalue()
    return csv_str
