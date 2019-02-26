#!/usr/bin/env python3

"""Find duplicate text documents from a list of filenames."""

import sys

from collections import deque
from operator import attrgetter

from cityhash import CityHash32, CityHash64, CityHash128
from scipy.spatial.distance import hamming, cosine
from tqdm import tqdm

tqdm.monitor_interval = 0

HASHSIZE = {
    CityHash32: 32,
    CityHash64: 64,
    CityHash128: 128,
}

HASHES = {size: hashf for (hashf, size) in HASHSIZE.items()}

def ngrams(iterable, n=1):
    """Generate ngrams from an iterable
    
    l = range(5)
    list(l) -> [0, 1, 2, 3, 4, 5]
    list(ngrams(l, n=1)) -> [(0,), (1,), (2,), (3,), (4,)]
    list(ngrams(l, n=2)) -> [(0, 1), (1, 2), (2, 3), (3, 4)]
    list(ngrams(l, n=3)) -> [(0, 1, 2), (1, 2, 3), (2, 3, 4)]
    
    """
    return zip(*(iterable[i:] for i in range(n)))

def simhash(text, n=2, hashf=CityHash32):
    """Simhash implementation using an underlying, fast string-hash: cityhash"""
    lsh = [0] * HASHSIZE[hashf]
    if not text:
        return hash_vector
    for ngram in ngrams(text, n=n):
        hash_ = hashf(''.join(ngram))
        for i, _ in enumerate(lsh):
            if hash_ & (1 << i):
                lsh[i] += 1
            else:
                lsh[i] -= 1
    return [int(b > 0) for b in lsh]

class Text(object):
    """A class modeling a text document that can be compared for equality
    to other Text instances using simhash (a locality sensitive hash or 
    LSH) based on character n-grams."""
    def __init__(
        self,
        filename,
        n=2,
        hashf=CityHash32,
        threshold=0.25
    ):
        if 1.0 < threshold < 0.0:
            raise ValueError(
                (
                    f'invalid threshold={threshold}; '
                    'threshold must be in range [0.0..1.0]'
                )
            )
        self.filename = filename
        self.n = n
        self.hashf = hashf
        self.threshold = threshold
        self.lsh = deque(simhash(self.load(), n=self.n, hashf=self.hashf))
    
    def load(self):
        with open(self.filename, mode='r') as f:
            data = f.read()
            self.size = len(data)
            return data
    
    def __hash__(self):
        return hash(self.filename)
    
    def __eq__(self, other):
        return cosine(self.lsh, other.lsh) <= self.threshold
    
    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self.filename}, n={self.n}, hashf={self.hashf.__name__}'
            f'threshold={self.threshold})'
        )

def document_sorter(document):
    return -document.size, document.filename

def find_duplicates(
    documents,
    n=2,
    hashf=CityHash32
):
    """Find duplicate document sets from a collection of documents.
    
    The return value is a dict whose keys are documents and whose values are
    sets of documents that are duplicates of the key document according to the
    given document LSH similarity threshold.
    
    A document must implement __eq__ such that two documents are equivalent
    if the cosine similarity of their .lsh attributes is within the specified
    document similarity threshold.
    """
    duplicates = {}
    deduped = set()
    for _ in tqdm(
        range(HASHSIZE[hashf]),
        unit='rotations',
        dynamic_ncols=True
    ):
        documents = sorted(documents, key=attrgetter('lsh'))
        for pair in ngrams(documents, n=2):
            a, b = sorted(pair, key=document_sorter)
            if a == b:
                if b not in deduped:
                    deduped.add(b)
                    if a not in duplicates:
                        duplicates[a] = {b}
                    else:
                        duplicates[a].add(b)
        for document in documents:
            document.lsh.rotate()
    return duplicates

def main(
    filenames,
    doctype=Text,
    n=2,
    hashf=CityHash32,
    threshold=0.25,
    verbose=False
):
    """Find duplicate documents and report the duplicates found.
    Duplicate document pairs are printed to stdout as TSV.
    To report the number of duplicates found to stderr, set verbose=True."""
    documents = []
    for filename in tqdm(
        filenames,
        unit='files',
        dynamic_ncols=True
    ):
        documents.append(
            doctype(
                filename,
                n=n,
                hashf=hashf,
                threshold=threshold
            )
        )
    dupe_sets = find_duplicates(
        documents,
        n=n,
        hashf=hashf
    )
    for unique, duplicates in dupe_sets.items():
        if verbose:
            print(
                (
                    f'found {len(duplicates)} duplicate(s) of file: '
                    f' {unique.filename}'
                ),
                file=sys.stderr
            )
        for duplicate in duplicates:
            print('\t'.join((unique.filename, duplicate.filename)))
    if verbose:
        total = sum((len(ds) for ds in dupe_sets.values()))
        print(f'found {total} duplicate(s) in total', file=sys.stderr)

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
        '-n',
        '--n-gram-size',
        type=int,
        default=2,
        help='size of character n-grams'
    )
    parser.add_argument(
        '-s',
        '--hash-size',
        type=int,
        default=32,
        choices=sorted(HASHES),
        help='hash size (in bits)'
    )
    parser.add_argument(
        '-r',
        '--threshold',
        type=float,
        default=0.25,
        help=(
            'threshold for how much two documents can differ in their '
            'LSHs before they are not considered duplicates (lower thresholds '
            'are more strict; higher thresholds are more lenient)'
        )
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print duplicate counts to stderr',
    )
    args = parser.parse_args()
    filenames = args.filenames.read().splitlines()
    if args.filenames.name != '<stdin>':
        args.filenames.close()
    main(
        filenames,
        n=args.n_gram_size,
        hashf=HASHES[args.hash_size],
        threshold=args.threshold,
        verbose=args.verbose
    )