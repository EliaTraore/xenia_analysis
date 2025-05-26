import logging

from .shared import BaseExporter

from .dist_exporters import (
    ExportInteractivePlot,
)

from .peak_exporters import (
    ExportRhythmsMultiPlot,
    ExportRhythmVsDistMultiPlot
)

from .excel_exporters import (
    ExportByTentacleToExcel,
)

from logger import getLogger, log_runtime


LOGGER = getLogger(__name__)


class SingleH5Exporter(BaseExporter):
    def export(self, processor):
        exporters = [
            lambda: ExportInteractivePlot(self.output_manager),
            lambda: ExportRhythmsMultiPlot(self.output_manager),
            lambda: ExportRhythmVsDistMultiPlot(self.output_manager),
        ]
        if self.gen_csv:
            exporters.extend([
                lambda: ExportByTentacleToExcel(self.output_manager),
            ])
        for i, exporter_getter in enumerate(exporters):
            exporter = exporter_getter()
            if not exporter:
                continue
            exporter.export(processor)
            LOGGER.debug(f"exporter[{i}] done")
