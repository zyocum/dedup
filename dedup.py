#!/usr/bin/env python3

import csv
import sys
import json

from math import inf
from operator import itemgetter
from unicodedata import normalize
from itertools import combinations

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

class Text(object):
    """A class modeling a text document that can be compared for equality
    to other Text instances using simhash (a locality sensitive hash or 
    LSH) based on character n-grams.
    
    """
    def __init__(
        self,
        filename,
        n=2,
        hashf=CityHash128,
        normalization_form=None
    ):
        self.filename = filename
        self.n = n
        self.hashf = hashf
        self.normalization_form = normalization_form
        self.lsh = simhash(self.load(), n=self.n, hashf=self.hashf)
    
    def load(self):
        with open(self.filename, mode='r') as f:
            data = f.read()
            if self.normalization_form:
                data = normalize(self.normalization_form, data)
            self.size = len(data)
            return data
    
    def __hash__(self):
        return hash(self.filename)
    
    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self.filename!r}, n={self.n}, hashf={self.hashf.__name__})'
        )

class ADM(Text):
    """A class modeling a Basis Technology Annotatded Data Model (ADM)
    that can be compared for equality to other Text instances using simhash
    based on character n-grams."""
    def load(self):
        with open(self.filename, mode='r') as f:
            obj = json.loads(f.read())
            data = obj['data']
            self.size = len(data)
            return data

def document_sorter(document):
    """A sorting key function that sorts documents by length (descending)
    and filename (ascending)
    
    """
    return -document.size, document.filename

def simdiff(a, b, bits=128):
    """Compute the bitwise difference between two simhashes"""
    if bits < 1:
        raise ValueError(f'bits must be >= 1 (bits={bits})')
    xor = a ^ b
    difference = sum(((xor & (1 << i)) > 0) for i in range(bits))
    return difference

def pairs(documents, hashf=CityHash128, window=2):
    """Generate duplicate candidate pairs and their minimum bitwise difference
    scores.
    
    The return type is ((a, b), c) where:
    
        a: a document instance that has a .lsh attribute
        b: a document instance that has a .lsh attribute
        c: the minimum difference score between all rotations of the LSHs of
           a and b
    """
    d = {}
    bits = HASHSIZE[hashf]
    for i in range(bits):
        def lsh(document):
            return rotate(document.lsh, i, width=bits)
        for ng in ngrams(
            sorted(documents, key=lsh),
            n=window
        ):
            for a, b in combinations(ng, 2):
                a, b = sorted((a, b), key=document_sorter)
                d[(a, b)] = simdiff(lsh(a), lsh(b), bits=bits)
    yield from sorted(d.items(), key=itemgetter(1))

def load(
    filenames,
    doctype=Text,
    n=2,
    hashf=CityHash128,
    normalization_form=None
):
    """Generate doctype instances per filename with a progress bar"""
    with tqdm(
        filenames,
        unit='files',
        dynamic_ncols=True
    ) as progress:
        for filename in progress:
            yield doctype(
                filename,
                n=n,
                hashf=hashf,
                normalization_form=normalization_form
            )

DOCTYPES = {
    '.txt': Text,
    '.adm.json': ADM
}

def main(
    filenames,
    doctype=Text,
    n=2,
    hashf=CityHash128,
    normalization_form=None,
    threshold=inf,
    window=10
):
    documents = load(
        filenames,
        doctype=doctype,
        n=n,
        hashf=hashf,
        normalization_form=normalization_form
    )
    writer = csv.writer(sys.stdout, dialect=csv.excel_tab)
    for (a, b), score in pairs(documents, hashf=hashf, window=window):
        if score <= threshold:
            writer.writerow((a.filename, b.filename, score))

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
        default=128,
        choices=sorted(HASHES),
        help='hash size (in bits)'
    )
    parser.add_argument(
        '-r',
        '--threshold',
        type=float,
        default=max(HASHES),
        help=(
            'minimum bitwise difference threshold for considering two LSHs '
            'equivalent (lower thresholds are more strict; higher thresholds '
            'are more lenient; thresholds must be between 0 and -b/--bits)'
        )
    )
    parser.add_argument(
        '-f',
        '--normalization-form',
        default='NFKD',
        choices=['NFC', 'NFKC', 'NFD', 'NFKD'],
        help=(
            'Unicode normalization option; refer to unicodedata.normalize for '
            'explanation of options'
        )
    )
    parser.add_argument(
        '-t',
        '--doc-type',
        choices=sorted(DOCTYPES),
        default='.txt',
        help='the type of documents to compare'
    )
    parser.add_argument(
        '-w', '--window',
        type=int,
        default=2,
        help='window size to check for candidates in the sorted list of pairs',
    )
    args = parser.parse_args()
    if not (args.threshold <= args.bits):
        print(
            (
                '[INVALID DIFFERENCE THRESHOLD] '
                f'-r/--threshold={args.threshold} must be '
                f'less than -b/--bits={args.bits}'
            ),
            file=sys.stderr
        )
        sys.exit(1)
    filenames = args.filenames.read().splitlines()
    if args.filenames.name != '<stdin>':
        args.filenames.close()
    main(
        filenames,
        doctype=DOCTYPES[args.doc_type],
        n=args.n_gram_size,
        hashf=HASHES[args.bits],
        normalization_form=args.normalization_form,
        threshold=args.threshold,
        window=args.window
    )
