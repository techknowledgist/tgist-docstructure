import else_read, sections, normheader


class ComplexElsevierSectionFactory(sections.SectionFactory):


    def make_sections(self,separate_headers=True):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """

        (a_text, a_tags) = else_read.load_data(self.text_file, self.fact_file)
        raw_sections = else_read.headed_sections(a_tags, separate_headers=True)
        text_sections = filter(lambda x: type(x) == tuple, raw_sections)
        header_sections = filter(lambda x: type(x) != tuple, raw_sections)
        abstracts = else_read.find_abstracts(a_tags)
        
        for match in text_sections:
            section = sections.Section()
            section.types = normheader.header_to_types(match[0].text(a_text))
            section.header = match[0].text(a_text)
            section.filename = self.text_file
            section.start_index = match[1][0].start_index
            section.end_index = match[1][-1].end_index
            if separate_headers:
                section.text = ""
            else:
                section.text = section.header
            for paragraph in match[1]:
                section.text += "\n\n" + paragraph.text(a_text)
            self.sections.append(section)

        for header in header_sections:
            section = sections.Section()
            section.types = ["Header"]
            section.filename = self.text_file
            section.start_index = header.start_index
            section.end_index = header.end_index
            section.text = header.text(a_text)
            self.sections.append(section)

        for abstract in abstracts:
            section = sections.Section()
            section.types = ["Abstract"]
            section.filename = self.text_file
            section.start_index = abstract.start_index
            section.end_index = abstract.end_index
            section.text = abstract.text(a_text)
            self.sections.append(section)
            
        self.sections.extend(section_gaps(self.sections, a_text, self.text_file))
        link_sections(self.sections)
        self.sections = sorted(self.sections, key= lambda x: x.start_index)

def section_gaps(labeled_sections, text, filename=""):
    """
    Finds the unlabeled sections in a text and labels them "Unlabeled". """
    
    gaps = []
    end = len(text)
    labeled_sections = sorted(labeled_sections, key= lambda x: x.start_index)
    covered = 0
    for section in labeled_sections:
        start_index = section.start_index
        end_index=section.end_index
        if start_index > covered:
            ul_section = sections.Section()
            ul_section.types = ["Unlabeled"]
            ul_section.filename = filename
            ul_section.start_index = covered
            ul_section.end_index = start_index
            ul_section.text = text[covered:start_index]
            gaps.append(ul_section)
        if end_index > covered:
            covered = end_index
    if end > covered:
        ul_section=sections.Section()
        ul_section.types = ["Unlabeled"]
        ul_section.filename = filename
        ul_section.start_index = covered
        ul_section.end_index = end
        ul_section.text = text[covered:end]
        gaps.append(ul_section)
    return gaps

def link_sections(labeled_sections):
    """ Links subsections to their parent sections. """
    for section in labeled_sections:
        for other_section in labeled_sections:
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
