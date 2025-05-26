import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from logger import getLogger

from .shared import BaseExporter

LOGGER = getLogger(__name__)


def to_ext_name(s: str):
    return s.lower().translate(str.maketrans({" ": "-", "(": "", ")": ""}))


class ExportRhythmsMultiPlot(BaseExporter):
    Y_AXIS_TITLE = "Pulse [Hz]"
    X_AXIS_TITLE = "Time [min]"
    MAIN_TITLE = "Rhythm over Time"
    AXIS_FONT_SIZE = 12

    def _graph_title(self, processor):
        return f"{self.MAIN_TITLE} ({processor.substance} {processor.concentration} {processor.concentration_unit})"

    def export(self, processor):
        xdata: dict = processor.processed.peaks_timestamps_dict
        ydata: dict = processor.processed.rhythms_dict
        name = to_ext_name(self.MAIN_TITLE)

        fig = make_subplots(rows=4, cols=2, subplot_titles=list(xdata))
        for i, col in enumerate(xdata):
            row_i = 1 + (i // 2)
            col_i = 1 + (i % 2)

            xaxis = pd.Series(xdata[col][:]) / 60  # convert to minutes
            yaxis = pd.Series(ydata[col])
            fig.add_trace(go.Scatter(y=yaxis, x=xaxis), row=row_i, col=col_i)
            LOGGER.debug(f"placing plot of {col=} in ({row_i}, {col_i})")

            next(fig.select_yaxes(row=row_i, col=col_i)).update(
                title=dict(text=self.Y_AXIS_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="y",
            )
            next(fig.select_xaxes(row=row_i, col=col_i)).update(
                title=dict(text=self.X_AXIS_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="x",
            )
        fig.update_layout(title_text=self._graph_title(processor), showlegend=False)

        if self.show_plot:
            fig.show()
        self.save_fig(processor, fig, node_name=f"{name}.multi-plot")


class ExportRhythmVsDistMultiPlot(BaseExporter):
    MAIN_TITLE = "Distance and Rhythm over Time per Tentacle"
    X_TITLE = "Time [min]"

    TOP_Y_TITLE = "Distance(t,m) [pixels]"
    TOP_MAIN_TITLE = "Distance over Time"

    BOTTOM_Y_TITLE = "Pulse [Hz]"
    BOTTOM_MAIN_TITLE = "Rhythm over Time"

    AXIS_FONT_SIZE = 12

    def _export(
        self,
        processor,
        name: str,
        dist_x: np.ndarray,
        dist_y: pd.DataFrame,
        rhythm_x: dict,
        rhythm_y: dict,
    ):
        num_cols = len(dist_y.columns)
        name = to_ext_name(f"{self.MAIN_TITLE} ({name})")
        titles = sum(
            [
                [f"{col} {self.TOP_MAIN_TITLE}" for col in dist_y.columns],
                [f"{col} {self.BOTTOM_MAIN_TITLE}" for col in dist_y.columns],
            ],
            start=[],
        )

        fig = make_subplots(rows=2, cols=num_cols, subplot_titles=titles)

        # dist data in first row
        row = 1
        for c, col in enumerate(dist_y.columns):
            col_i = c + 1
            fig.add_trace(go.Scatter(y=dist_y[col], x=dist_x), row=row, col=col_i)
            LOGGER.debug(f"placing plot of {col=} in ({row}, {col_i})")

            next(fig.select_yaxes(row=row, col=col_i)).update(
                title=dict(text=self.TOP_Y_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="y",
            )
            next(fig.select_xaxes(row=row, col=col_i)).update(
                title=dict(text=self.X_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="x",
            )

        # rhythm data in second row
        row = 2
        for c, col in enumerate(rhythm_x):
            col_i = c + 1

            xaxis = pd.Series(rhythm_x[col][:]) / 60  # convert to minutes
            yaxis = pd.Series(rhythm_y[col])
            fig.add_trace(go.Scatter(y=yaxis, x=xaxis), row=row, col=col_i)
            LOGGER.debug(f"placing plot of {col=} in ({row}, {col_i})")

            next(fig.select_yaxes(row=row, col=col_i)).update(
                title=dict(
                    text=self.BOTTOM_Y_TITLE, font=dict(size=self.AXIS_FONT_SIZE)
                ),
                matches="y",
            )
            next(fig.select_xaxes(row=row, col=col_i)).update(
                title=dict(text=self.X_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="x",
            )

        fig.update_layout(
            showlegend=False,
            height=1000,
            width=1000 * num_cols,
        )

        if self.show_plot:
            fig.show()
        self.save_fig(processor, fig, node_name=f"{name}.multi-plot")

    def export(self, processor):
        time_axis = processor.processed.time_axis[:] / 60  # convert to minutes

        self._export(
            processor,
            name="all",
            dist_x=time_axis,
            dist_y=processor.processed.dists_full_normed_df,
            rhythm_x=processor.processed.peaks_timestamps_dict,
            rhythm_y=processor.processed.rhythms_dict,
        )

        self._export(
            processor,
            name="agg",
            dist_x=time_axis,
            dist_y=processor.processed.dists_sum_aggs,
            rhythm_x=processor.processed.aggs_peaks_timestamps_dict,
            rhythm_y=processor.processed.aggs_rhythms_dict,
        )
