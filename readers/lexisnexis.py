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

    (headers, paragraphs, abstracts, descriptions) = read_sections(tags)

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
        matches.append((header, sorted(headed_paragraphs, key= lambda x: x.end_index)))

    return matches


def read_sections(tags):

    """Returns lists of headers, paragraphs and descriptions from the list of Tags."""

    # first see if you can find data in BAE fact file format
    structures = tags_with_name(tags, 'STRUCTURE')
    headers = tags_with_type(structures, 'SECTITLE')
    paragraphs = tags_with_type(structures, 'TEXT')
    abstracts =  tags_with_type(structures, 'ABSTRACT')
    descriptions = tags_with_type(structures, 'TEXT_CHUNK')
    if (headers or paragraphs or descriptions):
        return (headers, paragraphs, abstracts, descriptions)

    # if there weren't any data, try whether we used the output of create_standoff.pl (we
    # should probably have some setting somewhere that encodes what input type we are
    # dealing with)
    headers = tags_with_name(tags, 'heading')
    paragraphs = tags_with_name(tags, 'p')
    abstracts =  tags_with_type(structures, 'abstract')
    descriptions = tags_with_name(tags, 'description')
    #print len(structures), len(title_structures), len(text_structures), len(text_chunks), \
    #    len(headers), len(paragraphs), len(descriptions)
    return (headers, paragraphs, abstracts, descriptions)



def read_tags(text_file, fact_file):
    """Returns the text as a unicode string as well as a dictionary with the various kinds
    of tags."""
    (text, tags) = load_data(text_file, fact_file)
    # poke for the kind of tags expected in the BAE fact file format
    structures = tags_with_name(tags, 'STRUCTURE')
    if structures:
        return read_tags_bae(text, structures)
    else:
        return read_tags_default(text, tags)


def read_tags_bae(text, structures):

    def is_claim(text, claims_section):
        return text.attributes["TYPE"] == "TEXT" \
            and text.start_index >= claims_section.start_index \
            and text.end_index <= claims_section.end_index

    tags = {}
    tags['headers'] = tags_with_type(structures, 'SECTITLE')
    tags['paragraphs'] = tags_with_type(structures, 'TEXT')
    tags['abstracts'] =  tags_with_type(structures, 'ABSTRACT')
    tags['summaries'] = tags_with_type(structures, 'SUMMARY')
    tags['sections'] = tags_with_type(structures, 'TEXT_CHUNK')
    tags['claims_sections'] = tags_with_type(structures, 'CLAIMS')
    if tags['claims_sections']:
        claims_section = tags['claims_sections'][0]
        tags['claims'] = [c for c in structures if is_claim(c, claims_section)]
        tags['claims'] = sorted(tags['claims'], key = lambda x: x.start_index)
    else:
        tags['claims'] = []
    #return (text, headers, paragraphs, abstracts, summaries, sections, claims)
    return (text, tags)

def read_tags_default(text, tags):
    
    # this used the output of create_standoff.pl
    # TODO: needs to be updated

    headers = tags_with_name(tags, 'heading')
    paragraphs = tags_with_name(tags, 'p')
    abstracts =  tags_with_type(tags, 'abstract')
    summaries = tags_with_type(tags, 'summary')
    sections = tags_with_name(tags, 'description')
    claims = tags_with_name(tags, 'claim')
    claims = sorted(claims, key = lambda x: x.start_index)
    
    #print len(structures), len(title_structures), len(text_structures), len(text_chunks), \
    #    len(headers), len(paragraphs), len(descriptions)
    #return (text, headers, paragraphs, abstracts, summaries, sections, claims)
    return (text, tags)



