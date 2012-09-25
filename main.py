"""

Main executable for the document structure parser. 

Usage:

   % python main.py [OPTIONS] TEXT_FILE FACT_FILE STRUCTURE_FILE
   % python main.py [OPTIONS] XML_FILE TEXT_FILE TAGS_FILE FACT_FILE STRUCTURE_FILE
   % python main.py [-c COLLECTION] [-l LANGUAGE] FILE_LIST
   % python main.py [-c COLLECTION] [-l LANGUAGE] DIRECTORY
   % python main.py -o XML_FILE TEXT_FILE TAGS_FILE FACT_FILE STRUCTURE_FILE ONTO_FILE
   % python main.py -t

In the first form, input is taken from TEXT_FILE, which contains the bare text, and
FACT_FILE, which contains some structural tags taken from the low-level BAE input
parser. The output is written to STRUCTURE_FILE, which has lines like the following

   SECTION ID=1 TYPE="UNLABELED" START=0 END=3978
   SECTION ID=2 TYPE="INTRODUCTION" TITLE="INTRODUCTION" START=3978 END=6016

In the secons form, the input is an xml file and three intermediate files are created:
text file, tags file and facts file. As with form 1, the text file and the fact file are
then used to create the sect file. Both forms have the same options, all optional:

   [-h] [-c COLLECTION] [-l LANGUAGE]
   
If the -h option is specified, html versions of the fact file and the sect file will be
created and saved as FACT_FILE.html and SECT_FILE.html.

The [-h COLLECTION] argument specifies the collection that the input document was
taken from. This can be used to overrule the default behaviour, which is to scan the fact
file and find the following line:

   DOCUMENT COLLECTION="$COLLECTION"

In this line, $COLLECTION is in ('WEB_OF_SCIENCE', 'LEXISNEXIS', 'PUBMED', 'ELSEVIER').

Simliarly, with [-l LANGUAGE} the language can be handed in as an argument. Values are
'ENGLISH', 'GERMAN' and 'CHINESE'. As with the collection, the default behaviour is to
scan the fact file if there is one, searching for

   DOCUMENT LANGUAGE="ENGLISH|CHINESE|GERMAN"

In the third form, the input and output files are specified in the file FILE_LIST. In the
fourth form, all pairs of .txt and .fact files in DIRECTORY are processed and .sect files
are created. Both these forms have the -l and -c options, but the -h option will be
ignored. In both cases, whether the oprions are specified or not, the language and
collection are assumed to be the saem for all files in the list or directory.

In the fifth form, an XML file is taken and an input file for ontology creation is
generated. This is currentyl only relevant for patents. 

Finally, in the sixth form, a simple sanity check is run, where four files (one pubmed,
one mockup Elsevier, one mockup WOS and one patent) are processed and the diffs between
the resulting .sect files and the regression files are printed to the standard
output.

If the code fails the regression test, the coder is responsible for checking why that
happened and do one of two things: (i) change the code if a bug was introduced, (ii)
update the files in data/regression if code changes introduced legitimate changes to the
output.

"""


import os, sys, codecs, re, getopt, difflib
import elsevier1, elsevier2, pubmed, wos, lexisnexis, utils.view
from readers.common import load_data, open_write_file
from utils.xml import transform_tags_file
from utils.misc import run_shell_commands


def usage():
    print "\nUsage:"
    print '  % python main.py [-h] [-c COLLECTION] [-l LANGUAGE] ' \
          + 'TEXT_FILE FACT_FILE STRUCTURE_FILE'
    print '  % python main.py [-h] [-c COLLECTION] [-l LANGUAGE] ' \
          + 'XML_FILE TEXT_FILE TAGS_FILE FACT_FILE STRUCTURE_FILE'
    print '  % python main.py [-c COLLECTION] [-l LANGUAGE] FILE_LIST'
    print '  % python main.py [-c COLLECTION] [-l LANGUAGE] DIRECTORY'
    print '  % python main.py -o XML_FILE TEXT_FILE TAGS_FILE ' \
          + 'FACT_FILE STRUCTURE_FILE ONTO_FILE'
    print '  % python main.py -t'

    
def create_fact_file(xml_file, text_file, tags_file, fact_file):
    """Given an xml file, first create text and tags files using the xslt standoff scripts and
    then create a fact file."""
    dirname = os.path.dirname(__file__)
    text_xsl = os.path.join(dirname, 'utils/standoff/text-content.xsl')
    tags_xsl = os.path.join(dirname, 'utils/standoff/standoff.xsl')
    commands = [
        "xsltproc %s %s > %s" % (text_xsl, xml_file, text_file),
        "xsltproc %s %s | xmllint --format - > %s" % (tags_xsl, xml_file, tags_file)]
    run_shell_commands(commands)
    transform_tags_file(tags_file, fact_file)


class Parser(object):

    def __init__(self):
        self.test_mode = False
        self.html_mode = False
        self.onto_mode = False
        self.collection = None
        self.language = None

    def __str__(self):
        return "<Parser for %s on %s>" % (self.language, self.collection)
    

    def process_file(self, text_file, fact_file, sect_file, fact_type='BAE', verbose=False):
        """
        Takes a text file and a fact file and creates a sect file with the section data.
        The data in fact_file can have two formats: (i) the format generated by the BAE
        wrapper with fact_type=BAE and (ii) the format generated by utils/standoff with
        fact_type=BASIC. """
        self._create_factory(text_file, fact_file, sect_file, fact_type, verbose)
        try:
            self.factory.make_sections()
            f = codecs.open(self.factory.sect_file, "w", encoding='utf-8')
            self.factory.print_sections(f)
            f.close()
            if self.html_mode:
                fact_file_html = 'data/html/' + os.path.basename(fact_file) + '.html'
                sect_file_html = 'data/html/' + os.path.basename(sect_file) + '.html'
                utils.view.createHTML(text_file, fact_file, fact_file_html)
                utils.view.createHTML(text_file, sect_file, sect_file_html)
        except UserWarning:
            print 'WARNING:', sys.exc_value

    def process_xml_file(self, xml_file, text_file, tags_file, fact_file, sect_file,
                         verbose=False):
        """
        Takes an xml file and creates sect file, while generating some intermediate data."""
        create_fact_file(xml_file, text_file, tags_file, fact_file)
        self.process_file(text_file, fact_file, sect_file, fact_type='BASIC', verbose=verbose)

    def process_directory(self, path):
        """
        Processes all files in a directory with text and fact files. Takes all .txt files,
        finds sister files with extension .fact and then creates .sect files."""
        # TODO: add --xml option for directories with only xml files
        text_files = []
        fact_files= {}
        for f in os.listdir(path):
            if f.endswith('.txt'): text_files.append(f)
            if f.endswith('.fact'): fact_files[f] = True
        total_files = len(text_files)
        file_number = 0
        print "Processing %d files" % total_files
        for text_file in text_files:
            file_number += 1
            fact_file = text_file[:-4] + '.fact'
            sect_file = text_file[:-4] + '.sect'
            if fact_files.has_key(fact_file):
                text_file = os.path.join(path, text_file)
                fact_file = os.path.join(path, fact_file)
                sect_file = os.path.join(path, sect_file)
                print "Processing %d of %d: %s" % (file_number, total_files, text_file[:-4])
                self.process_file(text_file, fact_file, sect_file)

    def process_files(self, file_list):
        """
        Takes a file with names of input and output files and processes them. Each line in the
        file has three filenames, separated by tabs, the first file is the text inut file, the
        second the fact input file, and the third the output file."""
        # TODO: may want to extend this to XML files
        for line in open(file_list):
            (text_file, fact_file, sections_file) = line.strip().split()
            #print "Processing  %s" % (text_file[:-4])
            self.process_file(text_file, fact_file, sections_file)

    def _create_factory(self, text_file, fact_file, sect_file, fact_type, verbose=False):
        """
        Returns the factory needed given the collection parameter and specifications in the
        fact file and, if needed, some characteristics gathered from the text file."""
        self._determine_collection(fact_file)
        if self.collection == 'PUBMED': 
            self.factory = pubmed.BiomedNxmlSectionFactory(
                text_file, fact_file, sect_file, fact_type, self.language, verbose)
        elif self.collection == 'WEB_OF_SCIENCE':
            self.factory = wos.WebOfScienceSectionFactory(
                text_file, fact_file, sect_file, fact_type, self.language, verbose) 
        elif self.collection == 'LEXISNEXIS':
            self.factory = lexisnexis.PatentSectionFactory(
                text_file, fact_file, sect_file, fact_type, self.language, verbose)
        elif self.collection == 'ELSEVIER':
            self.factory = self._create_elsevier_factory(
                text_file, fact_file, sect_file, fact_type, verbose)
        else:
            raise Exception("No factory could be created")

    def _create_elsevier_factory(self, text_file, fact_file, sect_file,
                             fact_type, verbose=False):
        """
        Since Elsevier data come in two flavours and each flavour has its own factory, check
        the file to make sure what kind of Elsevier document we are dealing with. It appears
        that counting occurrences of the TEXT type in the fact file predicts whether an
        Elsevier file is structured or not with a precision of about 0.99."""
        fh = open(fact_file)
        text_tags = len( [l for l in fh.readlines() if l.find('TEXT') > -1] )
        fh.close()
        if text_tags < 4 :
            return elsevier1.SimpleElsevierSectionFactory(
                text_file, fact_file, sect_file, fact_type, self.language)
        else:
            return elsevier2.ComplexElsevierSectionFactory(
                text_file, fact_file, sect_file, fact_type, self.language, verbose)
    
    def _determine_collection(self, fact_file):
        """
        Loop through the fact file in order to find the line that specifies the collection."""
        if self.collection is None:
            expr = re.compile('DOCUMENT.*COLLECTION="(\S+)"')
            for line in open(fact_file):
                result = expr.search(line)
                if result is not None:
                    self.collection = result.group(1)
                    break

    def run_tests(self):
        """
        Runs a regression test on a couple of files. For all these files, there needs to be a
        sect file in data/regression. Prints a diff of the output of the document parser
        relative to a file in the data/regression directory."""
        files = (
            ('pubmed', 'f401516f-bd40-11e0-9557-52c9fc93ebe0-001-gkp847'),
            ('pubmed', 'pubmed-mm-test'),
            ('elsevier', 'elsevier-simple'),
            ('elsevier', 'elsevier-complex'),
            ('lexisnexis', 'US4192770A'),
            ('lexisnexis', 'US4192770A.xml'),
            ('wos', 'wos')
            )
        results = []
        self.html_mode = True
        for collection, filename in files:
            self.run_test(collection, filename, results)
        for filename, sect_file, response, key_file, key in results:
            print "\n==> %s" % filename
            for line in difflib.unified_diff(response, key, fromfile=sect_file, tofile=key_file):
                sys.stdout.write(line)
        print 

    def run_test(self, collection, filename, results):
        # reset the collection every iteration, we are not using the collection argument
        # on purpose because we want to also test whether the code finds the collection in
        # the fact file
        self.collection = None
        if filename.endswith('.xml'):
            self.run_test_with_basic_input(collection, filename, results)
        else:
            self.run_test_with_bae_input(collection, filename, results)
        
    def run_test_with_basic_input(self, collection, filename, results):
        self.collection = 'LEXISNEXIS'
        xml_file = "data/in/%s/%s" % (collection, filename)
        text_file = "data/tmp/%s.txt" % filename
        tags_file = "data/tmp/%s.tags" % filename
        fact_file = "data/tmp/%s.fact" % filename
        sect_file = "data/out/%s.sect.basic" % filename
        key_file ="data/regression/%s.sect" % filename
        self.process_xml_file(xml_file, text_file, tags_file, fact_file, sect_file)
        response = open(sect_file).readlines()
        key = open(key_file).readlines()
        results.append((filename, sect_file, response, key_file, key))
    
    def run_test_with_bae_input(self, collection, filename, results):
        text_file = "data/in/%s/%s.txt" % (collection, filename)
        fact_file = "data/in/%s/%s.fact" % (collection, filename)
        sect_file = "data/out/%s.sect.bae" % filename
        key_file ="data/regression/%s.sect" % filename
        self.process_file(text_file, fact_file, sect_file)
        response = open(sect_file).readlines()
        key = open(key_file).readlines()
        results.append((filename, sect_file, response, key_file, key))
        
    def create_ontology_creation_input(self, xml_file, text_file, tags_file,
                                       fact_file, sect_file, onto_file):
        """Create input files that can be used by the ontology creation process. It is
        currently only guaranteed to work for English patents."""
        # TODO: german gets wrong abstract
        create_fact_file(xml_file, text_file, tags_file, fact_file)
        self.collection = 'LEXISNEXIS'
        self.process_file(text_file, fact_file, sect_file, fact_type='BASIC')
        (text, section_tags) = load_data(text_file, sect_file)
        TARGET_FIELDS = ['FH_TITLE', 'FH_DATE', 'FH_ABSTRACT', 'FH_SUMMARY',
                         'FH_DESC_REST', 'FH_FIRST_CLAIM']
        USED_FIELDS = TARGET_FIELDS + ['FH_DESCRIPTION']
        FH_DATA = {}
        for f in USED_FIELDS: FH_DATA[f] = None
        self._add_usable_sections(section_tags, text, FH_DATA)
        ONTO_FH = open_write_file(onto_file)
        for f in TARGET_FIELDS:
            # TODO: make more specific
            try:
                ONTO_FH.write("%s:\n" % f)
                ONTO_FH.write(FH_DATA[f][2].encode('utf-8'))
                ONTO_FH.write("\n")
            except Exception:
                pass
        ONTO_FH.write("END\n")

    def _add_usable_sections(self, section_tags, text, FH_DATA):
        mappings = { 'META-TITLE': 'FH_TITLE', 'META-DATE': 'FH_DATE',
                     'ABSTRACT': 'FH_ABSTRACT', 'SUMMARY': 'FH_SUMMARY',
                     'DESCRIPTION': 'FH_DESCRIPTION' }
        for tag in section_tags:
            (p1, p2, tagtype) = (tag.start_index, tag.end_index, tag.attr('TYPE'))
            if mappings.get(tagtype) is not None:
                FH_DATA[mappings[tagtype]] = (p1, p2, text[int(p1):int(p2)].strip())
            elif tagtype == 'CLAIM':
                if tag.attr('CLAIM_NUMBER') == '1':
                    FH_DATA['FH_FIRST_CLAIM'] = (p1, p2, text[int(p1):int(p2)].strip())
            desc = FH_DATA['FH_DESCRIPTION']
            summ = FH_DATA['FH_SUMMARY']
            if desc and summ:
                FH_DATA['FH_DESC_REST'] = (summ[1], desc[1], text[summ[1]:desc[1]].strip())
        

    
if __name__ == '__main__':

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'htoc:l:')
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    parser = Parser()
    for opt, val in opts:
        if opt == '-t': parser.test_mode = True
        if opt == '-h': parser.html_mode = True
        if opt == '-o': parser.onto_mode = True
        if opt == '-c': parser.collection = val
        if opt == '-l': parser.language = val
    
    # run some simple tests
    if parser.test_mode:
        parser.run_tests()

    # create ontology input
    elif parser.onto_mode:
        xml_file, txt_file, tags_file, fact_file, sect_file, onto_file = args
        parser.create_ontology_creation_input(xml_file, txt_file, tags_file,
                                              fact_file, sect_file, onto_file)

    # process a text file and a fact file, creating a sect file
    elif len(args) == 3:
        text_file, fact_file, sect_file = args
        parser.process_file(text_file, fact_file, sect_file, verbose=False)

    # process an xml file, creating txt file, tags file, fact file and sect file
    elif len(args) == 5:
        xml_file, txt_file, tags_file, fact_file, sect_file = args
        parser.process_xml_file(xml_file, txt_file, tags_file, fact_file, sect_file, 
                                verbose=False)

    # process multiple files listed in an input file or the contents of a directory
    elif len(args) == 1:
        path = args[0]
        if os.path.isdir(path):
            parser.process_directory(path)
        elif os.path.isfile(path):
            parser.process_files(path)

    # by default
    else:
        text_file = "doc.txt"
        fact_file = "doc.fact"
        sect_file = "doc.sections"
        parser.collection = 'PUBMED'
        parser.process_file(text_file, fact_file, sect_file, verbose=False)
        
