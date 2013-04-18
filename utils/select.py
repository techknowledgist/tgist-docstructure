"""

Module that gives access to individual sections in a file that was processed by the
document structure parser.

Usage:

   % python select.py elsevier-simple.txt elsevier-simple.sect INTRDDUCTION

   this selects all sections whose type is INTRODUCTION
   
   Note that different types can refer to the same stretch of text.

The main limitation is that this script does not take embedding into consideration. So a
section is basically defined as a stretch of text between two headers. This is due to
current limitations on what the document parser produces.

"""


import sys, codecs


class SectionReader(object):

    """Object that stores the text and, for each section type, a list of start and end
    offsets. It maintains these object to give easy access to the content of all sections
    in a document."""
    
    def __init__(self, text_file, sect_file):
        """Load the text and the section types."""
        self.text = codecs.open(text_file, encoding='utf-8').read()
        self.sections = {}
        fh_sect = codecs.open(sect_file, encoding='utf-8')
        for line in fh_sect:
            p1 = line.find('START')
            p2 = line.find('END')
            p3 = line.find('TYPE')
            start = line[p1+6:].split()[0] 
            end = line[p2+4:].split()[0]
            label = line[p3+5:p1].strip()
            label = label.strip('"')
            labels = label.split('|')
            for label in labels:
                self.sections.setdefault(label, []).append((int(start), int(end)))

    def get_sections(self, sectiontype):
        """Return a list of strings, where each string is the text content of a section of
        the prescribed type."""
        return [self.text[x:y] for (x,y) in self.sections.get(sectiontype,[])]

    def section_types(self):
        """Return a list of all section types in the document."""
        return sorted(self.sections.keys())
        
    def print_sections(self):
        for key in self.section_types():
            print ' ', key, self.sections[key]

        
if __name__ == '__main__':

    text_file, sect_file, sectiontype = sys.argv[1:4]
    reader = SectionReader(text_file, sect_file)
    #print reader.section_types()
    #reader.print_sections()
    for section in reader.get_sections(sectiontype):
        print ">" * 70
        print section
        print "=" * 70
        print
