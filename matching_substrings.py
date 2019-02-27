#!/usr/bin/env python3

"""Read pairs of files from stdin and report matching substrings across the
files.

Output is TSV with the following fields:

    1.filename
    2.filename
    1.startOffset
    1.endOffset
    2.startOffset
    2.endOffset
    text
    size

or JSON like the following:

{
    "1.filename": "/path/to/1.txt",
    "2.filename": "/path/to/2.txt",
    "1.startOffset": 0,
    "1.endOffset": 4,
    "2.startOffset": 10,
    "2.endOffset": 14,
    "text": "the",
    "size": 3
}
"""

import csv
import sys
import json

from itertools import islice
from operator import attrgetter
from difflib import SequenceMatcher

FIELDS = [
    '1.filename',
    '2.filename',
    '1.startOffset',
    '1.endOffset',
    '2.startOffset',
    '2.endOffset',
    'text',
    'size',
]

def matching_substrings(
    s1,
    s2,
    threshold=5
):
    """Generate substring matches from a pair of strings where the length
    of the substrings satisfies a minimum length threshold.  The matches
    are also sorted by length in descending order."""
    matcher = SequenceMatcher(None, s1, s2)
    yield from sorted(
        (m for m in matcher.get_matching_blocks() if m.size >= threshold),
        key=attrgetter('size'),
        reverse=True
    )

def main(
    f,
    threshold=5,
    n=None,
    jsonl=False
):
    """Print a report of matching substrings to stdout as TSV or JSON lines.
    f: a file with pairs of filenames to check for substring matches (one pair
       per line)
    threshold: the minimum substring match length to report
    n: how  many substrings to report per pair of files
    """
    reader = csv.reader(f, dialect=csv.excel_tab)
    if not jsonl:
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=FIELDS,
            dialect=csv.excel_tab
        )
        writer.writeheader()
    for record in reader:
        filename1, filename2 = record
        with open(filename1, mode='r') as f1, open(filename2, mode='r') as f2:
            s1 = f1.read()
            s2 = f2.read()
        matches = matching_substrings(
            s1,
            s2,
            threshold=threshold
        )
        for match in islice(matches, n):
            start1 = match.a
            end1 = match.a + match.size
            start2 = match.b
            end2 = match.b + match.size
            d = {
                '1.filename': filename1,
                '2.filename': filename2,
                '1.startOffset': start1,
                '1.endOffset': end1,
                '2.startOffset': start2,
                '2.endOffset': end2,
                'text': s1[start1:end1],
                'size': match.size
            }
            if jsonl:
                print(json.dumps(d, ensure_ascii=False))
            else:
                writer.writerow(d)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'input',
        type=argparse.FileType('r'),
        help='input file (use "-" to read from stdin)'
    )
    parser.add_argument(
        '-r', '--threshold',
        type=int,
        default=5,
        help='minimum matching substring length to report'
    )
    parser.add_argument(
        '-n', '--matches',
        type=int,
        default=None,
        help=(
            'number of substring matches to report per file pair '
            '(default is to report all substring matches)'
        )
    )
    parser.add_argument(
        '-j', '--json',
        default=False,
        action='store_true',
        help='output as JSON lines (default is TSV)'
    )
    args = parser.parse_args()
    main(
        args.input,
        threshold=args.threshold,
        n=args.matches,
        jsonl=args.json
    )
    if args.input.name != '<stdin>':
        args.input.close()
