#!/usr/bin/env python3

'''Produce a TSV of equivalence classes given a TSV of duplicates produced by dedup.py.'''

import csv
import sys

def main(filename, threshold, display_first_marker):

    with open(filename, mode='r') as f:

        equivalents = {}
        for documents in filter_rows(csv.reader(f, delimiter='\t'), threshold):

            # find equivalence class
            equivalence_class = set()
            if documents[0] in equivalents:
                equivalence_class = equivalents[documents[0]]
            elif documents[1] in equivalents:
                equivalence_class = equivalents[documents[1]]

            # update equivalence class
            equivalence_class.add(documents[0])
            equivalence_class.add(documents[1])
            equivalents[documents[0]] = equivalence_class
            equivalents[documents[1]] = equivalence_class

    frozen_equivalents = set()
    for equivalence_class in equivalents.values():
        frozen_equivalents.add(frozenset(equivalence_class))

    writer = csv.writer(sys.stdout, dialect=csv.excel_tab)
    for i, equivalence_class in enumerate(frozen_equivalents):
        for j, document in enumerate(equivalence_class):

            row = (i, document)
            if display_first_marker:
                marker = '' if j > 0 else '*'
                row = (marker, i, document)

            writer.writerow(row)

def filter_rows(rows, threshold):
   yield from ((a, b) for (a, b, bitwise_difference) in rows if int(bitwise_difference) <= threshold)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'input',
        help='path to duplicates TSV file'
    )
    parser.add_argument(
        '-t',
        '--threshold',
        type=int,
        default=0,
        help='minimum bitwise difference threshold for considering two LSHs equivalent'
    )
    parser.add_argument(
        '-d',
        '--display-first-marker',
        action='store_true',
        help='mark the first entry in each equivalence class with an asterisk in the first column'
    )
    args = parser.parse_args()
    main(args.input, args.threshold, args.display_first_marker)
