import codecs, re
from exceptions import UserWarning
import med_read, pat_read, normheader


class Section(object):
    """
    Represents a semantically-typed section in a document. Should be used by all
    SectionFactories because the code to write to the output uses this class. The section
    does not include the header, but self.header does contain the string of the header, if
    there is one. """

    def __init__(self):
        self.types = []
        self.header = ""
        self.subsumers = []
        self.subsumer_types = set()
        self.subsumed = []
        self.filename = ""
        self.start_index = -1
        self.end_index = -1
        self.text = ""

    def __str__(self):
        text_string = self.text.replace("\n", '\\n').encode('utf-8')[:80]
        (p1, p2) = (self.start_index, self.end_index)
        (BLUE, GREEN, END) = ('\033[34m', '\033[32m', '\033[0m')
        offsets = "%s<%d %d>%s" % (GREEN, p1, p2, END)
        types= "%s%s%s" % (BLUE, str(self.types), END)
        return "%s %s\n%s...\n" % (types, offsets, text_string)
    
    def __len__(self):
        return self.end_index - self.start_index


class ClaimSection(Section):
    def __init__(self):
        Section.__init__(self)
        self.claim_number=-1
        self.parent_claims = []

    
class SectionFactory(object):
    """
    Abstract class that contains shared code for the section factories for all data
    types. Provodes a unified interface for the code that calls the section creation
    code. Themain method called by outside code is make_sections(), which should be
    implemented on all subclasses."""
    
    def __init__(self, text_file, fact_file, sect_file):
        """
        The first two files given are the ones that are given by the wrapper, the third is
        a file that the wrapper expects."""
        self.text_file = text_file
        self.fact_file = fact_file
        self.sect_file = sect_file
        self.sections = []

    def __str__(self):
        return "<%s on %s>" % (self.__class__.__name__, self.text_file[:-4])

    def make_sections(self):
        """
        Creates a list of Section instances in self.sections. Each subclass should implement
        this method. """
        raise UserWarning, "make_sections() not implemented for %s " % self.__class__.__name__

    def section_string(self,section,section_id=None, full_text=False):
        """
        Called by print_sections. Returns a human-readable string with relevant information about
        a particular section.
        """
        sec_string="SECTION"
        if section_id is not None:
            sec_string += " ID="+str(section_id)
        if len(section.types) > 0:
            sec_string += " TYPE=\"" + "|".join(section.types).upper() + "\""
        if len(section.header) > 0:
            sec_string += " TITLE=\"" + section.header + "\""
        if section.start_index is not -1:
            sec_string += " START=" + str(section.start_index)
        if section.end_index is not -1:
            sec_string += " END=" + str(section.end_index)
        try:
            if section.claim_number > 0:
                sec_string += " CLAIM_NUMBER=" + str(section.claim_number)
            if len(section.parent_claims) > 0:
                sec_string += " PARENT_CLAIMS=" + self.parent_claims_string(section.parent_claims)
        except AttributeError:
            pass   
        if full_text and len(section.text) > 0:
            sec_string+="\n"+section.text
        return sec_string + "\n"

    def parent_claims_string(self, parent_claims):
        ret_string=str(parent_claims[0])
        for claim in parent_claims[1:]:
            ret_string += ","
            ret_string += str(claim)
        return ret_string
    
    def print_sections(self, fh):
        """
        Prints section data to a file handle.
        """
        section_id=0
        for section in self.sections:
            section_id+=1
            fh.write(self.section_string(section,section_id))



### Code to deal with Web of Science abstracts

class WebOfScienceSectionFactory(SectionFactory):

    pass


### Code to deal with patents

class PatentSectionFactory(SectionFactory):

    def make_sections(self):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """
        
        (a_text, a_tags) = pat_read.load_data(self.text_file, self.fact_file)
        raw_sections = pat_read.headed_sections(a_tags)
        for match in raw_sections:
            section = Section()
            section.types = normheader.header_to_types(match[0].text(a_text))
            section.header = match[0].text(a_text)
            section.filename = self.text_file
            section.start_index = match[0].start_index
            section.end_index = match[1][-1].end_index
            section.text = section.header
            for paragraph in match[1]:
                section.text += "\n\n" + paragraph.text(a_text)
            self.sections.append(section)

        self.make_claims()
        self.sections.extend(section_gaps(self.sections, a_text, self.text_file))
        self.sections = sorted(self.sections, key= lambda x: x.start_index)

    
    def make_claims(self, cautious=True):
        (text, tags) = pat_read.load_data(self.text_file, self.fact_file)
        structures = filter(lambda x: x.name == "STRUCTURE", tags)
        claim_sections = []
        claims = filter(lambda x: x.name == "claim", tags)
        claims_sections = filter(lambda x: x.name == "claims", tags)
        claims_sections.extend(filter(lambda x: x.attributes["TYPE"] == "CLAIMS", structures))
        if cautious:
            assert len(claims_sections) <= 1, "Multiple claims sections in document"
        try:
            claims_section = claims_sections[0]
        except IndexError:
            return []
        claims.extend(filter(lambda x: x.attributes["TYPE"] == "TEXT"
                             and x.start_index >= claims_section.start_index
                             and x.end_index <= claims_section.end_index, structures))
        claims=sorted(claims, key = lambda x: x.start_index)
        claim_index=1
        for claim in claims:
            section = ClaimSection()
            section.types = ["claim"]
            section.filename = self.text_file
            section.start_index = claim.start_index
            section.end_index = claim.end_index
            section.text = claim.text(text)
            section.claim_number = claim_index
            claim_index += 1
            claim_refs=re.findall(r"claim \d+", section.text)
            for ref in claim_refs:
                section.parent_claims.append(int(ref.split()[-1]))
            self.sections.append(section)


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
                for sem_type in other_section.types:
                    section.subsumer_types.add(sem_type)
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
        """
        Initialize the factory by reading segment boundaries from the fact file and the
        actual segments from the text file. """
        SectionFactory.__init__(self, text_file, fact_file, sect_file)
        self.segment_boundaries = self.read_fact_file()
        self.segments = self.read_segments()
        self.sections = []

    def read_fact_file(self):
        """
        Reads the fact file and retrieves the start and end offsets of all strucutre tags
        with type TEXT. Returns a list of tuples with start and end offset for each TEXT
        segment. This is for the simple Elsevier layout where the BAE parser usually
        genrates one text structure element, but at times it will find a couple more."""
        re_STRUCTURE = re.compile("STRUCTURE TYPE=\"(\S+)\" START=(\d+) END=(\d+)")
        boundaries = []
        for line in open(self.fact_file):
            result = re_STRUCTURE.match(line)
            if result is not None:
                structure_type, start, end = result.groups()
                if structure_type == 'TEXT':
                    boundaries.append((int(start), int(end)))
        return boundaries

    def read_segments(self):
        """
        Create an ElsevierSegment for each pair of segment boundaries and return a list of
        those segments."""
        self.text = codecs.open(self.text_file, encoding='utf-8').read()
        segments = []
        for start, end in self.segment_boundaries:
            segment = ElsevierSegment(self, start, end)
            segments.append(ElsevierSegment(self, start, end))
        return segments
        
    def make_sections(self):
        for segment in self.segments:
            segment.make_sections()
            self.sections.extend(segment.sections)



class ElsevierSegment(object):
    """
    Class that contains the code to deal with document structure in Elsevier articles that
    do not have the extended XML structure. There is a Segment instance for each
    structural tag with type=TEXT in the fact file, usually just one. The segment contains
    a pointer to the factory which stores a unicode string of the entire text file. A
    segment contains instance variables for he segment text, the start and end of that
    text in the full text file, the lines in the segment and the sections. The sections
    will later be exported to the enclosing factory. Also has variables to store
    document-level characteristics, these all start with 'f_'."""
    
    def __init__(self, factory, start, end):
        self.factory = factory
        self.text = factory.text[start:end]
        self.start = start
        self.end = end
        self.lines = []     # raw lines from the file
        self.elements = []  # contains Headers and Sections
        self.sections = []  # Sections to be exportted to the factory
        self.f_lines = None
        self.f_tokens = None
        self.f_characters = None
        self.f_whitelines = None
        self.f_average_line_length = None
        self.f_whiteline_ratio1 = None
        self.f_whiteline_ratio2 = None
        
    def __str__(self):
        return "<Segment file=%s start=%d end=%d" \
            % (self.factory.text_file, self.start, self.end)

    def __len__(self):
        return self.end - self.start

    def make_sections(self):
        self._read_lines()
        self._set_features()
        self._characterize_lines()
        self._create_headers_and_sections()
        self._merge_elements()
        self._add_headers_to_sections()
        self._transfer_sections()
        #self.print_features()
        #print_list(self.lines)
        #print_list(self.elements)

    def _read_lines(self):
        line, i, max = '', 0, len(self)
        begin, end = i, i
        self.lines = []
        while i < max:
            char = self.text[i]
            if self.text[i] == "\n":
                l = ElsevierLine(line, begin, end)
                self.lines.append(l)
                line, begin, end = '', i, i
            else:
                line += char
                end += 1
            i += 1
        connect(self.lines)
            
    def _characterize_lines(self):
        """Ask all lines to analyze themselves."""
        for line in self.lines:
            line.characterize()

    def _set_features(self):
        """Set some segment level features. This is where a lot of magic variables live."""
        line_count = len(self.lines)
        whitelines = len([line for line in self.lines if line.length == 0])
        char_count = sum([line.length + 1 for line in self.lines])
        self.f_lines = line_count
        self.f_whitelines = whitelines
        self.f_tokens = len(self.text.split())
        self.f_characters = char_count
        if line_count != 0:
            self.f_average_line_length = char_count / float(line_count)
            self.f_whiteline_ratio1 = whitelines / float(line_count)
            self.f_whiteline_ratio2 = self.f_whiteline_ratio1
            if self.f_average_line_length > 80:
                # change the adjusted ratio when paragraphs are just one line
                adjusted_lines = (line_count * (self.f_average_line_length / 80))
                self.f_whiteline_ratio2 = whitelines / float(adjusted_lines)
        self.f_spaceous = True if self.f_whiteline_ratio2 > 0.1 else False

    def _create_headers_and_sections(self):
        """
        Loop through all lines, mark those that are headers, then build header and section
        objects and put them in self.sections. Note that after this method has applied,
        the content of self.section is not yet what is expected by the factory."""
        def replace_line(line):
            return ElsevierHeader(line) if line.header else ElsevierSection(line)
        for line in self.lines:
            if line.is_header(self.f_spaceous):
                line.mark_as_header()
        self.elements = [replace_line(l) for l in self.lines]
        connect(self.elements)

    def _merge_elements(self):
        """
        If there is a continuous sequence of more then one section in the elements list,
        merge them into one section with all the lines and updated end offset."""
        for element in reversed(self.elements):
            element.delete = False
            if not element.is_section():
                continue
            if element.previous is not None and element.previous.is_section():
                element.previous.add_section(element)
                element.delete = True
        self.elements = [s for s in self.elements if not s.delete]

    def _add_headers_to_sections(self):
        """
        Loops through self.elements and keeps a stack of the current headers, using the
        level atrribute on the headers, and assigns the current stack of headers to each
        section in the list."""
        headers = []
        level = 0
        for e in self.elements:
            if e.is_header():
                headers = headers[:e.level - 1]
                headers.append(e)
                level = e.level
            elif e.is_section():
                e.headers = headers
                
    def _transfer_sections(self):
        """
        Take all the elements that are ElsevierSections, turn them into instances of
        Section, and put them on the self.sections list."""
        for e in self.elements:
            if e.is_section():
                section = e.generalize()
                self.sections.append(section)

    def print_features(self):
        print "\nSegment Features"
        for feature in sorted([f for f in self.__dict__.keys() if f.startswith('f_')]):
            print "   %-25s %s" % (feature, self.__dict__[feature])
        print


        
class ElsevierLine(object):
    """
    Object to represent a line in the text. It holds the following information: (1) the
    text string, (2) the begin and end offsets, (3) the length, (4) pointers to previous
    and next lines, and (5) a boolean that indicates that the line is a header, set to
    false by default. A line is a string of characters bordered by newlines, so the
    newline is not part of the line itself. """

    # WISH LIST
    #
    # - Should add a few more segment level properties, for example whether the document
    #   uses what looks like numbering on the headers, if this is set to True, then you
    #   need a bit more evidence to promote a line to a segment, for example you could
    #   only allow References and Acknowledgements as section headers without a number.
    #
    # - Have not yet done anything significant with the embedding.
    #
    # - Lines are now marked as headers and have types, but I have not yet added the code
    # - to transfer this to the sections themselves.
    
    re_prefix = re.compile('\d\.(\d\.)?')
    
    def __init__(self, line, p1, p2):
        self.line = line
        self.begin = p1
        self.end = p2
        self.length = p2 - p1
        self.previous = None
        self.next = None
        self.header = False
        self.header_type = None
        self.header_number = None
        self.header_level = None
        
    def __str__(self):
        l = self.line
        chars = 40 # number of characters to print from the line
        header = "%5d %5d " % (self.begin, self.end)
        level = self.header_level if self.header_level else ' ' 
        character = "header=%d %s  (%s)" % (self.header, level, self.characteristics())
        line = self.line if len(l) < chars else "%s ... %s" % (l[:chars/2], l[-chars/2:])        
        return "%s %-40s '%s'" % (header, character, line)

    def characterize(self):
        """
        Collect some general characteristics about the line, like wheter it is long or
        short, has a number and whether it is an orphan. Store this in instance variables
        starting with 'is_' or 'has_'."""
        self.is_numbered = False           # has number prefix
        self.is_short = False              # is shorter than 50 characters
        self.is_long = False               # is longer than 100 characters
        self.is_orphan = False             # surrounded by empty lines
        self.is_empty = False              # is an empty line
        self.has_empty_line_above = False  # line above is empty or None
        self.has_empty_line_below = False  # line below is empty or None
        self._do_i_start_with_a_number()
        self._am_i_surrounced_by_whitelines()
        self._am_i_long_or_short()

    def _do_i_start_with_a_number(self):
        prefix = self.numbering_prefix()
        if prefix:
            self.is_numbered = True
            self.header_number = prefix
            self.header_level = len([n for n in prefix.split('.') if n])

    def _am_i_surrounced_by_whitelines(self):
        if self.previous is None or self.previous.line.strip() == '':
            self.has_empty_line_above = True 
        if self.next is None or self.next.line.strip() == '':
            self.has_empty_line_below = True 
        if self.has_empty_line_above and self.has_empty_line_below:
            self.is_orphan = True

    def _am_i_long_or_short(self):
        if self.line.strip() == '':
            self.is_empty = True
        if self.length < 50:
            self.is_short = True
        if self.length > 100:
            self.is_long = True

    def characteristics(self):
        character = []
        if self.is_numbered: character.append('number')
        if self.is_short: character.append('short')
        if self.is_long: character.append('long')
        if self.is_empty: character.append('empty')
        if self.is_orphan:
            character.append('orphan')
        else:
            if self.has_empty_line_above: character.append('empty_above')
            if self.has_empty_line_below: character.append('empty_below')
        return ' '.join(character)#"%s%s%s" % (number, short, tall)


    def is_header(self, spaceous):
        """
        Return True if the line is a header, return False otherwise. The answer depends on
        local characteristics of the line, but takes as a parameter the spaceousness of
        the file, which is derived from the whiteline ratio of the file, which is a
        normalized measure of how many white lines the file has. This measure is motivated
        by the fact that there seem to be two kinds of simple Elsevier files, one with
        many white lines, where the headers are always orphans, and one with less white
        lines, where the headers are not followed by an empty line."""

        # abbreviations
        numbered = self.is_numbered
        short = self.is_short
        long = self.is_long
        empty = self.is_empty
        orphan = self.is_orphan
        empty_line_above = self.has_empty_line_above
        empty_line_below = self.has_empty_line_below

        # The following cases form a kind of decision tree, the clearest cases are first,
        # but it gets more murky going down the line. Cases are not mutually exclusive
        if numbered and short and orphan:
            return True
        if numbered and short and empty_line_above and not spaceous:
            return True
        if empty:
            return False
        if short and empty_line_above and not spaceous:
            return True

        # default is for a line to not be a header
        return False


    def numbering_prefix(self):
        match = self.re_prefix.match(self.line)
        if match is not None:
            return match.group(0)
        return ''

    def mark_as_header(self):
        """
        Marks the line as a header. Note that when this runs, some header informations,
        like the level and the prefix, may have already been set by one of the methods
        that are part of the characterization functionality. This is not very intuitive
        and may need to change."""
        self.header = True
        if self.header_level is None:
            self.header_level = 1
        self.header_type = normheader.header_to_types(self.line)


class ElsevierSegmentElement(object):

    def is_section(self): return False
    def is_header(self): return False
    def add_type(self): pass

    
    
class ElsevierHeader(ElsevierSegmentElement):
    
    """
    An ElsevierHeader contains an ElsevierLine, but also copies some of its attributes to
    the top level."""
    
    def __init__(self, line):
        self.line = line
        self.begin = line.begin
        self.end = line.end
        self.types = line.header_type
        self.level = line.header_level

    def __str__(self):
        return "Header%d %d %d  '%s'" % (self.level, self.begin, self.end, self.line.line)

    def is_header(self):
        return True



class ElsevierSection(ElsevierSegmentElement):

    """An ElsevierSection starts off as one ElsevierLine."""

    def __init__(self, line):
        self.lines = [line]
        self.begin = line.begin
        self.end = line.end
        self.headers = []

    def __str__(self):
        return "Section %d %d  '%s'" % (self.begin, self.end, self.lines[0].line[:80])
    
    def is_section(self):
        return True

    def add_section(self, section):
        """Add the data from the following section to self, adding to the self.lines list and
        changing the end offset."""
        self.end = section.end
        self.lines.extend(section.lines)

    def generalize(self):
        """Create a Section instance using local information adn return it."""
        section = Section()
        section.start_index = self.begin
        section.end_index = self.end
        section.text = "\n".join([l.line for l in self.lines])
        for header in self.headers:
            for type in header.types:
                section.types.append(type)
        if not section.types:
            section.types = ["Unlabeled"]
        return section

    def add_type(self):
        if self.previous is not None and self.previous.is_header():
            print self.previous.types
            self.headers.extend(self.previous.types)


    
class ComplexElsevierSectionFactory(SectionFactory):

    def make_sections(self):
        pass
        


def connect(objects):
    """Turn the objects list into a linked list."""
    for i in range(len(objects)-1):
        obj = objects[i]
        next_obj = objects[i+1]
        obj.next = next_obj
        next_obj.previous = obj
    if objects:
        # just to make sure that there is a previous and next on each object
        objects[0].previous = None
        objects[-1].next = None

        
def print_list(objects):
    for obj in objects: print obj
    print
        
