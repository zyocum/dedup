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
usage: dedup.py [-h] [-n N_GRAM_SIZE] [-b {32,64,128}] [-r THRESHOLD] [-v]
                filenames

Find duplicate text documents from a list of filenames.

positional arguments:
  filenames             file listing a set of filenames to check for
                        duplicates; one filename per line (use "-" to read
                        filenames as lines from stdin)

optional arguments:
  -h, --help            show this help message and exit
  -n N_GRAM_SIZE, --n-gram-size N_GRAM_SIZE
                        size of character n-grams (default: 2)
  -b {32,64,128}, --bits {32,64,128}
                        hash size (in bits) (default: 32)
  -r THRESHOLD, --threshold THRESHOLD
                        threshold for considering two LSHs equivalent (lower
                        thresholds are more strict; higher thresholds are more
                        lenient) (default: 0.25)
  -v, --verbose         print duplicate counts to stderr (default: False)
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
(dedup) $ find test -name "*.txt" | ./dedup.py -
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 4237.89files/s]
100%|██████████████████████████████████████████████████████████████████████████████████████████████| 32/32 [00:00<00:00, 27514.91rotations/s]
test/1.txt	test/2.txt
test/3.txt	test/4.txt
test/3.txt	test/5.txt
test/4.txt	test/5.txt
test/7.txt	test/6.txt
(dedup) $ find test -name "*.txt" | ./dedup.py - -b 64
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 3132.08files/s]
100%|██████████████████████████████████████████████████████████████████████████████████████████████| 64/64 [00:00<00:00, 19870.86rotations/s]
test/7.txt	test/6.txt
test/1.txt	test/2.txt
test/3.txt	test/4.txt
test/3.txt	test/5.txt
test/4.txt	test/5.txt
(dedup) find test -name "*.txt" | ./dedup.py - -b 128
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 1759.25files/s]
100%|████████████████████████████████████████████████████████████████████████████████████████████| 128/128 [00:00<00:00, 10996.50rotations/s]
test/1.txt	test/2.txt
test/3.txt	test/4.txt
test/7.txt	test/6.txt
(dedup) $ find test -name "*.txt" | ./dedup.py - -r 0.33 -b 128
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 1649.35files/s]
100%|████████████████████████████████████████████████████████████████████████████████████████████| 128/128 [00:00<00:00, 10832.75rotations/s]
test/1.txt	test/2.txt
test/3.txt	test/4.txt
test/3.txt	test/5.txt
test/7.txt	test/6.txt
test/4.txt	test/5.txt
```

If you have a list of filename pairs (such as the output from `dedup.py`), then `matching_substrings.py` can be used to inspect the substrings that match between the candidate files:

```
(dedup) $ ./matching_substrings.py -h
usage: matching_substrings.py [-h] [-r THRESHOLD] [-n MATCHES] [-j] input

Read pairs of files from stdin and report matching substrings across the
files. Ourput is TSV with the following fields: 1.filename 2.filename
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
(dedup) $ ./matching_substrings.py duplicates.tsv -j | jq .
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
  "1.filename": "test/7.txt",
  "2.filename": "test/6.txt",
  "1.startOffset": 0,
  "1.endOffset": 8,
  "2.startOffset": 0,
  "2.endOffset": 8,
  "text": "abcdefg\n",
  "size": 8
}
{
  "1.filename": "test/4.txt",
  "2.filename": "test/5.txt",
  "1.startOffset": 0,
  "1.endOffset": 7,
  "2.startOffset": 0,
  "2.endOffset": 7,
  "text": "we all ",
  "size": 7
}
{
  "1.filename": "test/4.txt",
  "2.filename": "test/5.txt",
  "1.startOffset": 7,
  "1.endOffset": 13,
  "2.startOffset": 16,
  "2.endOffset": 22,
  "text": "scream",
  "size": 6
}
```