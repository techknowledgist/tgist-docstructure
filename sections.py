from exceptions import UserWarning


class Section(object):
    """
    Represents a semantically-typed section in a document. Should be used by all
    SectionFactories because the code to write to the output uses this class. The section
    does not include the header, but self.header does contain the string of the header, if
    there is one. """

    SECTION_ID = 0
    
    def __init__(self):
        Section.SECTION_ID += 1
        self.id = Section.SECTION_ID
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
        offsets = "%s<id=%d start=%d end=%d>%s" % (GREEN, self.id, p1, p2, END)
        types= "%s%s%s" % (BLUE, str(self.types), END)
        return "%s %s\n%s...\n" % (types, offsets, text_string)
    
    def __len__(self):
        return self.end_index - self.start_index


class SectionFactory(object):
    """
    Abstract class that contains shared code for the section factories for all data
    types. Provodes a unified interface for the code that calls the section creation
    code. Themain method called by outside code is make_sections(), which should be
    implemented on all subclasses."""
    
    def __init__(self, text_file, fact_file, sect_file, verbose=False):
        """
        The first two files are the ones that are given by the wrapper, the third is
        the file that the wrapper expects."""
        # reset the SECTION_ID class variable so that ids start at 1 for each file, this
        # is important because it makes the regression test much more robust.
        Section.SECTION_ID = 0
        self.text_file = text_file
        self.fact_file = fact_file
        self.sect_file = sect_file
        self.sections = []
        self.verbose = verbose

    def __str__(self):
        return "<%s on %s>" % (self.__class__.__name__, self.text_file[:-4])

    def make_sections(self):
        """
        Creates a list of Section instances in self.sections. Each subclass should implement
        this method. """
        raise UserWarning, "make_sections() not implemented for %s " % self.__class__.__name__

    def section_string(self, section, suppress_empty=True):
        """
        Called by print_sections. Returns a human-readable string with relevant information about
        a particular section.
        """
        sec_string = "SECTION ID=%d" % (section.id)
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
        if self.verbose and len(section.text) > 0:
            sec_string += "\n"+section.text
        if suppress_empty and len(section.text.strip()) < 1:
            return None
        return sec_string + "\n"

    def parent_claims_string(self, parent_claims):
        ret_string = str(parent_claims[0])
        for claim in parent_claims[1:]:
            ret_string += ","
            ret_string += str(claim)
        return ret_string
    
    def print_sections(self, fh):
        """
        Prints section data to a file handle.
        """
        for section in self.sections:
            try:
                fh.write(self.section_string(section))
            except TypeError:
                pass


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

