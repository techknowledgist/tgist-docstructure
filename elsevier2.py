import sections, normheader
import readers.elsevier2
from sections import Section, SectionFactory, section_gaps, link_sections


class ComplexElsevierSectionFactory(SectionFactory):


    def make_sections(self, separate_headers=True):
        """
        Given a list of headertag/sectiontag pairs, a list of abstract tags, and the raw text
        of the article, converts them into a list of semantically typed sections. """

        (a_text, a_tags) = readers.elsevier2.load_data(self.text_file, self.fact_file)
        raw_sections = readers.elsevier2.headed_sections(a_tags, len(a_text), separate_headers=True)
        text_sections = filter(lambda x: type(x) == tuple, raw_sections)
        header_sections = filter(lambda x: type(x) != tuple, raw_sections)
        abstracts = readers.elsevier2.find_abstracts(a_tags)
        
        for match in text_sections:
            section = Section()
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
            section = Section()
            section.types = ["Header"]
            section.filename = self.text_file
            section.start_index = header.start_index
            section.end_index = header.end_index
            section.text = header.text(a_text)
            self.sections.append(section)

        #Sometimes abstracts are tagged one way, sometimes another way, sometimes both at once.
        #We need to eliminate double-counting.
        abstract_sections = filter(lambda x: "Abstract" in x.types, self.sections)

        for abstract in abstracts:
            for abs_sec in abstract_sections:
                if ((abs_sec.start_index < abstract.start_index and abs_sec.end_index > abstract.start_index)
                    or (abs_sec.start_index > abstract.start_index and abs_sec.start_index < abstract.end_index)):
                    already_here=True
                    break
            if not already_here:
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

        
def section_gaps(labeled_sections, text, filename=""):
    """
    Finds the unlabeled sections in a text and labels them "Unlabeled". """
    
    gaps = []
    end = len(text)
    labeled_sections = sorted(labeled_sections, key= lambda x: x.start_index)
    covered = 0
    for section in labeled_sections:
        start_index = section.start_index
        end_index = section.end_index
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
        ul_section = Section()
        ul_section.types = ["Unlabeled"]
        ul_section.filename = filename
        ul_section.start_index = covered
        ul_section.end_index = end
        ul_section.text = text[covered:end]
        gaps.append(ul_section)
    return gaps

