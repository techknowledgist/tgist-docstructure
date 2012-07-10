import normheader

class Section():
    """
    Represents a semantically-typed section in a document.
    """
    def __init__(self):
        self.types=[]
        self.header=""
        self.subsumers=[]
        self.subsumed=[]
        self.filename=""
        self.start_index=-1
        self.end_index=-1
        self.text=""

    def __repr__(self):
        return str(self.types) + "\n" + self.text
    
    def __len__(self):
        return self.end_index-self.start_index

def make_sections(raw_sections, abstracts, a_text,filename=""):
    """
    Given a list of headertag/sectiontag pairs, a list of abstract tags,
    and the raw text of the article, converts them into a list of semantically
    typed sections.
    """
    sections=[]
    for match in raw_sections:
        section=Section()
        section.types=normheader.header_to_types(match[0].text(a_text))
        section.header=match[0].text(a_text)
        section.filename=filename
        section.start_index=match[1].start_index
        section.end_index=match[1].end_index
        section.text=match[1].text(a_text)
        sections.append(section)
    for abstract in abstracts:
        section=Section()
        section.types=["Abstract"]
        section.filename=filename
        section.start_index=abstract.start_index
        section.end_index=abstract.end_index
        section.text=abstract.text(a_text)
        sections.append(section)
    sections.extend(section_gaps(sections,a_text,filename))
    link_sections(sections)
    return sections

def section_gaps(sections,text,filename=""):
    """
    Finds the unlabeled sections in a text and labels them "Unlabeled".
    """
    gaps=[]
    end=len(text)
    sections=sorted(sections, key= lambda x: x.start_index)
    covered=0
    for section in sections:
        start_index=section.start_index
        end_index=section.end_index
        if start_index > covered:
            ul_section=Section()
            ul_section.types=["Unlabeled"]
            ul_section.filename=filename
            ul_section.start_index=covered
            ul_section.end_index=start_index
            ul_section.text=text[covered:start_index]
            gaps.append(ul_section)
        if end_index > covered:
            covered=end_index
    if end > covered:
        ul_section=Section()
        ul_section.types=["Unlabeled"]
        ul_section.filename=filename
        ul_section.start_index=covered
        ul_section.end_index=end
        ul_section.text=text[covered:end]
        gaps.append(ul_section)
    return gaps

def link_sections(sections):
    """
    Links subsections to their parent sections.  There might be efficiency
    issues with this code.
    """
    for section in sections:
        for other_section in sections:
            if is_subsection(section,other_section):
                section.subsumers.append(other_section)
            if is_subsection(other_section,section):
                section.subsumed.append(other_section)
        
def is_subsection(section,other_section):
    """
    Returns true if the first section is a subsection of the second.
    """
    if (other_section.start_index<=section.start_index and
        other_section.end_index>=section.end_index and
        len(other_section)>len(section)):
            return True
