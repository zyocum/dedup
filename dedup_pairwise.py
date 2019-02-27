#!/usr/bin/env python3

"""Naively search for duplicate text files based on string similarity."""

import difflib
from math import factorial
from itertools import combinations

from tqdm import tqdm

tqdm.monitor_interval = 0

def combos(n, k=2):
    """Compute n choose k"""
    return int(factorial(n) / (factorial(k) * factorial(n - k)))

def diff(s1, s2):
    """Compute the difference betweeen two strings normalized by the length
    of the longest of the two strings"""
    longest = max((s1, s2), key=len)
    return sum(d[0] != ' ' for d in difflib.ndiff(s1, s2)) / len(longest)

class Text(object):
    """A class modeling a text document."""
    def __init__(
        self,
        filename,
        threshold=0.25
    ):
        self.filename = filename
        self.threshold = threshold
        self.data = self.load()
    
    def load(self):
        with open(self.filename, mode='r') as f:
            data = f.read()
            self.size = len(data)
            return data
    
    def __hash__(self):
        return hash(self.filename)
    
    def __eq__(self, other):
        return diff(self.data, other.data) <= self.threshold
    
    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self.filename}, threshold={self.threshold})'
        )

def document_sorter(document):
    """A sorting key function that sorts documents by length (descending)
    and filename (ascending)"""
    return -document.size, document.filename

def find_duplicates(documents):
    """Naively search all pair-wise combinations of a collection of strings
    for duplicates.
    
    The return value is a dict whose keys are strings and whose values are
    sets of strings are duplicates of the key string according to the given
    similarity threshold."""
    deduped = set()
    duplicates = {}
    for pair in tqdm(
        iterable=combinations(documents, 2),
        total=combos(len(documents), 2),
        unit='pairs',
        dynamic_ncols=True
    ):
        a, b = sorted(pair, key=document_sorter)
        if (a, b) not in deduped and (a == b):
            deduped.add((a, b))
            if a not in duplicates:
                duplicates[a] = {b}
            else:
                duplicates[a].add(b)
    return duplicates

def main(filenames, threshold=0.25):
    documents = []
    for filename in tqdm(
        filenames,
        unit='files',
        dynamic_ncols=True
    ):
        documents.append(Text(filename, threshold=threshold))
    dupe_sets = find_duplicates(documents)
    for uniuqe, duplicates in dupe_sets.items():
        for duplicate in duplicates:
            print('\t'.join((unique, duplicate)))
    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'filenames',
        type=argparse.FileType('r'),
        help=(
            'file listing a set of filenames to check for duplicates; '
            'one filename per line (use "-" to read filenames as lines from '
            'stdin)'
        )
    )
    parser.add_argument(
        '-r', '--threshold',
        type=float,
        default=0.25,
        help=(
            'threshold for considering two strings equivalent (lower thresholds '
            'are more strict; higher thresholds are more lenient)'
        )
    )
    args = parser.parse_args()
    filenames = args.filenames.read().splitlines()
    if args.filenames.name != '<stdin>':
        args.filenames.close()
    main(filenames, threshold=args.threshold)
