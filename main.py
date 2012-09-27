"""

Main executable for the document structure parser. 

Usage:

   % python main.py [-h] TEXT_FILE FACT_FILE STRUCTURE_FILE [COLLECTION]
   % python main.py FILE_LIST [COLLECTION]
   % python main.py DIRECTORY [COLLECTION]
   % python main.py -t [-v]
   
In the first form, input is taken from TEXT_FILE, which contains the bare text, and
FACT_FILE, which contains some structural tags taken from the low-level input parser. The
output is written to STRUCTURE_FILE, which has lines like the following

   SECTION ID=1 TYPE="UNLABELED" START=0 END=3978
   SECTION ID=2 TYPE="INTRODUCTION" TITLE="INTRODUCTION" START=3978 END=6016

If the -h option is specified, html versions of the fact file and the sect file will be
created and saved as FACT_FILE.html and SECT_FILE.html.

In the second form, the input and output files are specified in the file FILE_LIST. In the
third form, all pairs of .txt and .fact files in DIRECTORY are processed and .sect files
are created.

The optional COLLECTION argument specifies the collection that the input document was
taken from. This can be used to overrule the default behaviour, which is to scan the fact
file and find the following line:

   DOCUMENT COLLECTION="$COLLECTION"

In this line, $COLLECTION is in ('WEB_OF_SCIENCE', 'LEXISNEXIS', 'PUBMED', 'ELSEVIER').

Finally, in the fourth form, a simple sanity check is run, where four files (one pubmed,
one mockup Elsevier, one mockup WOS and one patent) are processed and the diffs between
the resulting .sect files and the regression files are printed to the standard
output. With the -v option, more verbose utput is printed, which adds the content of all
the generated .sect files.

If the code fails the regression test, the coder is responsible for checking why that
happened and do on eof two things: (i) change the code if a bug was introduced, (ii)
update the files in data/regression if code changes introduced legitimate changes to the
output.

"""


import os, sys, codecs, re, getopt, difflib
import elsevier1, elsevier2, pubmed, wos, lexisnexis, utils.view



def process_file(text_file, fact_file, sect_file, collection, verbose=False, html=False):
    """
    Takes a text file and a fact file and creates a .sections file with the section data.
    The data in fact_file can have two formats: (i) the format generated by the BAE
    wrapper and (ii) the format generated by create_standoff.pl. """
    section_factory = create_factory(text_file, fact_file, sect_file, collection, verbose)
    try:
        section_factory.make_sections()
        f = codecs.open(section_factory.sect_file, "w", encoding='utf-8')
        section_factory.print_sections(f)
        f.close()
        if html:
            utils.view.createHTML(text_file, fact_file, fact_file + '.html')
            utils.view.createHTML(text_file, sect_file, sect_file + '.html')
    except UserWarning:
        print 'WARNING:', sys.exc_value

def process_files(file_list, collection):
    """
    Takes a file with names of input and output files and processes them. Each line in the
    file has three filenames, separated by tabs, the first file is the text inut file, the
    second the fact input file, and the third the output file."""
    for line in open(file_list):
        (txt_file, fact_file, sections_file) = line.strip().split()
        process_file(txt_file, fact_file, sections_file, collection)

def process_directory(path, collection):
    """
    Processes all files in a directory with text and fact files. Takes all .txt files,
    finds sister files with extension .fact and then creates .sect files."""
    text_files = []
    fact_files= {}
    for f in os.listdir(path):
        if f.endswith('.txt'): text_files.append(f)
        if f.endswith('.fact'): fact_files[f] = True
    for text_file in text_files:
        fact_file = text_file[:-4] + '.fact'
        sect_file = text_file[:-4] + '.sect'
        if fact_files.has_key(fact_file):
            text_file = os.path.join(path, text_file)
            fact_file = os.path.join(path, fact_file)
            sect_file = os.path.join(path, sect_file)
            process_file(text_file, fact_file, sect_file, collection)

def create_factory(text_file, fact_file, sect_file, collection, verbose=False):
    """
    Returns the factory needed given the collection parameter and specifications in the
    fact file and, if needed, some characteristics gathered from the text file."""
    if collection is None:
        collection = determine_collection(fact_file)
    if collection == 'PUBMED': 
        return pubmed.BiomedNxmlSectionFactory(text_file, fact_file, sect_file, verbose)
    elif collection == 'WEB_OF_SCIENCE':
        return wos.WebOfScienceSectionFactory(text_file, fact_file, sect_file, verbose) 
    elif collection == 'LEXISNEXIS':
        return lexisnexis.PatentSectionFactory(text_file, fact_file, sect_file, verbose)
    elif collection == 'ELSEVIER':
        return create_elsevier_factory(text_file, fact_file, sect_file, verbose)
    elif collection == 'C_ELSEVIER':
        return elsevier2.ComplexElsevierSectionFactory(text_file, fact_file, sect_file, verbose)

def  create_elsevier_factory(text_file, fact_file, sect_file, verbose=False):
    """
    Since Elsevier data come in two flavours and each flavour has its own factory, check
    the file to make sure what kind of Elsevier document we are dealing with. It appears
    that counting occurrences of the TEXT type in the fact file predicts whether an
    Elsevier file is structured or not with a precision of about 0.99."""
    fh = open(fact_file)
    text_tags = len( [l for l in fh.readlines() if l.find('TEXT') > -1] )
    fh.close()
    if text_tags < 4 :
        return elsevier1.SimpleElsevierSectionFactory(text_file, fact_file, sect_file)
    else:
        return elsevier2.ComplexElsevierSectionFactory(text_file, fact_file, sect_file, verbose)

def determine_collection(fact_file):
    """
    Loop through the fact file in order to find the line that specifies the collection."""
    # THIS CODE HAS NOT YET BEEN PROPERLY TESTED
    expr = re.compile('DOCUMENT.*COLLECTION="(\S+)"')
    for line in open(fact_file):
        result = expr.search(line)
        if result is not None:
            return result.group(1)
    return None

def run_tests(verbose=False):
    """Runs a test on four files: a pubmed file, a mockup WOS file, a mockup unstructured
    Elsevier file, and a LexisNexis patent. Prints the output of the document parser as
    well as a diff of that output relative to a file in the data/regression directory."""
    files = (
        'f401516f-bd40-11e0-9557-52c9fc93ebe0-001-gkp847',
        'elsevier-simple',
        'US4192770A',
        'wos'
        )
    results = []
    for f in files:
        if verbose:
            print "==> %s\n" % f
        text_file = "data/%s.txt" % f
        fact_file = "data/%s.fact" % f
        sect_file = "data/%s.sect" % f
        key_file ="data/regression/%s.sect" % f
        process_file(text_file, fact_file, sect_file, None, verbose=False)
        response = open(sect_file).readlines()
        key = open(key_file).readlines()
        if verbose:
            print ''.join(response)
        results.append((f, sect_file, response, key_file, key))
    if verbose:
        print
    for filename, sect_file, response, key_file, key in results:
        print "\n==> %s (diff)" % filename
        for line in difflib.unified_diff(response, key, fromfile=sect_file, tofile=key_file):
            sys.stdout.write(line)
                
    
if __name__ == '__main__':

    (opts, args) = getopt.getopt(sys.argv[1:], 'htv')
    test_mode, html_mode, verbose = False, False, False
    for opt, val in opts:
        if opt == '-t': test_mode = True
        if opt == '-h': html_mode = True
        if opt == '-v': verbose = True

    # when called to run some simple tests
    if test_mode:
        run_tests(verbose)
            
    # when called to process one file
    elif len(args) >= 3:
        text_file, fact_file, sect_file = args[:3]
        collection = args[3] if len(args) > 3 else None
        process_file(text_file, fact_file, sect_file, collection, verbose=False, html=html_mode)

    # processing multiple files
    elif len(sys.argv) >= 2:
        path = sys.argv[1]
        collection = sys.argv[2] if len(sys.argv) > 2 else None
        # using directory
        if os.path.isdir(path):
            process_directory(path, collection)
        # using a file that lists files to process
        elif os.path.isfile(path):
            process_files(path, collection)

    # by default
    else:
        text_file = "doc.txt"
        fact_file = "doc.fact"
        sect_file = "doc.sections"
        collection = 'C_ELSEVIER'
        process_file(text_file, fact_file, sect_file, collection, verbose=True, html=False)
        
