from logger import getLogger

LOGGER = getLogger(__name__)

class Extensions:
    HTML = "html"
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"

    @classmethod
    def getExporters(cls, fig) -> dict:
        return {
            cls.HTML: fig.write_html,
            cls.PNG: fig.write_image,
            cls.SVG: fig.write_image,
            cls.PDF: fig.write_image,
        }

class BaseExporter:
    def __init__(self, output_manager):
        self.output_manager = output_manager
        self.gen_csv = output_manager.gen_csv
        self.show_plot = output_manager.show_plot


    def export(self, processor):
        LOGGER.warning(f"{type(self)} has unimplemented export method, doing nothing")

    def get_output_full_path(self, processor, ext, name=""):
        name = f"{processor.shortname}.{name}" if len(name) > 0 else processor.shortname
        return self.output_manager.get_output_full_path(f"{name}.{ext}")

    def base_fig_layout(self):
        return dict(
            legend_title_text=None,
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        )

    def save_fig(self, processor, fig, node_name, exts=(Extensions.HTML,)):
        exporters = Extensions.getExporters(fig)
        for ext, exporter in exporters.items():
            if ext not in exts:
                continue
            LOGGER.debug(f"trying to export to {ext=}")
            try:
                exporter(self.get_output_full_path(processor, name=node_name, ext=ext))
            except Exception:
                LOGGER.error(f"export failed for {ext=}", exc_info=True)
