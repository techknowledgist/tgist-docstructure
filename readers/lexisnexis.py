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
from common import tags_with_name, tags_with_type, tags_with_matching_type

    
def headed_sections(tags, cautious=False):

    (headers, paragraphs, descriptions) = read_sections(tags)

    if not descriptions:
        return []

    description = descriptions[0] # first text_chunk is always (?) the description
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


def read_sections(tags):

    """Returns lists of headers, paragraphs and descriptions from the list of Tags."""
    
    structures = tags_with_name(tags, 'STRUCTURE')
    title_structures = tags_with_type(structures, 'SECTITLE')
    text_structures = tags_with_type(structures, 'TEXT')
    text_chunks = tags_with_type(structures, 'TEXT_CHUNK')
    # these three are doing nothing with input from the BAE fact file, but are still needed if we use
    # the output of create_standoff.pl, shoul dprobably hve some setting somewhere that
    # encodes what input tyoe we are dealing with
    headers = tags_with_name(tags, 'heading')
    paragraphs = tags_with_name(tags, 'p')
    descriptions = tags_with_name(tags, 'description')
    # and these three make sure there are headers etcetera when we have a BAE fact file
    headers.extend(title_structures)
    paragraphs.extend(text_structures)
    descriptions.extend(text_chunks)

    #print len(structures), len(title_structures), len(text_structures), len(text_chunks), \
    #    len(headers), len(paragraphs), len(descriptions)
    return (headers, paragraphs, descriptions)

