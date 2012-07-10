import codecs, re
from exceptions import UserWarning
import med_read, normheader


class Section(object):
    """
    Represents a semantically-typed section in a document. Should be used by all
    SectionFactories because the code to write to the poutput uses this class. """

    def __init__(self):
        self.types = []
        self.header = ""
        self.subsumers = []
        self.subsumed = []
        self.filename = ""
        self.start_index = -1
        self.end_index = -1
        self.text = ""

    def __str__(self):
        return "%s \n   %s..." % (str(self.types), self.text[:80])
    
    def __len__(self):
        return self.end_index - self.start_index

    
class SectionFactory(object):
    """
    Abstract class that contains shared code for the section factories for all data
    types. Provodes a unified interface for the code that calls the section creation
    code. Themain method called by outside code is make_sections(), which should be
    implemented on all subclasses."""
    
    def __init__(self, text_file, fact_file, sect_file):
        """
        The first two files given are the ones that are given by the wrapper, the third is a
        file that the wrapper expects. """
        self.text_file = text_file
        self.fact_file = fact_file
        self.sect_file = sect_file
        self.sections = []

    def __str__(self):
        return "<%s on %s>" % (self.__class__.__name__, self.filename)

    def make_sections(self):
        """
        Creates a list of Section instances ion self.sections. Each subclass should implement
        this method. """
        raise UserWarning, "make_sections() not implemented for %s " % self.__class__.__name__
    
    def print_sections(self, fh):
        """
        Prints section data to a file handle. """
        for section in self.sections:
            fh.write("SECTION Type=\"%s\" Title=\"%s\" Start=%d End=%d\n" %
                     ( "|".join(section.types), section.header, 
                     section.start_index, section.end_index))

            

### Code to deal with the Biomed nxml data
            
class BiomedNxmlSectionFactory(SectionFactory):


    def make_sections(self):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """

        (a_text, a_tags) = med_read.load_data(self.text_file, self.fact_file)
        raw_sections = med_read.headed_sections(a_tags)
        abstracts = med_read.find_abstracts(a_tags)
    
        for match in raw_sections:
            section = Section()
            section.types = normheader.header_to_types(match[0].text(a_text))
            section.header = match[0].text(a_text)
            section.filename = self.text_file
            section.start_index = match[1].start_index
            section.end_index = match[1].end_index
            section.text = match[1].text(a_text)
            self.sections.append(section)

        for abstract in abstracts:
            section = Section()
            section.types = ["Abstract"]
            section.filename = self.text_file
            section.start_index = abstract.start_index
            section.end_index = abstract.end_index
            section.text = abstract.text(a_text)
            self.sections.append(section)
            
        self.sections.extend(section_gaps(self.sections, a_text, self.text_file))
        link_sections(self.sections)
        self.sections = sorted(self.sections, key= lambda x: x.start_index)

        
def section_gaps(sections, text, filename=""):
    """
    Finds the unlabeled sections in a text and labels them "Unlabeled". """
    
    gaps = []
    end = len(text)
    sections = sorted(sections, key= lambda x: x.start_index)
    covered = 0
    for section in sections:
        start_index = section.start_index
        end_index=section.end_index
        if start_index > covered:
            ul_section = Section()
            ul_section.types = ["Unlabeled"]
            ul_section.filename = filename
            ul_section.start_index = covered
            ul_section.end_index = start_index
            ul_section.text = text[covered:start_index]
            gaps.append(ul_section)
        if end_index > covered:
            covered = end_index
    if end > covered:
        ul_section=Section()
        ul_section.types = ["Unlabeled"]
        ul_section.filename = filename
        ul_section.start_index = covered
        ul_section.end_index = end
        ul_section.text = text[covered:end]
        gaps.append(ul_section)
    return gaps

def link_sections(sections):
    """ Links subsections to their parent sections. """
    for section in sections:
        for other_section in sections:
            if is_subsection(section,other_section):
                section.subsumers.append(other_section)
                other_section.subsumed.append(section)
        
def is_subsection(section,other_section):
    """ Returns true if the first section is a subsection of the second. """
    if (other_section.start_index <= section.start_index and
        other_section.end_index >= section.end_index and
        len(other_section) > len(section)):
            return True

        
### Code to deal with Elsevier data
        
class SimpleElsevierSectionFactory(SectionFactory):

    def __init__(self, text_file, fact_file, sect_file):
        SectionFactory.__init__(self, text_file, fact_file, sect_file)
        self.doc = Document(text_file)
        self.sections = []
        
    def make_sections(self):
        self.text = codecs.open(self.text_file, encoding='utf-8').read()
        self.read_lines()
        self.doc.connect_lines()
        self.doc.set_doc_features()
        self.doc.mark_headers()
        self.doc.mark_header_hierarchy()
        #self.print_lines()
        
    def read_lines(self):
        line, i, max = '', 0, len(self.text)
        begin, end = i, i
        while i < max:
            char = self.text[i]
            if self.text[i] == "\n":
                l = Line(line, begin, end)
                self.doc.lines.append(l)
                line, begin, end = '', i, i
            else:
                line += char
                end += 1
            i += 1
            
    def print_lines(self):
        self.doc.print_lines()

            
class Document(object):
    """
    Class that contains the code to deal with document structure in Elsevier articles that
    do not have the extended XML structure. Contains instance variables for the lines in
    the documents and the sections. Also has variables to store document-level
    characteristics, these all start with 'f_'. """
    
    def __init__(self, filename):
        self.filename = filename
        self.lines = []
        self.sections = []
        self.f_size_in_lines = None
        self.f_size_in_characters = None
        self.f_average_line_length = None
        self.f_whiteline_ratio = None
        
    def set_doc_features(self):
        line_count = len(self.lines)
        whitelines = len([line for line in self.lines if line.length == 0])
        char_count = sum([line.length + 1 for line in self.lines])
        self.f_size_in_lines = line_count
        self.f_size_in_characters = char_count
        if line_count != 0:
            self.f_average_line_length = char_count / float(line_count)
            self.f_whiteline_ratio = whitelines / float(line_count)
        self.print_features()

    def connect_lines(self):
        """Turn the self.lines list into a linked list."""
        for i in range(len(self.lines)-1):
            line = self.lines[i]
            next_line = self.lines[i+1]
            line.next = next_line
            next_line.previous = line

    def mark_headers(self):
        for line in self.lines:
            if line.is_header():
                line.header = True

    def mark_header_hierarchy(self):
        """
        previous_header = null
        for h in header
	   if not previous_header
		previous_header = h.info()

       class header
           def info

        """
        for line in self.lines:
            if line.header == True:
                header = Header(line)
                print header
                
    def print_features(self):
        print "\nDocument Features"
        for feature in sorted([f for f in self.__dict__.keys() if f.startswith('f_')]):
            print "   %-25s %s" % (feature, self.__dict__[feature])
        print

    def print_lines(self):
        for l in self.lines:
            print l


class Line(object):
    """
    Object to represent a line in the text. It holds the following information: (1) the
    text string, (2) the begin and end offsets, (3) the length, (4) pointers to previous
    and next lines, and (5) a boolean that indicates that the line is a header, set to
    false by default. A line is a string of characters bordered by newlines, so the
    newline is not part of the line itself. """

    re_prefix = re.compile('\d\.(\d\.)?')
    
    def __init__(self, line, p1, p2):
        self.line = line
        self.begin = p1
        self.end = p2
        self.length = p2 - p1
        self.previous = None
        self.next = None
        self.header = False

    def __str__(self):
        l = self.line
        line = self.line if len(l) < 75 else "%s ... %s" % (l[:38], l[-37:])
        return "<Line %d %d %s '%s'>" % (self.begin, self.end, self.header, line)

    def is_header(self):
        if 0 < self.length < 50:
            return True
        return False

    def numbering_prefix(self):
        match = self.re_prefix.match(self.line)
        if match is not None:
            return match.group(0)
        return ''
    

class Header(Line):

    def __init__(self, line):
        for f in line.__dict__.keys():
            self.__dict__[f] = line.__dict__[f]
        prefix = line.numbering_prefix()
        self.embedding = [p for p in prefix.split('.') if p]
            
    def __str__(self):
        return "<Header %d %d [%s] '%s'>" % (self.begin, self.end, '.'.join(self.embedding), self.line)
