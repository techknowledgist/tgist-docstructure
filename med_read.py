
class Tag():
    
    def __init__(self,text):
        split_text=text.split()
        try:
            self.start_index = int(split_text[0])
            self.end_index = int(split_text[1])
            self.name = split_text[2]
            self.attributes = split_text[3:]
        except IndexError:
            self.start_index = None
            self.end_index = None
            self.name = None
            self.attributes = None

    def __str__(self):
        return "[%d %d %s]" % (self.start_index, self.end_index, self.name)
            
    def __len__(self):
        return self.end_index-self.start_index

    def text(self,doc):
        return doc[self.start_index:self.end_index]

    
def load_data(text_file, fact_file):
    text = open(text_file).read()
    sections = []
    # the following line is instead of the commented out line below, this way you do not
    # get an empty Tag for whitelines or the empty element at the end of the split
    tags = [Tag(line) for line in open(fact_file) if line.strip() != '']
    # tags=map(Tag,open(tagname).read().split("\n"))
    return (text,tags)

def load_articles(basename_file="files.txt"):
    articles = []
    for line in open(basename_file):
        basename = line.strip().split("/")[-1]
        articles.append(load_data(basename))
    return articles

def headed_sections(tags):
    headers = filter(lambda x: x.name == "title", tags)
    sections = filter(lambda x: x.name == "sec", tags)
    matches = []
    for header in headers:
        for section in sections:
            if header.start_index == section.start_index:
                matches.append((header,section))
                break
    return matches

def find_abstracts(tags):
    return filter(lambda x: x.name == "abstract", tags)
