import codecs

# List of all interesting tags. This list is just for patents, may need many more. One
# question to answer is whether we should restrict the tags at all.

TAGS = ('description', 'abstract', 'technical-field', 'background-art',
        'related-apps', 'claims', 'claim', 'p', 'heading', 'summary',
        'invention-title', 'publication-reference', 'date')


def transform_tags_file(file1 , file2):
    """Takes an xml file as created by the xslt scripts in standoff and create a file that is
    more like the BAE fact file, using just the tags that are of interest."""

    out = codecs.open(file2, 'w', encoding='utf-8')
    for line in codecs.open(file1, encoding='utf-8'):
        fields = line.strip().split()
        tag = fields[0][1:]
        if tag in TAGS:
            tagline =  tag + ' ' + ' '.join(fields[1:])
            tagline = tagline.strip('/>')
            out.write(tagline+"\n")
