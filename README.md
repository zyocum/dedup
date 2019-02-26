# Dedup

A Python script for finding duplicate text files.

## Install
```
$ python3 -m venv .
$ source bin/activate
(dedup) $ pip install -r requirements.txt
```

## Usage

```
usage: dedup.py [-h] [-n N_GRAM_SIZE] [-s {32,64,128}] [-r THRESHOLD] [-v]
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
  -s {32,64,128}, --hash-size {32,64,128}
                        hash size (in bits) (default: 32)
  -r THRESHOLD, --threshold THRESHOLD
                        threshold for how much two documents can differ in
                        their LSHs before they are not considered duplicates
                        (lower thresholds are more strict; higher thresholds
                        are more lenient) (default: 0.25)
  -v, --verbose         print duplicate counts to stderr (default: False)
$ find test -name "*.txt" | xargs head
==> test/5.txt <==
we all like ice scream

==> test/4.txt <==
we all scream for ice cream

==> test/6.txt <==
abcdefg

==> test/7.txt <==
abcdefg
hijklmnop

==> test/3.txt <==
we all scream for ice scream

==> test/2.txt <==
the cat sat on the mat

==> test/1.txt <==
the cat sat in the hat
$ find test -name "*.txt" | ./dedup.py -
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 5299.66files/s]
100%|███████████████████████████████████████████████████████████████████████████████████████████████| 32/32 [00:00<00:00, 3571.81rotations/s]
test/1.txt	test/2.txt
test/3.txt	test/4.txt
test/3.txt	test/5.txt
test/7.txt	test/6.txt

```