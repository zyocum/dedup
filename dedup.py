#!/usr/bin/env python3

"""Find duplicate text documents from a list of filenames."""

import sys

from operator import attrgetter

from cityhash import CityHash32, CityHash64, CityHash128
from tqdm import tqdm

tqdm.monitor_interval = 0

HASHSIZE = {
    CityHash32: 32,
    CityHash64: 64,
    CityHash128: 128,
}

HASHES = {bits: hashf for (hashf, bits) in HASHSIZE.items()}

def ngrams(iterable, n=1):
    """Generate ngrams from an iterable
    
    l = range(5)
    list(l) -> [0, 1, 2, 3, 4, 5]
    list(ngrams(l, n=1)) -> [(0,), (1,), (2,), (3,), (4,)]
    list(ngrams(l, n=2)) -> [(0, 1), (1, 2), (2, 3), (3, 4)]
    list(ngrams(l, n=3)) -> [(0, 1, 2), (1, 2, 3), (2, 3, 4)]
    
    """
    return zip(*(iterable[i:] for i in range(n)))

def rotate(n, rotations=1, width=32):
    """Bitwise rotate an int.
    
    bin(rotate(1, rotations=0))  ->                                '0b1'
    bin(rotate(1, rotations=1))  -> '0b10000000000000000000000000000000'
    bin(rotate(1, rotations=2))  ->  '0b1000000000000000000000000000000'
    bin(rotate(1, rotations=32)) ->                                '0b1'
    bin(rotate(1, rotations=31)) ->                               '0b10'
    bin(rotate(1, rotations=-1)) ->                               '0b10'
    bin(rotate(1, rotations=1, width=8)) ->                 '0b10000000'
    bin(rotate(1, rotations=8, width=8)) ->                        '0b1'
    
    """
    width = max(n.bit_length(), width)
    rotations %= width
    if rotations < 1:
        return n
    mask = 2 ** width - 1
    n &= mask
    return (n >> rotations) | ((n << (width - rotations) & mask))

def simhash(text, n=2, hashf=CityHash32):
    """Simhash implementation using an underlying, fast string-hash: cityhash"""
    lsh = [0] * HASHSIZE[hashf]
    if not text:
        return 0
    for ngram in ngrams(text, n=n):
        hash_ = hashf(''.join(ngram))
        for i, _ in enumerate(lsh):
            if hash_ & (1 << i):
                lsh[i] += 1
            else:
                lsh[i] -= 1
    return sum(int(b > 0) << i for (i, b) in enumerate(reversed(lsh)))

def simdiff(a, b, bits=32):
    """Compute the bitwise difference between two simhashes normalized
    by the length of the longest hash in bits"""
    if bits < 1:
        raise ValueError(f'bits must be >= 1 (bits={bits})')
    xor = a ^ b
    difference = sum(((xor & (1 << i)) > 0) for i in range(bits))
    return difference / bits

class Text(object):
    """A class modeling a text document that can be compared for equality
    to other Text instances using simhash (a locality sensitive hash or 
    LSH) based on character n-grams.
    
    """
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
        self.lsh = simhash(self.load(), n=self.n, hashf=self.hashf)
    
    def load(self):
        with open(self.filename, mode='r') as f:
            data = f.read()
            self.size = len(data)
            return data
    
    def __hash__(self):
        return hash(self.filename)
    
    def __eq__(self, other):
        diff = simdiff(self.lsh, other.lsh, bits=HASHSIZE[self.hashf])
        return diff < self.threshold
    
    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self.filename}, n={self.n}, hashf={self.hashf.__name__}'
            f'threshold={self.threshold})'
        )

def document_sorter(document):
    """A sorting key function that sorts documents by length (descending)
    and filename (ascending)
    
    """
    return -document.size, document.filename

def find_duplicates(
    documents,
    n=2,
    hashf=CityHash32,
    show_dupes=False
):
    """Find duplicate document sets from a collection of documents.
    
    The return value is a dict whose keys are documents and whose values are
    sets of documents that are duplicates of the key document according to the
    given document LSH similarity threshold.
    
    A document must implement __eq__ such that two documents are equivalent
    if the similarity of their .lsh attributes is within the specified
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
            if (a, b) not in deduped and (a == b):
                if show_dupes:
                    print(a.filename, ':', a.load(), file=sys.stderr)
                    print(b.filename, ':', b.load(), file=sys.stderr)
                    print('{:0>128b}'.format(a.lsh), file=sys.stderr)
                    print('{:0>128b}'.format(b.lsh), file=sys.stderr)
                    print(
                        simdiff(a.lsh, b.lsh, bits=HASHSIZE[hashf]),
                        file=sys.stderr
                    )
                deduped.add((a, b))
                if a not in duplicates:
                    duplicates[a] = {b}
                else:
                    duplicates[a].add(b)
        for document in documents:
            document.lsh = rotate(document.lsh, width=HASHSIZE[hashf])
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
    To report the number of duplicates found to stderr, set verbose=True.
    
    """
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
        hashf=hashf,
        show_dupes=verbose
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
        '-b',
        '--bits',
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
            'threshold for considering two LSHs equivalent (lower thresholds '
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
        hashf=HASHES[args.bits],
        threshold=args.threshold,
        verbose=args.verbose
    )
