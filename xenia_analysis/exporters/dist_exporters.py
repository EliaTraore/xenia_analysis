import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from logger import getLogger
from .shared import BaseExporter

LOGGER = getLogger(__name__)


class ExportUnifiedPlot(BaseExporter):
    EXT = "unified-plot"
    Y_AXIS_TITLE = "Distance(t,m) [pixels]"
    X_AXIS_TITLE = "Time [min]"

    def _graph_title(self, processor):
        return f"Tentacles distance from Mouth over Time ({processor.substance} {processor.concentration} {processor.concentration_unit})"

    def _export(self, processor, df: pd.DataFrame, name: str):
        xaxis = processor.processed.time_axis[:] / 60 # convert to minutes
        fig: go.Figure = df.plot.scatter(
            y=df.columns, x=xaxis,
            title=dict(
                text=self._graph_title(processor),
                subtitle=dict(text=name)
            )
        )
        fig.update_layout(
            **self.base_fig_layout(),
            yaxis_title=self.Y_AXIS_TITLE,
            xaxis_title=self.X_AXIS_TITLE,
            xaxis=dict(range=[0, max(xaxis) * 1.01]),  # initial shown x-range
        )
        if self.show_plot:
            fig.show()
        self.save_fig(processor, fig, node_name=f"{name}.{self.EXT}")

    def export(self, processor):
        self._export(
            processor,
            df=processor.processed.dists_full_normed_df,
            name="normalized-post-interpolation",
        )


class ExportInteractivePlot(BaseExporter):
    EXT = "multi-plot"
    Y_AXIS_TITLE = "Distance(t,m) [pixels]"
    X_AXIS_TITLE = "Time [min]"
    AXIS_FONT_SIZE = 12

    def _graph_title(self, processor):
        return f"Tentacles distance from Mouth over Time ({processor.substance} {processor.concentration} {processor.concentration_unit})"

    def _export(self, processor, df: pd.DataFrame, name: str):
        xaxis = processor.processed.time_axis[:] / 60 # convert to minutes

        fig = make_subplots(
            rows=4,
            cols=2,
            subplot_titles=df.columns,
        )
        for i, col in enumerate(df.columns):
            row_i = 1 + (i // 2)
            col_i = 1 + (i % 2)
            fig.add_trace(go.Scatter(y=df[col], x=xaxis), row=row_i, col=col_i)
            LOGGER.debug(f"placing plot of {col=} in ({row_i}, {col_i})")

            next(fig.select_yaxes(row=row_i, col=col_i)).update(
                title=dict(text=self.Y_AXIS_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="y",
            )
            next(fig.select_xaxes(row=row_i, col=col_i)).update(
                title=dict(text=self.X_AXIS_TITLE, font=dict(size=self.AXIS_FONT_SIZE)),
                matches="x",
            )
        fig.update_layout(
            showlegend=False,
            title=dict(
                text=self._graph_title(processor),
                subtitle=dict(text=name)
            )
        )

        if self.show_plot:
            fig.show()
        self.save_fig(processor, fig, node_name=f"{name}.multi-plot")

    def export(self, processor):
        self._export(
            processor,
            df=processor.processed.dists_full_normed_df,
            name="normalized-post-interpolation",
        )
