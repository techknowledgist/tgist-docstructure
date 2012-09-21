import codecs, re
from sections import Section, SectionFactory



class WebOfScienceSectionFactory(SectionFactory):


    def __init__(self, text_file, fact_file, sect_file, fact_type, verbose=False):

        SectionFactory.__init__(self, text_file, fact_file, sect_file, fact_type)
        self.sections = []
        self.text = codecs.open(self.text_file, encoding='utf-8').read()

    def make_sections(self):
        
        re_STRUCTURE = re.compile("STRUCTURE TYPE=\"ABSTRACT\" START=(\d+) END=(\d+)")
        for line in open(self.fact_file):
            result = re_STRUCTURE.match(line)
            if result is not None:
                start, end = result.groups()
                section = Section()
                section.start_index = int(start)
                section.end_index = int(end)
                section.text = self.text[section.start_index:section.end_index]
                section.types.append('ABSTRACT')
                self.sections.append(section)
