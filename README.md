# Obeliks - sentence splitting & tokenization

## Instalation

Install from PyPI:
```shell
pip install obeliks
```

## Usage

### Command line:
```shell
obeliks -h
```

Command line parameters:
```
-if <name*> read input from one or more files
-sif        read input from list of files, specified via stdin
-o <name>   write output to file <name>
-tei        produce XML-TEI output
-c		    produce CoNLL-U output
-d		    pass "newdoc id" to output (implies -c)
```

Usage examples:
```shell
obeliks "To je stavek." "Tudi to je stavek."
```
```shell
echo -e "To je stavek.\nTudi to je stavek." | obeliks
```
```shell
obeliks "To je stavek." "Tudi to je stavek." -o output.txt
```
```shell
echo -e "To je stavek.\nTudi to je stavek." | obeliks > output.txt
```
```shell
obeliks -if text*.txt
```
```shell
cat text*.txt | obeliks
```


### As a Python module:
```python
import obeliks

text = 'Pozdravljen, svet!'

# Store results to string
output = obeliks.run(text, conllu=True)

# Write result to file
obeliks.run(text, out_file='tei.txt', tei=True)

# Write to stdout
obeliks.run(text, to_stdout=True, conllu=True)

# Return object
object = obeliks.run(text, object_output=True)

# Read input from file(s)
output = obeliks.run(in_file='in.txt', conllu=True)
output = obeliks.run(in_files=['in1.txt', 'in2.txt'], tei=True)
```

