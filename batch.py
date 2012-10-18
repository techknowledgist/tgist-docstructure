"""

Example batch script. This one want as input a directory that has txt and fact files.

"""

import os, sys, glob

from main import Parser


INDIR = sys.argv[1]
OUTDIR = 'data/tmp'


for text_file in glob.glob("%s/*.txt" % INDIR):
    basename = os.path.basename(text_file)
    fact_file = text_file[:-3] + 'fact'
    sect_file = os.path.join(OUTDIR, basename[:-3] + 'sect')
    if os.path.exists(fact_file):
        #if not basename == 'USPP021257P2.txt':
        #    continue
        print basename
        parser = Parser()
        parser.collection = 'LEXISNEXIS'
        parser.process_file(text_file, fact_file, sect_file, verbose=False)
