import pandas
import numpy
import scipy
import h5py

import argparse


def parseArgs():
    parser = argparse.ArgumentParser(
        prog='Xenia analysis',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', help='path of the input dir with details.json')
    parser.add_argument('-nc', '--no-copy', default=False, action='store_true', help="don't copy the input dir to the output dir")
    parser.add_argument('-s', '--show', default=False, action='store_true', help='if to show the generated plots' )
    return parser.parse_args()


def main():
    args = parseArgs()
    print(f'{args=}')
    print(f'{args.input=}')
    print(f'{args.no_copy=}')
    print(f'{args.show=}')

if __name__ == '__main__':
    main()
