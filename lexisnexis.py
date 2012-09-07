import re
import normheader
import readers.lexisnexis
from sections import Section, SectionFactory, section_gaps


class ClaimSection(Section):

    def __init__(self):
        Section.__init__(self)
        self.claim_number = -1
        self.parent_claims = []
    

class PatentSectionFactory(SectionFactory):

    def make_sections(self, separate_headers=True):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """
        
        (a_text, a_tags) = readers.lexisnexis.load_data(self.text_file, self.fact_file)
        #for t in a_tags: print t
        raw_sections = readers.lexisnexis.headed_sections(a_tags)
        #print
        #for s in raw_sections: print s[0], s[1][0]
        #print raw_sections
        text_sections = filter(lambda x: type(x) == tuple, raw_sections)
        header_sections = filter(lambda x: type(x) != tuple, raw_sections)
        
        for match in text_sections:
            section = Section()
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
                

        self.make_claims()
        self.sections.extend(section_gaps(self.sections, a_text, self.text_file))
        self.sections = sorted(self.sections, key= lambda x: x.start_index)

    
    def make_claims(self, cautious=True):
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

