# Dedup

A Python script for finding duplicate text files.

## Install
```
$ python3 -m venv .
$ source bin/activate
(dedup) $ pip install -r requirements.txt
```

## Usage

`dedup.py` can find candidate duplicate pairs in a way that avoids searching the full set of pair-wise combinations:

```
(dedup) $ ./dedup.py -h
usage: dedup.py [-h] [-n N_GRAM_SIZE] [-b {32,64,128}] [-r THRESHOLD]
                [-f {NFC,NFKC,NFD,NFKD}] [-t {.adm.json,.txt}] [-w WINDOW]
                filenames

positional arguments:
  filenames             file listing a set of filenames to check for
                        duplicates; one filename per line (use "-" to read
                        filenames as lines from stdin)

optional arguments:
  -h, --help            show this help message and exit
  -n N_GRAM_SIZE, --n-gram-size N_GRAM_SIZE
                        size of character n-grams (default: 2)
  -b {32,64,128}, --bits {32,64,128}
                        hash size (in bits) (default: 128)
  -r THRESHOLD, --threshold THRESHOLD
                        minimum bitwise difference threshold for considering
                        two LSHs equivalent (lower thresholds are more strict;
                        higher thresholds are more lenient; thresholds must be
                        between 0 and -b/--bits) (default: 128)
  -f {NFC,NFKC,NFD,NFKD}, --normalization-form {NFC,NFKC,NFD,NFKD}
                        Unicode normalization option; refer to
                        unicodedata.normalize for explanation of options
                        (default: NFKD)
  -t {.adm.json,.txt}, --doc-type {.adm.json,.txt}
                        the type of documents to compare (default: .txt)
  -w WINDOW, --window WINDOW
                        window size to check for candidates in the sorted list
                        of pairs (default: 2)
(dedup) $ find test -name "*.txt" | sort | xargs head
==> test/1.txt <==
the cat sat in the hat

==> test/2.txt <==
the cat sat on the mat

==> test/3.txt <==
we all scream for ice scream

==> test/4.txt <==
we all scream for ice cream

==> test/5.txt <==
we all like ice scream

==> test/6.txt <==
abcdefg

==> test/7.txt <==
abcdefg
hijklmnop
(dedup) $ find test -name '*.txt' | ./dedup.py -
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 1489.30files/s]
test/1.txt	test/2.txt	17
test/3.txt	test/6.txt	55
test/3.txt	test/7.txt	56
test/4.txt	test/6.txt	56
test/2.txt	test/5.txt	58
test/5.txt	test/7.txt	61
(dedup) $ find test -name '*.txt' | ./dedup.py - -b 64 -r 64
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 2830.44files/s]
test/3.txt	test/4.txt	4
test/1.txt	test/2.txt	7
test/7.txt	test/6.txt	12
test/4.txt	test/5.txt	14
test/3.txt	test/2.txt	29
test/1.txt	test/6.txt	32
(dedup) $ find test -name '*.txt' | ./dedup.py - -b 32 -r 32
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 4707.41files/s]
test/3.txt	test/4.txt	3
test/3.txt	test/5.txt	5
test/1.txt	test/2.txt	6
test/4.txt	test/6.txt	13
test/5.txt	test/7.txt	13
test/1.txt	test/6.txt	15
```

If you have a list of filename pairs (such as the output from `dedup.py`), then `matching_substrings.py` can be used to inspect the substrings that match between the candidate files:

```
(dedup) $ ./matching_substrings.py -h
usage: matching_substrings.py [-h] [-r THRESHOLD] [-n MATCHES] [-j] input

Read pairs of files from stdin and report matching substrings across the
files. Output is TSV with the following fields: 1.filename 2.filename
1.startOffset 1.endOffset 2.startOffset 2.endOffset text size or JSON like the
following: { "1.filename": "/path/to/1.txt", "2.filename": "/path/to/2.txt",
"1.startOffset": 0, "1.endOffset": 4, "2.startOffset": 10, "2.endOffset": 14,
"text": "the", "size": 3 }

positional arguments:
  input                 input file (use "-" to read from stdin)

optional arguments:
  -h, --help            show this help message and exit
  -r THRESHOLD, --threshold THRESHOLD
                        minimum matching substring length to report (default:
                        5)
  -n MATCHES, --matches MATCHES
                        number of substring matches to report per file pair
                        (default is to report all substring matches) (default:
                        None)
  -j, --json            output as JSON lines (default is TSV) (default: False)
(dedup) $ find test -name '*.txt' | ./dedup.py - -b 32 -r 32 | cut -f 1,2 | ./matching_substrings.py - -j | jq .
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 4758.53files/s]
{
  "1.filename": "test/3.txt",
  "2.filename": "test/4.txt",
  "1.startOffset": 0,
  "1.endOffset": 22,
  "2.startOffset": 0,
  "2.endOffset": 22,
  "text": "we all scream for ice ",
  "size": 22
}
{
  "1.filename": "test/3.txt",
  "2.filename": "test/4.txt",
  "1.startOffset": 23,
  "1.endOffset": 29,
  "2.startOffset": 22,
  "2.endOffset": 28,
  "text": "cream\n",
  "size": 6
}
{
  "1.filename": "test/3.txt",
  "2.filename": "test/5.txt",
  "1.startOffset": 17,
  "1.endOffset": 29,
  "2.startOffset": 11,
  "2.endOffset": 23,
  "text": " ice scream\n",
  "size": 12
}
{
  "1.filename": "test/3.txt",
  "2.filename": "test/5.txt",
  "1.startOffset": 0,
  "1.endOffset": 7,
  "2.startOffset": 0,
  "2.endOffset": 7,
  "text": "we all ",
  "size": 7
}
{
  "1.filename": "test/1.txt",
  "2.filename": "test/2.txt",
  "1.startOffset": 0,
  "1.endOffset": 12,
  "2.startOffset": 0,
  "2.endOffset": 12,
  "text": "the cat sat ",
  "size": 12
}
{
  "1.filename": "test/1.txt",
  "2.filename": "test/2.txt",
  "1.startOffset": 13,
  "1.endOffset": 19,
  "2.startOffset": 13,
  "2.endOffset": 19,
  "text": "n the ",
  "size": 6
}
```

## Locality Sensitive Hashing

The script uses locality sensitive hashing (LSH) to compare texts.  LSHs are a kind of hashing function that, unlike normal hashing functions, have the property that the probability of a hash collision is proportional to the similarity of objects hashed.  In this case, the LSH implemented is simhash (described [here](http://matpalm.com/resemblance/simhash/)).

Running `dedup.py` with the `-v/--verbose` option prints the binary values of the computed LSHs and shows the similarity scores:

```
In [1]: from cityhash import CityHash32, CityHash64, CityHash128   

In [2]: from dedup import simhash
# 32 bit LSH
In [3]: '{:0>32b}'.format(simhash('the cat sat in the hat', hashf=CityHash32))
Out[3]: '00001001110100111100101111111010'
# 64 bit LSH
In [4]: '{:0>64b}'.format(simhash('the cat sat in the hat', hashf=CityHash64))
Out[4]: '0011010110100111001010111110011101000010100111001101111110100010'
#128 bit LSH
In [5]: '{:0>128b}'.format(simhash('the cat sat in the hat', hashf=CityHash128))
Out[5]: '00110010010110111010000110100100000111111101100011001010000000100110111000111010010101011001101101011011011000001110001010111001'
```

After computing an LSH for each document, the list of documents are sorted by their LSH and pairs of adjacent LSHs in the list are compared.  If an adjacent pair's LSHs are similar enough (based on a threshold), then the pair is considered a duplicate.  Considering the sorted list of LSHs once is not sufficient however, because if a pair of documents have high bits that differ, but most bits are still the same, they won't be considered, because they will be unlikely to be adjacent in the sorted list.  To mitigate this, each LSH is rotated and the lists of LSHs are sorted again, and again adjacent pairs are checked.

This strategy requires a pass over each of N documents to compute the LSHs, but once the LSHs are computed, it requires only N-1 * M comparisons where M is size of the LSH in bits.  When N is much larger than M, this is a significant improvement in time complexity over the naive approach of comparing N documents pairwise, which would require N choose 2 or N! / 2! * (N - 2)! comparisons.

If we have, say, over 100k documents to compare, performing N choose 2 comparisons becomes very expensive:

```
# ~241 hours is a long time
(dedup) $ find ~/Desktop/words -type f | ./dedup_pairwise.py - > ~/Desktop/duplicates_pairwise.tsv
100%|███████████████████████████████████████████████████████████████████████████████████████████| 128959/128959 [00:20<00:00, 6251.87files/s]
  0%|                                                                                  | 1272202/8315147361 [01:58<241:35:38, 9559.05pairs/s
```

But, if we use the strategy of rotating the LSHs, we can find duplicates in a reasonable amount of time:

```
# <10 minutes is acceptable
(dedup) $ find ~/Desktop/words -type f | ./dedup.py - -r 12 -b 128 >| ~/Desktop/duplicates.tsv 
100%|███████████████████████████████████████████████████████████████████████████████████████████| 128959/128959 [00:35<00:00, 3623.02files/s]
(dedup) $ wc -l ~/Desktop/duplicates.tsv 
    3841 /Users/zach/Desktop/duplicates.tsv
(dedup) $ head ~/Desktop/duplicates.tsv | while read a b r; do cat "$a"; cat "$b"; echo "-----"; done
karait
rait
-----
bull
dull
-----
mold
told
-----
purveyed
surveyed
-----
salute
lute
-----
blizzard
izzard
-----
blizzard
lizard
-----
aspout
pout
-----
exclaiming
claiming
-----
durant
jurant
-----
```