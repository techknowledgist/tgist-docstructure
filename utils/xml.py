
def transform_tags_file(file1 , file2):
    """Takes an xml file as created by the xslt scripts in standoff and create a file that is
    more like the BAE fact file, using tag that are of interest. """
    # TODO: list below is just for patents, need many more
    # TODO: do all tags?
    tags = ('<description', '<abstract', '<technical-field', '<background-art',
            '<claims', '<claim', '<p', '<heading') 
    out = open(file2, 'w')
    for line in open(file1):
        fields = line.strip().split()
        tag = fields[0]
        if tag in tags:
            tagline =  tag[1:] + ' ' + ' '.join(fields[1:])
            tagline = tagline.strip('>')
            out.write(tagline+"\n")
