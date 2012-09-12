"""

Source reading code for Elsevier structured documents.

"""
    

import shlex, codecs
from common import load_data, load_articles


class Tag():

    # TODO: should really use common.Tag, but the differences are big enough to hold off
    # on that for now.
    
    def __init__(self,text):
        try:
            split_text=shlex.split(text)
        except ValueError:
            split_text=text.split()
        try:
            self.start_index = int(split_text[0])
            self.end_index = int(split_text[1])
            self.name = split_text[2]
            self.attributes = split_text[3:]
        except IndexError:
            # not enough stuff, assume this is a malformed tag
            self.start_index = None
            self.end_index = None
            self.name = None
            self.attributes = None
        except ValueError:
            # guess that this is in the second format
            self.name = split_text[0]
            try:
                split_text = dict(map(lambda x: str.split(x, "=", 1), split_text[1:]))
            except ValueError:
                #whoops this was malformed after all
                self.start_index = None
                self.end_index = None
                self.name = None
                self.attributes = None
                return
            try:
                self.start_index = int(split_text["START"])
            except (KeyError,ValueError):
                self.start_index=-1
            try:
                self.end_index = int(split_text["END"])
            except (KeyError,ValueError):
                self.end_index=-1
            self.attributes=split_text
            

    def __str__(self):
        return "[%d %d %s]" % (self.start_index, self.end_index, self.name)
            
    def __len__(self):
        return self.end_index-self.start_index

    def text(self,doc):
        return doc[self.start_index:self.end_index]

    

def headed_sections(tags, max_title_lead=30, separate_headers=True):
    """
    max_title_lead controls how far the title's end can be from the section's beginning
    for it to still count as that section's header. separate_headers controls whether
    or not headers are treated as section objects in their own right, or simply have
    their text subsumed in the section.
    """
    
    structures = filter(lambda x: x.name == "STRUCTURE", tags)
    title_structures = filter(lambda x: x.attributes["TYPE"] == "TITLE", structures)
    text_structures = filter(lambda x: x.attributes["TYPE"][:4] == "TEXT", structures)

    
    matches = []
    header_matches=[]
    
    title_structures = sorted(title_structures, key=lambda x: x.start_index)
    text_structures = sorted(text_structures, key=lambda x: x.start_index)

    """OK so guesswork on what paragraphs go to what header.  We assume that if there is a period
    of unlabeled text in among labeled text it really should have gone with the previous label.
    Unlabeled text at the beginning and end is assumed to be properly unlabeled."""
    
    for index in range(len(title_structures)-1):
        title = title_structures[index]
        next_title = title_structures[index+1]
        titled_paras =[]
        for text_structure in text_structures:
            if (title.end_index < text_structure.start_index
                and text_structure.end_index < next_title.start_index):
                immediate_follower=False
                if text_structure.start_index - title.end_index < max_title_lead and len(titled_paras) < 1:
                    immediate_follower=True
                if separate_headers and immediate_follower:
                    header_matches.append(title)
                elif immediate_follower:
                    text_structure.start_index = title.start_index
                if immediate_follower or len(titled_paras) > 0:
                    titled_paras.append(text_structure)
        if len(titled_paras) > 0:
            matches.append((title, titled_paras))
    matches.extend(header_matches)
    return matches

def find_abstracts(tags):
    structures = filter(lambda x: x.name == "STRUCTURE", tags)
    return filter(lambda x: x.attributes["TYPE"] == "ABSTRACT", structures)


