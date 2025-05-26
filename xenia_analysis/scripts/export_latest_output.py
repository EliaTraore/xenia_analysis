import zipfile
import os.path
from pathlib import Path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def export_latest(output_dir: Path, name_suffix: str, name_filter: str):
    print(f"Exporting source and dest: {output_dir}")

    paths = [f for f in output_dir.iterdir() if f.is_dir() and name_filter in f.name]
    latest = max(paths, key=os.path.getctime)
    print(f"Exporting dir: {latest.name}")

    name_suffix = "." + name_suffix.replace(' ', '-') if len(name_suffix)>0 else ""
    name = f"{latest.name}{name_suffix}.zip"
    zip_path = output_dir.joinpath(name)

    with zipfile.ZipFile(zip_path, mode="w") as out:
        for f in latest.iterdir():
            if f.name.endswith("json"):
                continue  # don't export metadata
            out.write(f, arcname=f.name)

    print(f"done creating {zip_path=}")


def parseArgs():
    parser = ArgumentParser(
        prog="Export Latest",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output",
        default=Path(__file__, "..", "..", "..", "outputs").resolve(),
        help="dir to save the output under",
    )
    parser.add_argument(
        "-n",
        "--name-suffix",
        default="",
        help="a suffix to add to the output zip name"
    )

    parser.add_argument(
        "-f",
        "--name-filter",
        default="",
        help="a filter of the dirs to look at at the output - look for dirs with this string in name"
    )
    return parser.parse_args()


def main():
    args = parseArgs()
    output_dir = Path(args.output)

    if not output_dir.is_dir():
        print("please provide a path to a directory")
        print(f"{output_dir} isn't.")
        return

    export_latest(output_dir, args.name_suffix, args.name_filter)


if __name__ == "__main__":
    main()
