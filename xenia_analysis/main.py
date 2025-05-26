from pathlib import Path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from logger import getLogger, set_global_log_level_debug
from h5process import H5Processor
from xenio import InputsLoader, OutputsManager
from exporters.h5_exporters import SingleH5Exporter


LOGGER = getLogger(__name__)


def parseArgs():
    parser = ArgumentParser(
        prog="Xenia analysis", formatter_class=ArgumentDefaultsHelpFormatter
    )
    # fmt: off
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="path of the input dir with details.json",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=Path(__file__, "..", "..", "outputs").resolve(),
        help="dir to save the output under",
    )
    parser.add_argument(
        "--out-dir-suffix",
        help="suffix to add to the generated output dir name",
    )
    parser.add_argument(
        "--copy-inputs",
        default=False, action="store_true",
        help="don't copy the input dir to the output dir",
    )
    parser.add_argument(
        "--gen-csv",
        default=False, action="store_true",
        help="if to generate csv files for all the generated plots",
    )
    parser.add_argument(
        "--show",
        default=False, action="store_true",
        help="if to show the generated plots",
    )
    parser.add_argument(
        "--delete-all-other-outputs",
        default=False, action="store_true",
        help="if to clear out the outputs dir",
    )
    parser.add_argument(
        "-v"
        "--debug",
        dest="set_debug",
        default=False, action="store_true",
        help="set log level to debug (verbose mode)",
    )
    # fmt: on
    return parser.parse_args()


def main():
    args = parseArgs()
    if args.set_debug:
        set_global_log_level_debug()

    LOGGER.info(f"starting execution with {args=}")

    input_dir = args.input
    input_loader = InputsLoader(input_dir)
    output_manager = OutputsManager(
        args.output,
        input_loader=input_loader,
        no_copy=not args.copy_inputs,
        gen_csv=args.gen_csv,
        show_plot=args.show,
        name_suffix=args.out_dir_suffix,
    )

    if args.delete_all_other_outputs:
        output_manager.delete_all_other_outputs()

    inputs = input_loader.get_inputs()

    outputs = []
    LOGGER.info("processing h5...")
    for file_details in inputs:
        try:
            processor = H5Processor(input_dir, file_details)
            outputs.append(processor.process())
        except:
            LOGGER.error(f"failed to process file: {file_details}", exc_info=True)

    LOGGER.info("exporting processed...")
    single_exporter = SingleH5Exporter(output_manager)
    for i, processed in enumerate(outputs):
        LOGGER.info(f"[{i}/{len(outputs)}] exporting {processed.filename}")
        single_exporter.export(processed)


    LOGGER.info(f"execution completed, results in {output_manager.output_dir_path}")


if __name__ == "__main__":
    main()
