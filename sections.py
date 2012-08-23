import re
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

class ComplexElsevierSectionFactory(SectionFactory):

    def make_sections(self):
        pass
        
