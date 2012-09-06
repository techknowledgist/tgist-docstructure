import med_read, normheader
from sections import Section, SectionFactory, section_gaps

class BiomedNxmlSectionFactory(SectionFactory):


    def make_sections(self):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """

        (a_text, a_tags) = med_read.load_data(self.text_file, self.fact_file)
        raw_sections = med_read.headed_sections(a_tags, separate_headers=True)
        text_sections = filter(lambda x: type(x) == tuple, raw_sections)
        header_sections = filter(lambda x: type(x) != tuple, raw_sections)
        abstracts = med_read.find_abstracts(a_tags)
        
        for match in text_sections:
            section = Section()
            section.types = normheader.header_to_types(match[0].text(a_text))
            section.header = match[0].text(a_text)
            section.filename = self.text_file
            section.start_index = match[1].start_index
            section.end_index = match[1].end_index
            section.text = match[1].text(a_text)
            self.sections.append(section)

        for header in header_sections:
            section = Section()
            section.types = ["Header"]
            section.filename = self.text_file
            section.start_index = header.start_index
            section.end_index = header.end_index
            section.text = header.text(a_text)
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



