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


def read_tags(text_file, fact_file, fact_type):
    """Returns the text as a unicode string as well as a dictionary with the various kinds
    of tags."""
    (text, tags) = load_data(text_file, fact_file, fact_type)
    if fact_type == 'BAE':
        structures = tags_with_name(tags, 'STRUCTURE')
        return read_tags_bae(text, structures)
    else:
        return read_tags_basic(text, tags)


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
    return (text, tags)


def read_tags_basic(text, taglist):
    tags = {}

    # the follwoing are used in English patents, and many of them also in chinese and
    # german patents
    tags['headers'] = tags_with_name(taglist, 'heading')
    tags['paragraphs'] = tags_with_name(taglist, 'p')
    tags['abstracts'] =  tags_with_name(taglist, 'abstract')
    tags['summaries'] = tags_with_name(taglist, 'summary')
    tags['sections'] = tags_with_name(taglist, 'description')
    tags['claims_sections'] = tags_with_name(taglist, 'claims')
    tags['claims'] = tags_with_name(taglist, 'claim')
    tags['claims'] = sorted(tags['claims'], key = lambda x: x.start_index)

    # chinese patents until 2010 have two relevant named tags inside the description
    # TODO: see remark in ../lexisnexis.add_description_sections() on refactoring
    # language-specific code
    tags['technical-field'] = tags_with_name(taglist, 'technical-field')
    tags['background-art'] = tags_with_name(taglist, 'background-art')

    return (text, tags)



