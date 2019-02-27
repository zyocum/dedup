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
(dedup) $ find test -name "*.txt" | ./dedup.py - -r 0.33 -b 128 | ./matching_substrings.py - -j | jq .
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 1655.68files/s]
100%|████████████████████████████████████████████████████████████████████████████████████████████| 128/128 [00:00<00:00, 12382.85rotations/s]
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

## Locality Sensitive Hashing

The script uses locality sensitive hashing (LSH) to compare texts.  LSHs are a kind of hashing function that, unlike normal hashing functions, have the property that the probability of a hash collision is proportional to the similarity of objects hashed.  In this case, the LSH implemented is simhash (described [here](http://matpalm.com/resemblance/simhash/)).

Running `dedup.py` with the `-v/--verbose` option prints the binary values of the computed LSHs and shows the similarity scores:

```
# 32 bit LSH
(dedup) $ find test -name "*.txt" | ./dedup.py - -v
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 5169.95files/s]
  0%|                                                                                                          | 0/32 [00:00<?, ?rotations/s]test/1.txt : the cat sat in the hat

test/2.txt : the cat sat on the mat

00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001001110100011100101111100010
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001001010100111101101110111010
0.1875
test/3.txt : we all scream for ice scream

test/4.txt : we all scream for ice cream

00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010001000010001111101100001011010
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010001000010001111101000101011110
0.09375
test/3.txt : we all scream for ice scream

test/5.txt : we all like ice scream

00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010001000010001111101100001011010
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010011000010011111101100011001110
0.15625
test/4.txt : we all scream for ice cream

test/5.txt : we all like ice scream

00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011010001000010001111101000101011
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011010011000010011111101100011001
0.1875
test/7.txt : abcdefg
hijklmnop

test/6.txt : abcdefg

00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001101100000001101001111010110110
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001101000001000101001111010110001
0.1875
100%|██████████████████████████████████████████████████████████████████████████████████████████████| 32/32 [00:00<00:00, 17233.91rotations/s]
found 1 duplicate(s) of file:  test/1.txt
test/1.txt	test/2.txt
found 2 duplicate(s) of file:  test/3.txt
test/3.txt	test/4.txt
test/3.txt	test/5.txt
found 1 duplicate(s) of file:  test/4.txt
test/4.txt	test/5.txt
found 1 duplicate(s) of file:  test/7.txt
test/7.txt	test/6.txt
found 5 duplicate(s) in total
# 64 bit LSH
(dedup) $ find test -name "*.txt" | ./dedup.py - -v -b 64
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 3116.79files/s]
  0%|                                                                                                          | 0/64 [00:00<?, ?rotations/s]test/7.txt : abcdefg
hijklmnop

test/6.txt : abcdefg

00000000000000000000000000000000000000000000000000000000000000000000011110111011000101110111001001000010001001010011000101110100
00000000000000000000000000000000000000000000000000000000000000000010011110011011111100110111000001000010000001010011001111011100
0.1875
test/1.txt : the cat sat in the hat

test/2.txt : the cat sat on the mat

00000000000000000000000000000000000000000000000000000000000000000011000110100111001010111010011101000000100011001101111110100010
00000000000000000000000000000000000000000000000000000000000000000011000111100111100010111011011101000000100011001101111001100010
0.109375
test/3.txt : we all scream for ice scream

test/4.txt : we all scream for ice cream

00000000000000000000000000000000000000000000000000000000000000000101000000000111011010000000001000010000101010110001001001101001
00000000000000000000000000000000000000000000000000000000000000000101000000000111011011001000001000010100101011110001001001101001
0.0625
test/4.txt : we all scream for ice cream

test/5.txt : we all like ice scream

00000000000000000000000000000000000000000000000000000000000000000101000000000111011011001000001000010100101011110001001001101001
00000000000000000000000000000000000000000000000000000000000000000101000000001110011010000000001100010000100001011011001010001001
0.21875
test/3.txt : we all scream for ice scream

test/5.txt : we all like ice scream

00000000000000000000000000000000000000000000000000000000000000001100010010011010010101000000000111011010000000001000010000101010
00000000000000000000000000000000000000000000000000000000000000000110110010100010010101000000001110011010000000001100010000100001
0.1875
100%|██████████████████████████████████████████████████████████████████████████████████████████████| 64/64 [00:00<00:00, 15947.92rotations/s]
found 1 duplicate(s) of file:  test/7.txt
test/7.txt	test/6.txt
found 1 duplicate(s) of file:  test/1.txt
test/1.txt	test/2.txt
found 2 duplicate(s) of file:  test/3.txt
test/3.txt	test/5.txt
test/3.txt	test/4.txt
found 1 duplicate(s) of file:  test/4.txt
test/4.txt	test/5.txt
found 5 duplicate(s) in total
# 128 bit LSH
(dedup) $ find test -name "*.txt" | ./dedup.py - -v -b 128
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 829.01files/s]
  0%|                                                                                                         | 0/128 [00:00<?, ?rotations/s]test/1.txt : the cat sat in the hat

test/2.txt : the cat sat on the mat

00110000010010111010000110000100000111111100100001001000000000100110110000111010010001001001101101011010011000001110001010111001
00111010010010111010110110000000000111111000100100111000000000100010110000010010010001001101101101010010011100001010001010111001
0.1328125
test/3.txt : we all scream for ice scream

test/4.txt : we all scream for ice cream

11110111010000001011001000010000101100100000101000010011110010000011011100100111100110111100110011011000101101000110100011000110
11110111110000011011001000010000101100100000101000010011110010000111001110101111101110111100110011011000101101000110100011000110
0.0546875
test/7.txt : abcdefg
hijklmnop

test/6.txt : abcdefg

01110101000101011011101010010001100110011100101001010010000100100010110010011011010001101000100100000001000011000011000011101000
10011101110101011000101010010001110110010100111001111110000111101010100010011011010011101100100100110001101001011001000011110001
0.2421875
100%|█████████████████████████████████████████████████████████████████████████████████████████████| 128/128 [00:00<00:00, 6732.18rotations/s]
found 1 duplicate(s) of file:  test/1.txt
test/1.txt	test/2.txt
found 1 duplicate(s) of file:  test/3.txt
test/3.txt	test/4.txt
found 1 duplicate(s) of file:  test/7.txt
test/7.txt	test/6.txt
found 3 duplicate(s) in total
```

After computing an LSH for each document, the list of documents are sorted by their LSH and pairs of adjacent LSHs in the list are compared.  If an adjacent pair's LSHs are similar enough (based on a threshold), then the pair is considered a duplicate.  Considering the sorted list of LSHs once is not sufficient however, because if a pair of documents have high bits that differ, but most bits are still the same, they won't be considered, because they will be unlikely to be adjacent in the sorted list.  To mitigate this, each LSH is rotated and the lists of LSHs are sorted again, and again adjacent pairs are checked.

This strategy requires a pass over each of N documents to compute the LSHs, but once the LSHs are computed, it requires only N-1 * M comparisons where M is size of the LSH in bits.  When N is much larger than M, this is a significant improvement in time complexity over the naive approach of comparing N documents pairwise, which would require N choose 2 or N! / 2! * (N - 2)! comparisons.

If we have, say, over 100k documents to compare, performing N choose 2 comparisons becomes very expensive:

```
# ~241 days is a long time
(dedup) $ find ~/Desktop/words -type f | ./dedup_pairwise.py - > ~/Desktop/duplicates_pairwise.tsv
100%|███████████████████████████████████████████████████████████████████████████████████████████| 128959/128959 [00:20<00:00, 6251.87files/s]
  0%|                                                                                  | 1272202/8315147361 [01:58<241:35:38, 9559.05pairs/s
```

But, if we use the strategy of rotating the LSHs, we can find duplicates in a reasonable amount of time:

```
# <10 minutes is acceptable
(dedup) $ find ~/Desktop/words -type f | ./dedup.py - -r 0.1 -b 128 >| ~/Desktop/duplicates.tsv 
100%|███████████████████████████████████████████████████████████████████████████████████████████| 128959/128959 [00:35<00:00, 3623.02files/s]
100%|███████████████████████████████████████████████████████████████████████████████████████████████| 128/128 [07:53<00:00,  3.08s/rotations]
(dedup) $ wc -l ~/Desktop/duplicates.tsv 
    3841 /Users/zach/Desktop/duplicates.tsv
(dedup) $ head ~/Desktop/duplicates.tsv | while read a b; do cat "$a"; cat "$b"; echo "-----"; done
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