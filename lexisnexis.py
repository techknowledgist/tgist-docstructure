import re
import normheader
import readers.lexisnexis
from sections import Section, SectionFactory, section_gaps, make_section
from utils.misc import connect


class ClaimSection(Section):

    def __init__(self):
        Section.__init__(self)
        self.claim_number = -1
        self.parent_claims = []
    

class PatentSectionFactory(SectionFactory):

    def make_sections(self, separate_headers=True):
        return self.make_sections_NEW(separate_headers=True)


    def make_sections_OLD(self, separate_headers=True):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """
        
        (a_text, a_tags) = readers.lexisnexis.load_data(self.text_file, self.fact_file)
        raw_sections = readers.lexisnexis.headed_sections(a_tags)
        text_sections = filter(lambda x: type(x) == tuple, raw_sections)
        header_sections = filter(lambda x: type(x) != tuple, raw_sections)

        for match in text_sections:
            section = Section()
            print '>>>', match[0], match[0].text(a_text)
            section.types = normheader.header_to_types(match[0].text(a_text))
            section.header = match[0].text(a_text)
            section.filename = self.text_file
            if separate_headers:
                section.start_index = match[1][0].start_index
            else:
                section.start_index = match[0].start_index
            section.end_index = match[1][-1].end_index
            if separate_headers:
                section.text = ""
            else:
                section.text = section.header
            for paragraph in match[1]:
                section.text += "\n\n" + paragraph.text(a_text)
            self.sections.append(section)
            if separate_headers:
                head_section = Section()
                head_section.types = ["Header"]
                head_section.filename = self.text_file
                head_section.start_index = match[0].start_index
                head_section.end_index = match[0].end_index
                head_section.text = section.header
                self.sections.append(head_section)

        self.make_claims_OLD()
        self.sections.extend(section_gaps(self.sections, a_text, self.text_file))
        self.sections = sorted(self.sections, key= lambda x: x.start_index)

        
    def make_claims_OLD(self, cautious=True):
        (text, tags) = readers.lexisnexis.load_data(self.text_file, self.fact_file)
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
        claims = sorted(claims, key = lambda x: x.start_index)

        claim_index = 1
        for claim in claims:
            section = ClaimSection()
            section.types = ["claim"]
            section.filename = self.text_file
            section.start_index = claim.start_index
            section.end_index = claim.end_index
            section.text = claim.text(text)
            section.claim_number = claim_index
            claim_index += 1
            claim_refs = re.findall(r"claim \d+", section.text)
            for ref in claim_refs:
                section.parent_claims.append(int(ref.split()[-1]))
            self.sections.append(section)



    def make_sections_NEW(self, separate_headers=True):

        (text, tags) = readers.lexisnexis.read_tags(self.text_file, self.fact_file)

        self.add_basic_sections(text, tags)
        self.add_description_sections(text, tags)
        self.add_claims(text, tags['claims'])
        self.sections.extend(section_gaps(self.sections, text))

        # sort and link
        self.sections.sort(key= lambda x: x.start_index)
        link_sections(self.sections)
        connect(self.sections)
        #print_tags(text, tags)
        #self.print_hierarchy()

        for section in self.sections:
            if section.is_header():
                section_types = normheader.header_to_types(section.text)
                header_title = section.text
                parents = sorted([ss.start_index for ss in section.subsumers])
                current = section
                while True:
                    next = current.next
                    if next is None: break
                    if next.is_header(): break
                    next_parents = sorted([s.start_index for s in next.subsumers])
                    if parents == next_parents and next.types == ['Other']: 
                       next.types = section_types
                       next.header = header_title
                    current = next


    def add_basic_sections(self, text, tags):
        abstract = tags['abstracts'][0] if tags['abstracts'] else None
        description = tags['sections'][0] if tags['sections'] else None
        summary = tags['summaries'][0] if tags['summaries'] else None
        claims = tags['claims_sections'][0] if tags['claims_sections'] else None
        for section in [
            make_section(self.text_file, abstract, text, 'Abstract'),
            make_section(self.text_file, description, text, 'Description'),
            make_section(self.text_file, summary, text, 'Summary'),
            make_section(self.text_file, claims, text, 'Claims') ]:
            if section is not None:
                self.sections.append(section)

    def add_description_sections(self, text, tags):
        description = tags['sections'][0] if tags['sections'] else None
        (p1, p2) = (description.start_index, description.end_index) if description else (0, 0)
        headers = [t for t in tags['headers'] if t.is_contained_in(p1, p2)]
        paragraphs = [t for t in tags['paragraphs'] if t.is_contained_in(p1, p2)]
        for h in headers:
            self.sections.append(make_section(self.text_file, h, text, 'Header'))
        for p in paragraphs:
            self.sections.append(make_section(self.text_file, p, text, 'Other'))
            
    def add_claims(self, text, claims, cautious=True):
        claim_index = 1
        for claim in claims:
            section = ClaimSection()
            section.types = ["claim"]
            section.filename = self.text_file
            section.start_index = claim.start_index
            section.end_index = claim.end_index
            section.text = claim.text(text)
            section.claim_number = claim_index
            claim_index += 1
            claim_refs = re.findall(r"claim \d+", section.text)
            for ref in claim_refs:
                section.parent_claims.append(int(ref.split()[-1]))
            self.sections.append(section)

    def percolate_down(self):
        """Percolate types down the tree. Might be useful, but is not used now."""
        for s in self.sections:
            if s.types == ['Claims']:
                continue
            if not s.subsumers:
                for sub in s.subsumed:
                    sub.percolate_types(s.types)


def print_tags(text, tags):
    for name, l in tags.items():
        print name
        for t in l:
            title = '"' + text[t.start_index:t.end_index] + '"' if name == 'headers' else ''
            print "   %s %s" % (t, title)



### the following two are copied from pubmed.py
### maybe move these to section.py if they are not changed

### comment changed
def link_sections(sections):
    """ Links sections where one is subsuming the other. This does not quite build a tree."""
    for section in sections:
        for other_section in sections:
            if is_subsection(section, other_section):
                section.subsumers.append(other_section)
                for sem_type in other_section.types:
                    section.subsumer_types.add(sem_type)
                other_section.subsumed.append(section)
    # make sure that the subsumers are ordered so that the parent is always the last in
    # the list, this is also where the parent_id gets set
    for section in sections:
        section.subsumers.sort(key= lambda x: x.start_index)
        if section.subsumers:
            section.parent_id = section.subsumers[-1].id
            
### this one was altered (just the comment)
def is_subsection(section, other_section):
    """ Returns true if the first section is included in the second. This is not quite the
    same as subsection, rather, it implements dominance since inclusion could be way down
    the tree."""
    if (other_section.start_index <= section.start_index and
        other_section.end_index >= section.end_index and
        len(other_section) > len(section)):
            return True
