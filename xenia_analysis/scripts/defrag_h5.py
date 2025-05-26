from pathlib import Path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import h5py
import numpy as np


def ifprint(show, *args, **kwargs):
    if not show:
        return
    print(*args, **kwargs)


def iterpairs(show=False):
    pairs = [
        [
            "labels.xenia_06.04.25_tubocurarine.001_20250227_154456168_2_A24B4_tubocurarine_1mM_after_tubocurarine.analysis.h5",
            "labels.xenia_06.04.25_tubocurarine.000_20250227_154456168_2_A24B4_tubocurarine.000_1mM_original_ctrl.analysis.h5",
        ],
        [
            "labels.xenia_06.04.25_tubocurarine.002_20250227_154458160_1_A22A2_tubocurarine_1mM_aftertubocurarine_V2.analysis.h5",
            "labels.xenia_06.04.25_tubocurarine.003_20250227_154458160_1_A22A2_tubocurarine_1mM_ctrl_V2.analysis.h5",
        ],
        [
            "labels.xenia_06.04.25_tubocurarine.004_20250227_162325154_3_A24A3_tubocurarine_1mM_aftertubocurarine.analysis.h5",
            "labels.xenia_06.04.25_tubocurarine.005_20250227_162325154_3_A24A3_tubocurarine_1mM_ctrl.analysis.h5",
        ],
        [
            "labels.xenia_06.04.25_tubocurarine.007_20250227_165735817_5_A24A2(again)_tubocurarine_1mM_ctrl.analysis.h5",
            "labels.xenia_06.04.25_tubocurarine.008_20250227_165735817_5_A24A2(again)_tubocurarine_1mM_tubocurarine.analysis.h5",
        ],
        [
            "labels.xenia_06.04.25_tubocurarine.006_20250227_162327153_4_A22A1_tubocurarine_1mM_aftertubocurarine.analysis.h5",
            "labels.xenia_06.04.25_tubocurarine.009_20250227_162327153_4_A22A1_tubocurarine_1mM_ctrl_corrected.analysis.h5",
        ],
    ]

    for pair in pairs:
        ifprint(show, "looking at ", hash(tuple(pair)))
        ctrl = [f for f in pair if "ctrl" in f][0]
        after = [f for f in pair if f != ctrl][0]
        if ctrl == after:
            ifprint(show, "Error! cannot distinguish this pair:")
        ifprint(show, f"got {ctrl=}")
        ifprint(show, f"got {after=}")
        yield ctrl, after


def numpy_sandbox():
    def create_shard(c):
        r = np.ndarray(shape=(1,2,9,5))
        # r = np.ndarray(shape=(1,2,9))
        return r*c/r
    a = create_shard(2)
    b = create_shard(-3)
    c = np.concatenate([a,b], axis=len(a.shape)-1) #concat on the data, last axis

    print("a")
    print(a)
    print("b")
    print(b)
    print("c")
    print(c) # concat-ed correctly

class DefragH5Script:
    SCRIPT_NAME = "h5 xenia defrag"

    TRACKS = "tracks"
    NODES = "node_names"

    COPY_KEYS = [
        "edge_inds",
        "edge_names",
        "node_names",
        "track_names",
        # shape=():
        "labels_path",
        "provenance",
        "video_ind",
        "video_path",
    ]
    JOIN_KEYS = [
        "instance_scores",
        "point_scores",
        # "track_occupancy", shape=(1934, 1), doesnt fit my join structure and isn't used later so I'm skipping copying it
        "tracking_scores",
        "tracks",
    ]
    def __init__(self, show=False):
        self.show = show

    def join_files(self, input_dir: Path, ctrl: str, after: str):
        output_dir = Path(input_dir.parent, f"{input_dir.name}_defraged")
        outfile = ctrl.replace("ctrl", "merged")
        try:
            output_dir.mkdir()
        except FileExistsError:
            ifprint(self.show, f"{output_dir=} exists, assuming i'll override files")

        with (
            h5py.File(input_dir.joinpath(ctrl), "r") as fctrl,
            h5py.File(input_dir.joinpath(after), "r") as fafter,
            h5py.File(output_dir.joinpath(outfile), "w") as fout,
        ):
            for name, f in {"ctrl": fctrl, "after": fafter}.items():
                print(f"file name: {name}")
                [print(f"{k=}: {f[k].shape=} {type(f[k])=}") for k in f.keys()]

            for key in self.COPY_KEYS:
                fout.create_dataset(key, data=fctrl[key])

            for key in self.JOIN_KEYS:
                print(f"joining {key=}")
                axis = len(fctrl[key].shape) - 1
                data = np.concatenate([fctrl[key], fafter[key]], axis=axis)
                fout.create_dataset(key, data=data)
                print(f"sanity: {key}: {fctrl[key].shape=} {fafter[key].shape=} {fout[key].shape=}")

            print(f"finished with {outfile=} in {output_dir=}")
            fout.flush()

    def defrag(self, input_dir: Path):
        for ctrl, after in iterpairs():
            self.join_files(input_dir, ctrl, after)
            print("+" * 80)

    def parseArgs(self):
        parser = ArgumentParser(
            prog=self.SCRIPT_NAME,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        # fmt: off
        parser.add_argument("-i", "--input",
            required=True,
            help="path of the inputs dir",
        )
        # fmt: on
        return parser.parse_args()

    def main(self):
        args = self.parseArgs()
        print(f"starting execution of {self.SCRIPT_NAME} with {args=}")
        print("+" * 100)

        dir = Path(args.input)
        if not dir.is_dir():
            return print("please provide a path to a dir")

        self.defrag(dir)

        print("+" * 100)
        print(f"done execution of {self.SCRIPT_NAME}")


if __name__ == "__main__":
    # DefragH5Script().main()
    DefragH5Script(show=True).main()
    # numpy_sandbox()
