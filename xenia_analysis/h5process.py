import re
import logging
from pathlib import Path
from dataclasses import dataclass

import h5py
import pandas as pd
import numpy as np
from scipy import signal as sig

from logger import getLogger

pd.options.plotting.backend = "plotly"

LOGGER = getLogger(__name__)


class H5Keys:
    TRACKS = "tracks"
    NODES = "node_names"


class TentacleH5DataKeys:
    AVERAGE = "Average"
    MEDIAN = "Median"
    VARIANCE = "Variance"


@dataclass
class TentacleH5DataFrames:
    # data
    xdf: pd.DataFrame
    ydf: pd.DataFrame
    xdf_fuller: pd.DataFrame
    ydf_fuller: pd.DataFrame
    dists_df: pd.DataFrame
    dists_fuller_df: pd.DataFrame
    dists_full_normed_df: pd.DataFrame
    dists_sum_aggs: pd.DataFrame

    time_axis: np.ndarray
    peaks_timestamps_dict: dict[str, np.ndarray]
    rhythms_dict: dict[str, np.ndarray]

    aggs_peaks_timestamps_dict: dict[str, np.ndarray]
    aggs_rhythms_dict: dict[str, np.ndarray]

    # metadata
    xdf_nan_score: pd.DataFrame
    ydf_nan_score: pd.DataFrame

    def transpose(self):
        return TentacleH5DataFrames(
            xdf=self.xdf.T,
            ydf=self.ydf.T,
            xdf_fuller=self.xdf_fuller.T,
            ydf_fuller=self.ydf_fuller.T,
            dists_df=self.dists_df.T,
            dists_fuller_df=self.dists_fuller_df.T,
            dists_full_normed_df=self.dists_full_normed_df.T,
            dists_sum_aggs=self.dists_sum_aggs.T,
            xdf_nan_score=self.xdf_nan_score.T,
            ydf_nan_score=self.ydf_nan_score.T,
            # can't transpose vector and dicts:
            time_axis=self.time_axis,
            peaks_timestamps_dict=self.peaks_timestamps_dict,
            rhythms_dict=self.rhythms_dict,
            aggs_peaks_timestamps_dict=self.aggs_peaks_timestamps_dict,
            aggs_rhythms_dict=self.aggs_rhythms_dict,
        )

    def log_shape(self, level=logging.DEBUG):
        LOGGER.log(level, f"{self.xdf.shape=}")
        LOGGER.log(level, f"{self.ydf.shape=}")
        LOGGER.log(level, f"{self.xdf_fuller.shape=}")
        LOGGER.log(level, f"{self.ydf_fuller.shape=}")
        LOGGER.log(level, f"{self.dists_df.shape=}")
        LOGGER.log(level, f"{self.dists_fuller_df.shape=}")
        LOGGER.log(level, f"{self.dists_full_normed_df.shape=}")
        LOGGER.log(level, f"{self.dists_sum_aggs.shape=}")
        LOGGER.log(level, f"{self.xdf_nan_score.shape=}")
        LOGGER.log(level, f"{self.ydf_nan_score.shape=}")
        LOGGER.log(level, f"{self.time_axis.shape=}")

        LOGGER.log(level, f"{len(self.peaks_timestamps_dict.keys())=}")
        LOGGER.log(level, f"{len(self.rhythms_dict.keys())=}")
        LOGGER.log(level, f"{len(self.aggs_peaks_timestamps_dict.keys())=}")
        LOGGER.log(level, f"{len(self.aggs_rhythms_dict.keys())=}")


class H5Processor:
    def __init__(self, dirpath, file_details):
        self.substance = file_details["substance"]
        self.concentration = file_details["concentration"]["value"]
        self.concentration_unit = file_details["concentration"]["unit"]
        self.framerate = int(file_details["framerate_fps"])
        self.dirpath = dirpath
        self.filename = file_details["filename"]
        self.fullpath = Path(self.dirpath, self.filename)
        self.shortname = self._get_shortname()

        self.max_ctrl_frame = self.framerate * 60 * 4  # look at control part, upto 4 mins
        self.processed: TentacleH5DataFrames = None

    def _get_shortname(self):
        def fmt(exp_num, exp_well, substance, con, con_unit=""):
            return f"{exp_num}_{exp_well}_{substance}_{con}{con_unit}"

        shortname = self.filename
        try:
            shortname = shortname.removeprefix("labels.xenia").removesuffix(".analysis.h5")
            parts = shortname.split('_')[5:]
            exp_num, exp_well, substance, con = parts[:4]
            return fmt(exp_num, exp_well, substance, con)
        except:
            LOGGER.warning(f'failed to parse shortname out of {self.filename}, best effort-ing is {shortname=}')
        return shortname

    def process(self):
        with h5py.File(self.fullpath, "r") as f:
            tracks = f[H5Keys.TRACKS][:]
            index = [
                node_name.decode().replace("_", "-") for node_name in f[H5Keys.NODES][:]
            ]

        xdf = pd.DataFrame(tracks[0][0], index=index)
        ydf = pd.DataFrame(tracks[0][1], index=index)
        time_axis = np.arange(len(xdf.columns) - 1) / self.framerate
        dists_df = H5Processor._calc_dists_df(xdf, ydf)

        xdf_fuller, xdf_nan_score = H5Processor._smooth_missing_data_points(xdf)
        ydf_fuller, ydf_nan_score = H5Processor._smooth_missing_data_points(ydf)
        dists_fuller_df = H5Processor._calc_dists_df(xdf_fuller, ydf_fuller)
        dists_full_normed_df = self._normalize_df(dists_fuller_df)

        peaks_timestamps_dict = self._find_peak_timestamps(dists_full_normed_df)
        rhythms_dict = self._calc_rhythms(peaks_timestamps_dict)

        dists_sum_aggs = self._calc_dists_aggs(dists_full_normed_df)
        aggs_peaks_timestamps_dict = self._find_peak_timestamps(dists_sum_aggs)
        aggs_rhythms_dict = self._calc_rhythms(aggs_peaks_timestamps_dict)

        self.processed = TentacleH5DataFrames(
            xdf=xdf,
            ydf=ydf,
            time_axis=time_axis,
            xdf_fuller=xdf_fuller,
            ydf_fuller=ydf_fuller,
            dists_df=dists_df,
            dists_fuller_df=dists_fuller_df,
            dists_full_normed_df=dists_full_normed_df,
            dists_sum_aggs=dists_sum_aggs,
            aggs_peaks_timestamps_dict=aggs_peaks_timestamps_dict,
            aggs_rhythms_dict=aggs_rhythms_dict,
            peaks_timestamps_dict=peaks_timestamps_dict,
            rhythms_dict=rhythms_dict,
            xdf_nan_score=xdf_nan_score,
            ydf_nan_score=ydf_nan_score,
        ).transpose()  # plotting is better on long matrix rather than wide

        return self

    @staticmethod
    def _calc_dists_df(xdf: pd.DataFrame, ydf: pd.DataFrame):
        # calculating Euclidean distances: d(x,y) = √((x1-x0)²+(y1-y0)²)

        # get tentacle rows, skipping row zero: mouth row
        dx = xdf.iloc[1:] - xdf.iloc[0]  # delta x, matrix - vector subtraction
        dy = ydf.iloc[1:] - ydf.iloc[0]  # delta y, similarly

        dists = np.sqrt(dx**2 + dy**2)
        return pd.DataFrame(dists, columns=xdf.columns[1:])

    @staticmethod
    def _smooth_missing_data_points(df: pd.DataFrame):
        nan_score_calc = lambda d: d.isna().sum(axis=1) * 100 / d.shape[1]
        fuller = df.ffill(
            axis=1,  # fill rows
            limit=2,  # fill gaps of up to 2 NaN values
            limit_area="inside",  # interpolate - only fill NaNs surrounded by valid values
        )
        nan_score = pd.concat(
            list(map(nan_score_calc, [df, fuller])),
            keys=["before", "after"],
            axis=1,
        )
        return fuller, nan_score

    def _normalize_df(self, df: pd.DataFrame):
        data = {}
        for tentacle in df.index:
            moving_avg_vals = (
                pd.Series(df.loc[tentacle])
                .rolling(window=10, min_periods=2, closed='both')
                .mean()
                .to_numpy()
            )
            moving_avg_vals = pd.Series(moving_avg_vals)
            # moving_avg_vals = df.loc[tentacle]
            
            cmin = moving_avg_vals[: self.max_ctrl_frame].min()
            cmax = moving_avg_vals[: self.max_ctrl_frame].max()
            crange = cmax - cmin
            data[tentacle] = (moving_avg_vals - cmin) / crange
        normed = pd.DataFrame(data).T
        return normed

    def _find_peak_timestamps(self, dist_df: pd.DataFrame):
        avg_window = int(0.5 * self.framerate)
        percent = 95
        prominence = 0.1
        distance = self.framerate  # assuming pulse take at least a second
        # ⬇️ og width=0.5*fps, but avg_window=0.5*fps so assuming related
        width = avg_window

        data = {}
        for tentacle in dist_df.index:
            moving_avg = (
                pd.Series(dist_df.loc[tentacle])
                .rolling(window=avg_window, min_periods=2)
                .mean()
                .to_numpy()
            )
            moving_avg_normalized = moving_avg / np.nanpercentile(moving_avg, percent)
            peaks, _ = sig.find_peaks(
                moving_avg_normalized,
                distance=distance,
                prominence=prominence,
                width=width,
            )
            assert isinstance(peaks, np.ndarray)
            data[tentacle] = peaks / self.framerate
        return data

    def _calc_rhythms(self, peaks_timestamps: dict):
        data = {}
        c = 3
        for tentacle, timestamps in peaks_timestamps.items():
            ts:np.ndarray = timestamps
            ts = c / (ts[c:] - ts[:-c])

            # pad with the last value for the c missing values due to c avg
            ts = pd.Series(np.concatenate([ts, [np.nan]*c])).ffill(
                limit=c*2,  # how many consecutive NaNs to fill
                limit_area='outside',  # extrapolate
            )

            data[tentacle] = ts

        return data

    def _calc_dists_aggs(self, dists_df: pd.DataFrame):
        def _norm_vector(v: pd.Series):
            cmin = v[: self.max_ctrl_frame].min()
            cmax = v[: self.max_ctrl_frame].max()
            crange = cmax - cmin
            return (v - cmin) / crange

        avg = dists_df.mean()
        median = dists_df.median()
        var = dists_df.var()

        return pd.DataFrame(
            {
                TentacleH5DataKeys.AVERAGE: _norm_vector(avg),
                TentacleH5DataKeys.MEDIAN: _norm_vector(median),
                TentacleH5DataKeys.VARIANCE: _norm_vector(var),
            }
        ).T
