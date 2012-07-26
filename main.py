import os, sys, codecs
import sections


def convert_file(text_file, fact_file, sect_file):
    """
    Takes a filename, creates a .sections file with the section data.
    Preprocessing must have been done with create_standoff.pl. """
    section_factory = create_factory(text_file, fact_file, sect_file)
    try:
        section_factory.make_sections()
        f = codecs.open(section_factory.sect_file, "w", encoding='utf-8')
        section_factory.print_sections(f)
        f.close()
    except UserWarning:
        print 'WARNING:', sys.exc_value

def convert_files(file_list):
    """
    Takes either a list of filenames or a filename of a file containing a list
    of filenames, and creates .sections files with the section data in those
    files. Preprocessing must have been done with create_standoff.pl. """
    if isinstance(file_list,str):
        for line in open(file_list):
            basename = line.strip()
            convert_file(basename)
    else:
        for basename in file_list:
            convert_file(basename+".txt",basename+".tag",basename+".sections")

def convert_all(path="."):
    """
    Creates .sections files from all the files with ending .nxml at the given
    path. Preprocessing must have been done with create_standoff.pl. """
    listing = os.listdir(path)
    basenames = filter(lambda x: x[-5:] == ".nxml", listing)
    convert_files(basenames)

def create_factory(text_file, fact_file, sect_file):
    """
    Returns the factory needed given the filename, for now, hardwired to just one factory
    type, but should use the path and, for Elsevier data), the tags available, to
    determine what factory to use. """
    if text_file.startswith('data/elsevier'):
        return sections.SimpleElsevierSectionFactory(text_file, fact_file, sect_file)
    return sections.BiomedNxmlSectionFactory(text_file, fact_file, sect_file)
    

if __name__ == '__main__':

    text_file = 'tmp.nxml.txt'
    fact_file = 'tmp.nxml.tag'
    sect_file = 'tmp.nxml.sections'
    if len(sys.argv) > 3:
        text_file, fact_file, sect_file = sys.argv[1:4]
    convert_file(text_file, fact_file, sect_file)
    #convert_files('data/list.txt')
