import shlex, codecs
from common import Tag, load_data, find_abstracts
from common import tags_with_name, tags_with_type, tags_with_matching_type

    
def headed_sections(tags, max_title_lead=30, separate_headers=True):
    """
    max_title_lead controls how far the title's end can be from the section's beginning
    for it to still count as that section's header. separate_headers controls whether
    or not headers are treated as section objects in their own right, or simply have
    their text subsumed in the section.
    """
    
    headers = tags_with_name(tags, "title")
    sections = tags_with_name(tags, "sec")
    structures = tags_with_name(tags, "STRUCTURE")
    title_structures = tags_with_type(structures, "TITLE")
    text_structures = tags_with_matching_type(structures, "TEXT", 0, 4)
    #print len(headers), len(sections), len(structures), len(title_structures), len(text_structures)
    
    matches = []
    header_matches = []
    for header in headers:
        for section in sections:
            if (header.start_index == section.start_index):
                if separate_headers:
                    section.start_index = header.end_index + 1
                    header_matches.append(header)
                matches.append((header, section))
                break
    for title in title_structures:
        for text_structure in text_structures:
            if (title.end_index < text_structure.start_index
                and text_structure.start_index - title.end_index < max_title_lead):
                if separate_headers:
                    header_matches.append(title)
                else:
                    text_structure.start_index = title.start_index
                matches.append((title, text_structure))
                break
    matches.extend(header_matches)
    return matches
