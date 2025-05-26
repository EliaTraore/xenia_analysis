import xlsxwriter
import pandas as pd

from logger import getLogger
from .shared import BaseExporter

LOGGER = getLogger(__name__)


class ExportGeneralDfsToExcel(BaseExporter):
    def export(self, processor):
        output_path = self.get_output_full_path(processor, ext="xlsx", name="general")
        outs = {
            "x-values-missing-percentage": processor.processed.xdf_nan_score,
            "y-values-missing-percentage": processor.processed.ydf_nan_score,
        }

        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            for sheet_name, df in outs.items():
                LOGGER.debug(f"trying to add {sheet_name=}")
                try:
                    df.to_excel(writer, sheet_name=sheet_name)
                except Exception:
                    LOGGER.error(f"failed to add {sheet_name=}", exc_info=True)


class ExportAggsDictsToExcel(BaseExporter):
    def export(self, processor):
        output_path = self.get_output_full_path(
            processor, ext="xlsx", name="aggs"
        )
        outs = {
            "aggs-peaks-timestamp": processor.processed.aggs_peaks_timestamps_dict,
            "aggs-pulse-rate": processor.processed.aggs_rhythms_dict,
        }
        with xlsxwriter.Workbook(output_path) as workbook:
            # save dicts
            for sheet_name, data in outs.items():
                LOGGER.debug(f"trying to add {sheet_name=}")
                writer = workbook.add_worksheet(sheet_name)
                try:
                    for col, tentacle in enumerate(data):
                        writer.write(0, col, tentacle)
                        for r, val in enumerate(data[tentacle]):
                            writer.write(r + 1, col, val)
                except Exception:
                    LOGGER.error(f"failed to add {sheet_name=}", exc_info=True)

            # save og time axis
            for sheet_name, data in {
                "time-axis-secs": processor.processed.time_axis
            }.items():
                writer = workbook.add_worksheet(sheet_name)
                writer.write(0, 0, sheet_name)
                for row in range(len(data)):
                    writer.write(row + 1, 0, data[row])


class ExportByTentacleToExcel(BaseExporter):
    def export(self, processor):
        time_axis = {
            "time axis (secs)": pd.Series(processor.processed.time_axis),
            "time axis (mins)": pd.Series(processor.processed.time_axis/60),
        }
        self._export_dists(processor, time_axis)
        self._export_peaks(processor, time_axis)

    def _export_dists(self, processor, time_axis: dict):
        output_path = self.get_output_full_path(
            processor, ext="xlsx", name="by-tentacle-dist"
        )
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            writer_helper = PandasExcelUtils(writer)

            # sheet for dist agg
            sheet_name = "agg"
            df = pd.DataFrame({
                **time_axis,
                **{
                    f" {col} ": processor.processed.dists_sum_aggs[col]
                    for col in processor.processed.dists_sum_aggs.columns
                },
            })
            writer_helper.to_excel(data=df, sheet_name=sheet_name)

            # sheet per tentacle
            for tentacle in processor.processed.dists_df.columns:
                sheet_name = tentacle
                df = pd.DataFrame({
                    **time_axis,
                    "x values": processor.processed.xdf[tentacle],
                    "y values": processor.processed.ydf[tentacle],
                    "dist": processor.processed.dists_df[tentacle],
                    "x values interpolated": processor.processed.xdf_fuller[tentacle],
                    "y values interpolated": processor.processed.ydf_fuller[tentacle],
                    "dist of interpolated": processor.processed.dists_fuller_df[tentacle],
                    "dist interpolated normalized": processor.processed.dists_full_normed_df[tentacle],
                })
                LOGGER.debug(f"trying to add {sheet_name=}")
                try:
                    writer_helper.to_excel(data=df, sheet_name=sheet_name)
                except Exception:
                    LOGGER.error(f"failed to add {sheet_name=}", exc_info=True)

    @staticmethod
    def _gen_peaks_agg_sheet_data(processor):
        dicts = {
            "peaks (secs)": processor.processed.aggs_peaks_timestamps_dict,
            "peaks (mins)": {k: v/60  for (k,v) in processor.processed.aggs_peaks_timestamps_dict.items()},
            "pulse (hz)": processor.processed.aggs_rhythms_dict,
        }
        data = {}
        for col in processor.processed.aggs_rhythms_dict.keys():
            data.update({
                f"{col} {k}": pd.Series(dicts[k][col]) for k in dicts
            })

        return data

    def _export_peaks(self, processor, time_axis: dict):
        output_path = self.get_output_full_path(
            processor, ext="xlsx", name="by-tentacle-peaks"
        )
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            writer_helper = PandasExcelUtils(writer)

            # sheet for peaks agg
            sheet_name = "agg"
            writer_helper.to_excel(data=pd.DataFrame({
                **self._gen_peaks_agg_sheet_data(processor),
            }), sheet_name=sheet_name)

            # sheet per tentacle
            for tentacle in processor.processed.peaks_timestamps_dict:
                sheet_name = tentacle
                df = pd.DataFrame({
                    "peaks timestamp (secs)": pd.Series(processor.processed.peaks_timestamps_dict[tentacle]),
                    "peaks (mins)": pd.Series(processor.processed.peaks_timestamps_dict[tentacle])/60,
                    "pulse rate (hz)": pd.Series(processor.processed.rhythms_dict[tentacle]),
                })

                LOGGER.debug(f"trying to add {sheet_name=}")
                try:
                    writer_helper.to_excel(data=df, sheet_name=sheet_name)
                except Exception:
                    LOGGER.error(f"failed to add {sheet_name=}", exc_info=True)


class PandasExcelUtils:
    def __init__(self, writer: pd.ExcelWriter):
        self.writer = writer
        self.fmt = None

    def _get_fmt(self):
        if not self.fmt:
            self.fmt = self.writer.book.add_format()
            # self.fmt = self.writer.book.add_format({"num_format": "#,##0.00000"})
            self.fmt.set_align('center')
        return self.fmt

    def _auto_fit_cols_to_title(self, df:pd.DataFrame, sheet_name: str=None, fmt=None):
        sheets = [sheet_name] if sheet_name else self.writer.sheets.keys()
        fmt = fmt or self._get_fmt()
        for sheet_name in sheets:
            worksheet = self.writer.sheets[sheet_name]
            for i, col in enumerate(df.columns):
                idx = i + 1
                title_width = len(str(col))
                worksheet.set_column(idx, idx, title_width, cell_format=fmt)

    def _freeze_headers(self,sheet_name:str):
        worksheet = self.writer.sheets[sheet_name]
        worksheet.freeze_panes(1, 3)  # Freeze the first row & first 3 cols

    def to_excel(self, data:pd.DataFrame, sheet_name):
        data.to_excel(self.writer, sheet_name=sheet_name)
        self._auto_fit_cols_to_title(data, sheet_name)
        self._freeze_headers(sheet_name)
