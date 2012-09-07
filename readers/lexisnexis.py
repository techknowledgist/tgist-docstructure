"""
*****GOALS*****

1. Recognize the claims section, as well as the numbered list of claims

 2. In addition, for each claim there needs to be a pointer to the parent claim.
 Many claims start with text like "The method of claim 9 wherein" or "The system
 of claim 1 wherein". There is probably a limited vocabulary here so it should
 not be hard to find these.

 3. Recognize (and type) example sections as well as sections "Field of
 Invention", "Background of Invention", "Summary", "Description". For some we
 already have types, for others we do not. This does bring up the question on
 whether we should have a distinction between general types and types for
 certain domains or section generator types. For now we do not need to worry
 here, but we should keep it in the back of our minds.

"""

from common import Tag, load_data

    
def headed_sections(tags, cautious=False):

    structures = filter(lambda x: x.name == "STRUCTURE", tags)
    title_structures = filter(lambda x: x.attributes["TYPE"] == "SECTITLE", structures)
    text_structures = filter(lambda x: x.attributes["TYPE"] == "TEXT", structures)
    text_chunks = filter(lambda x: x.attributes["TYPE"] == "TEXT_CHUNK", structures)
    headers = filter(lambda x: x.name == "heading", tags)
    headers.extend(title_structures)
    paragraphs = filter(lambda x: x.name == "p", tags)
    paragraphs.extend(text_structures)
    descriptions = filter(lambda x: x.name == "description", tags)
    descriptions.extend(text_chunks) 
    try:
        description = descriptions[0] #first text_chunk guaranteed description?
    except IndexError:
        return []
    matches = []
    desc_start = description.start_index
    desc_end = description.end_index
    headers = sorted(headers, key = lambda x: x.start_index)
    for index in range(len(headers)):
        header = headers[index]
        head_start = header.start_index
        if index < len(headers) - 1: #we're not at the last header
            head_end = headers[index+1].start_index - 1
        else:
            head_end = desc_end
        headed_paragraphs=[]
        if head_start < desc_start or head_start > desc_end:
            continue #header outside descriptions section ignored
        if head_end > desc_end:
            head_end = desc_end
        for paragraph in paragraphs:
            if paragraph.start_index >= head_start and paragraph.end_index <= head_end:
                headed_paragraphs.append(paragraph)
        matches.append((header,sorted(headed_paragraphs, key= lambda x: x.end_index)))
        
    return matches



