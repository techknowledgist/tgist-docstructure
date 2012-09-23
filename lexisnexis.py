import re
import normheader
from readers.lexisnexis import read_tags
from sections import Section, SectionFactory, section_gaps, make_section, link_sections
from utils.misc import connect


class ClaimSection(Section):

    def __init__(self):
        Section.__init__(self)
        self.claim_number = -1
        self.parent_claims = []
    

class PatentSectionFactory(SectionFactory):

    def make_sections(self, separate_headers=True):

        (text, tags) = read_tags(self.text_file, self.fact_file, self.fact_type)

        self.add_meta_sections(text, tags)
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
                    if next.types == ['Claims']: break
                    next_parents = sorted([s.start_index for s in next.subsumers])
                    if parents == next_parents and next.types == ['Other']: 
                        next.types = section_types
                        next.header = header_title
                    current = next

    def add_meta_sections(self, text, tags):
        for t in tags.get('meta_tags',[]):
            if t.name == 'date':
                section = make_section(self.text_file, t, text, 'Meta-Date')
                self.sections.append(section)
            if t.name == 'invention-title':
                section = make_section(self.text_file, t, text, 'Meta-Title')
                self.sections.append(section)
        
    def add_basic_sections(self, text, tags):
        description = tags['sections'][0] if tags['sections'] else None
        summary = tags['summaries'][0] if tags['summaries'] else None
        claims = tags['claims_sections'][0] if tags['claims_sections'] else None
        # TODO: Chinese and German patents have two abstracts, and each has a language
        # feature (lang="chi"), maybe add this feature (would need a add a dictionary
        # feature to make_section)
        for a in tags['abstracts']:
            self.sections.append(make_section(self.text_file, a, text, 'Abstract'))
        for section in [
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
        if self.language == 'CHINESE':
            # TODO: this should be refactored, the differences between languages should
            # not be hidden in the code, but be visible from the outside in module names
            for tf in tags['technical-field']:
                self.sections.append(make_section(self.text_file, tf, text, 'Technical_Field'))
            for tf in tags['background-art']:
                self.sections.append(make_section(self.text_file, tf, text, 'Background_Art'))
        if self.language == 'GERMAN':
            # TODO: split paragraphs where each line has a prefix like [0014]
            pass
        
    def add_rest_section(self, text, tags):
        """Adds a section that is the difference of the Description section and the
        Summary section in thre. This is needed for analysis of patents, but is not used
        here since this should really be elsewhere."""
        description = tags['sections'][0] if tags['sections'] else None
        summary = tags['summaries'][0] if tags['summaries'] else None
        if description and summary:
            rest_section = Section()
            rest_section.start_index = summary.end_index
            rest_section.end_index = description.end_index
            rest_section.text = text[rest_section.start_index:rest_section.end_index]
            rest_section.types = ['Description_Rest']
            self.sections.append(rest_section)
            
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
            # somehow the former caused problems for the default standoff data
            title = "['%s']" % text[t.start_index-1:t.end_index] if name == 'headers' else ''
            title = text[t.start_index:t.end_index] if name == 'headers' else ''
            print "   %s %s" % (t, title)
