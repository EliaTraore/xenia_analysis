"""Module managing input/output (xenia-io) behaviors around the data."""

import re
import json
import random
import shutil
import platform
from pathlib import Path
from datetime import datetime

from logger import getLogger, log_runtime

LOGGER = getLogger(__name__)


INPUT_CONFIG_JSON_NAME = "details.json"
OUTPUT_SUMMARY_JSON_NAME = "metadata.json"
NAMES_SALT = ['black', 'navy', 'darkblue', 'mediumblue', 'blue', 'darkgreen', 'green', 'teal', 'darkcyan', 'deepskyblue', 'darkturquoise', 'mediumspringgreen', 'lime', 'springgreen', 'aqua', 'cyan', 'midnightblue', 'dodgerblue', 'lightseagreen', 'forestgreen', 'seagreen', 'darkslategray', 'darkslategrey', 'limegreen', 'mediumseagreen', 'turquoise', 'royalblue', 'steelblue', 'darkslateblue', 'mediumturquoise', 'indigo', 'darkolivegreen', 'cadetblue', 'cornflowerblue', 'rebeccapurple', 'mediumaquamarine', 'dimgray', 'dimgrey', 'slateblue', 'olivedrab', 'slategray', 'slategrey', 'lightslategray', 'lightslategrey', 'mediumslateblue', 'lawngreen', 'chartreuse', 'aquamarine', 'maroon', 'purple', 'olive', 'gray', 'grey', 'skyblue', 'lightskyblue', 'blueviolet', 'darkred', 'darkmagenta', 'saddlebrown', 'darkseagreen', 'lightgreen', 'mediumpurple', 'darkviolet', 'palegreen', 'darkorchid', 'yellowgreen', 'sienna', 'brown', 'darkgray', 'darkgrey', 'lightblue', 'greenyellow', 'paleturquoise', 'lightsteelblue', 'powderblue', 'firebrick', 'darkgoldenrod', 'mediumorchid', 'rosybrown', 'darkkhaki', 'silver', 'mediumvioletred', 'indianred', 'peru', 'chocolate', 'tan', 'lightgray', 'lightgrey', 'thistle', 'orchid', 'goldenrod', 'palevioletred', 'crimson', 'gainsboro', 'plum', 'burlywood', 'lightcyan', 'lavender', 'darksalmon', 'violet', 'palegoldenrod', 'lightcoral', 'khaki', 'aliceblue', 'honeydew', 'azure', 'sandybrown', 'wheat', 'beige', 'whitesmoke', 'mintcream', 'ghostwhite', 'salmon', 'antiquewhite', 'linen', 'lightgoldenrodyellow', 'oldlace', 'red', 'fuchsia', 'magenta', 'deeppink', 'orangered', 'tomato', 'hotpink', 'coral', 'darkorange', 'lightsalmon', 'orange', 'lightpink', 'pink', 'gold', 'peachpuff', 'navajowhite', 'moccasin', 'bisque', 'mistyrose', 'blanchedalmond', 'papayawhip', 'lavenderblush', 'seashell', 'cornsilk', 'lemonchiffon', 'floralwhite', 'snow', 'yellow', 'lightyellow', 'ivory', 'white'] # fmt: skip


class JSON_KEYS:
    INPUTS = "inputs"
    INPUT_DIR_PATH = "input-path"

    FILENAME = "filename"
    SUBSTANCE = "substance"
    CONCENTRATION = "concentration"
    CONCENTRATION_VALUE = "value"
    CONCENTRATION_UNIT = "unit"
    FRAMERATE = "framerate_fps"


class InputsLoader:
    def __init__(self, input_dir):
        self.input_dir = input_dir

        if not Path(input_dir).is_dir():
            LOGGER.error(f"{input_dir=} doesn't exist, stopping execution.")
            raise ValueError()

    def get_input_details_json_path(self) -> Path:
        return Path(self.input_dir, INPUT_CONFIG_JSON_NAME).resolve()

    def get_inputs(self):
        try:
            with open(self.get_input_details_json_path()) as f:
                inputs = json.load(f)[JSON_KEYS.INPUTS]
                assert inputs is not None
                return [i for i in inputs if i is not None]

        except (KeyError, AssertionError) as e:
            LOGGER.error(
                f"{INPUT_CONFIG_JSON_NAME} doesn't contain the key 'inputs', stopping execution.",
                exc_info=True,
            )
        except (FileNotFoundError, PermissionError) as e:
            LOGGER.error(
                f"{INPUT_CONFIG_JSON_NAME} doesn't exist in provided input dir, stopping execution.",
                exc_info=True,
            )
        raise e


class OutputsManager:
    def __init__(
        self,
        output_dir: Path,
        input_loader: InputsLoader,
        no_copy: bool,
        gen_csv: bool,
        show_plot: bool,
        name_suffix: str,
    ):
        self.no_input_copy = no_copy
        self.gen_csv = gen_csv
        self.show_plot = show_plot
        self._dash_html_exporter = None

        self.output_parent_dir_path = output_dir
        self.input_loader = input_loader
        self.output_dir_path = None
        self.rand_key = None
        self.name_suffix = name_suffix

        if not output_dir.is_dir():
            LOGGER.error(f"{output_dir=} doesn't exist, stopping execution.")
            raise ValueError()

        self._create_output_dir()

    def _create_output_dir(self):
        # prep metadata for output dir
        input_path = self.input_loader.get_input_details_json_path()
        with open(input_path) as f:
            input_details = json.load(f)
            rand_key = random.choice(NAMES_SALT)

        # create output dir
        self.rand_key = self.rand_key or rand_key
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.name_suffix = "." + self.name_suffix if self.name_suffix else ""
        dirname = f"{timestamp}_{self.rand_key}{self.name_suffix}"
        self.output_dir_path = Path(self.output_parent_dir_path, dirname).resolve()
        Path(self.output_dir_path).mkdir()

        if self.no_input_copy:
            # save metadata about input in output dir
            input_details[JSON_KEYS.INPUT_DIR_PATH] = (
                input_path.as_uri()
                if platform.system().lower() == "windows"
                else input_path.as_posix()
            )
            with open(self.get_output_metadata_json_path(), "w") as f:
                json.dump(input_details, f, indent=True)
        else:
            # requested, copy the input data into the output dir
            inputs = Path(self.input_loader.input_dir).glob("*.*")
            inputs_dest_dir = Path(self.output_dir_path, JSON_KEYS.INPUTS)
            Path(inputs_dest_dir).mkdir()

            for file in inputs:
                if Path(file).is_file():
                    shutil.copy2(file, inputs_dest_dir)

    def get_output_metadata_json_path(self):
        return Path(self.output_dir_path, OUTPUT_SUMMARY_JSON_NAME).resolve()

    def get_output_full_path(self, filename):
        return Path(self.output_dir_path, filename).resolve()

    def delete_all_other_outputs(self):
        for d in Path(self.output_parent_dir_path).iterdir():
            if d in self.output_dir_path:
                continue  # don't delete my new output
            shutil.rmtree(Path(self.output_parent_dir_path, d))


class GenDetailsFileScript:
    SCRIPT_NAME = "detail.json generator"
    description=f"""
        \nExamples:
        \tpython {Path(__file__).name} -i data/some_dir_with_subs --sub-dirs  # create details.json for each dir in given input
        \tpython {Path(__file__).name} -i data/some_dir_with_subs --join-out-to data/all_h5s  # copy all h5 and join details to output dir (no gen)
    """

    def parseArgs(self):
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

        parser = ArgumentParser(
            prog=self.SCRIPT_NAME,
            formatter_class=ArgumentDefaultsHelpFormatter,
            description="tries to generate details.json according to filenames",
        )
        # fmt: off
        parser.add_argument("-i", "--input",
            required=True,
            help="path of the inputs dir",
        )
        parser.add_argument("-d", "--dry",
            default=False, action="store_true",
            help="if to print the result instead of saving to file",
        )
        parser.add_argument("--sub-dirs",
            default=False, action="store_true",
            help="gen json for each dir in input dir",
        )

        parser.add_argument("--join-out-to",
            help="output dir. if given, *no details gen will happen*, and all " \
            "input dir existing h5 will be copied, and all the details json will be merged to one",
        )
        # fmt: on
        return parser.parse_args()

    @staticmethod
    def build_file_data(file: Path, substance: str, concentration: int, unit: str):
        try:
            concentration = int(concentration)
        except ValueError: pass # allow con with unit

        return {
            JSON_KEYS.FILENAME: file.name,
            JSON_KEYS.SUBSTANCE: substance,
            JSON_KEYS.CONCENTRATION: {
                JSON_KEYS.CONCENTRATION_VALUE: concentration,
                JSON_KEYS.CONCENTRATION_UNIT: unit,
            },
            JSON_KEYS.FRAMERATE: 20,
        }

    def gen_file_data(self, file: Path):
        try:
            # try crude parse
            parts = self.filename.removeprefix("labels.xenia").removesuffix(".analysis.h5")
            parts = parts.split('_')[5:]
            exp_num, exp_well, substance, con = parts[:4]
            better_con =  re.search(r'(\d+)([a-zA-Z]+)', con)
            if better_con:
                con, unit = better_con.groups()
                return self.build_file_data(file, substance, concentration=con, unit=unit)

            return self.build_file_data(file, substance, concentration=con, unit="")
        except: pass

        regex = r"([a-zA-Z]+)_(\d+)([a-zA-Z]+)\.analysis\.h5$"
        match = re.search(regex, file.name)
        if match:
            substance, concentration, unit = match.groups()
            return self.build_file_data(file, substance, concentration, unit)

        LOGGER.warning(
            f"cannot generate entry from data for {file.name=}, generating stab"
        )
        return self.build_file_data(
            file, substance="sub-holder", concentration="-1", unit="uni-holder"
        )

    def generate_details_json(self, input_dir: Path):
        return {
            JSON_KEYS.INPUTS: [
                self.gen_file_data(f)
                for f in input_dir.iterdir()
                if f.name != INPUT_CONFIG_JSON_NAME
            ]
        }
    def _cmd_gen_single(self, input_dir:Path, dry:bool):
        result = self.generate_details_json(input_dir)
        if dry:
            from pprint import pprint
            pprint(result)
        else:
            with open(input_dir.joinpath(INPUT_CONFIG_JSON_NAME), "w") as f:
                json.dump(result, f, indent=True)

    def _cmd_gen_dir(self, input_dir:Path, dry:bool=False):
        # for [f for f in output_dir.iterdir() if f.is_dir() and name_filter in f.name]
        for dir in input_dir.iterdir():
            self._cmd_gen_single(input_dir=dir, dry=dry)

    def _cmd_join_out_to(self, input_dir:Path, output_dir:Path):
        output_dir.mkdir()
        inputs_details = []
        for in_dir in input_dir.iterdir():
            with open(in_dir.joinpath(INPUT_CONFIG_JSON_NAME)) as f:
                inputs_details.extend(json.load(f)[JSON_KEYS.INPUTS])

            for in_file in in_dir.iterdir():
                if in_file.name.endswith('json'): continue  # skip

                if in_file.is_file():
                    shutil.copy2(in_file, output_dir)

        with open(output_dir.joinpath(INPUT_CONFIG_JSON_NAME), "w") as f:
            d = { JSON_KEYS.INPUTS : inputs_details}
            json.dump(d,f,indent=True)


    def main(self):
        args = self.parseArgs()
        LOGGER.info(f"starting execution of {self.SCRIPT_NAME} with {args=}")

        input_dir = Path(args.input)
        if not input_dir.is_dir():
            return print("please provide a path to a dir")

        # execute command
        if args.join_out_to:
            self._cmd_join_out_to(input_dir, output_dir=Path(args.join_out_to))
        elif args.sub_dirs:
            self._cmd_gen_dir(input_dir)
        else:
            self._cmd_gen_single(input_dir, args.dry)

        LOGGER.info(f"done execution of {self.SCRIPT_NAME}")


if __name__ == "__main__":
    GenDetailsFileScript().main()
