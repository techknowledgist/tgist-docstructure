"""

Main executable for the document structure parser. 

Usage:

   % python main.py TEXT_FILE FACT_FILE STRUCTURE_FILE

Input is taken from TEXT_FILE, which contains the bare text, and FACT_FILE, which contains
some structural tags taken from th elow-level input parser. The output is written to
STRUCTURE_FILE, which has lines like the following

   SECTION ID=1 TYPE="UNLABELED" START=0 END=3978
   SECTION ID=2 TYPE="INTRODUCTION" TITLE="INTRODUCTION" START=3978 END=6016

Currently, there is no good way to determine what kind of document we are dealing
with. Some additions to FACT_FILE are needed.

"""


import os, sys, codecs
import sections


def process_file(text_file, fact_file, sect_file, is_patent=False):
    """
    Takes a text file and a fact file and creates a .sections file with the section data.
    The data in fact_file can have two formats: (i) the format generated by the BAE
    wrapper and (ii) the format generated by create_standoff.pl. """
    section_factory = create_factory(text_file, fact_file, sect_file,is_patent)
    try:
        section_factory.make_sections()
        f = codecs.open(section_factory.sect_file, "w", encoding='utf-8')
        section_factory.print_sections(f)
        f.close()
    except UserWarning:
        print 'WARNING:', sys.exc_value

def process_files(file_list):
    """
    This does not work with the new input format yet, but is intended to provide a way to
    process files in batch."""
    if isinstance(file_list,str):
        for line in open(file_list):
            basename = line.strip()
            process_file(basename)
    else:
        for basename in file_list:
            process_file(basename+".txt",basename+".tag",basename+".sections")

def process_all(path="."):
    """
    Does not work with the new format yet, but would process all files in a directory with
    text and fact files."""
    listing = os.listdir(path)
    basenames = filter(lambda x: x[-5:] == ".nxml", listing)
    process_files(basenames)

def create_factory(text_file, fact_file, sect_file, is_patent=False):
    """
    Returns the factory needed given the filename, for now, hardwired to just one factory
    type, but should use the path and, for Elsevier data), the tags available, to
    determine what factory to use. """
    if is_patent:
        return sections.PatentSectionFactory(text_file, fact_file, sect_file)
    characteristics = collect_file_characteristics(text_file)
    white_lines = characteristics['white_lines'] 
    total_lines = characteristics['total_lines']
    white_line_ratio = float(white_lines) / (total_lines + 1)
    if white_line_ratio > 0.1:
        return sections.BiomedNxmlSectionFactory(text_file, fact_file, sect_file)
    return sections.SimpleElsevierSectionFactory(text_file, fact_file, sect_file)
    
def collect_file_characteristics(text_file):
    """
    This is a bit of a hack that is used to decide what kind of file we are dealing with,
    using file characteristics like the number of whitelines. Ideally, we would get that
    as a meta feature or by looking at the tags instead of the bare text. This method will
    stay here till we have a better way. If we do not find a better way, this should
    probably include all the characterisrics we extract for the Elsevier simple format."""
    white_lines = 0
    total_lines = 0
    f = codecs.open(text_file, "r", encoding='utf-8')
    for line in f:
        total_lines += 1
        if len(line.strip()) == 0:
            white_lines += 1
    f.close()
    characteristics = { 'white_lines': white_lines, 'total_lines': total_lines }
    return characteristics


    
if __name__ == '__main__':

    text_file = 'tmp.nxml.txt'
    fact_file = 'tmp.nxml.tag'
    sect_file = 'tmp.nxml.sections'
    if len(sys.argv) > 3:
        text_file, fact_file, sect_file = sys.argv[1:4]
    process_file(text_file, fact_file, sect_file, is_patent=True)
