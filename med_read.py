import shlex, codecs


class Tag():
    
    def __init__(self,text):
        split_text=shlex.split(text)
        try:
            self.start_index = int(split_text[0])
            self.end_index = int(split_text[1])
            self.name = split_text[2]
            self.attributes = split_text[3:]
        except IndexError:
            #not enough stuff, assume this is a malformed tag
            self.start_index = None
            self.end_index = None
            self.name = None
            self.attributes = None
        except ValueError:
            #guess that this is in the second format
            self.name = split_text[0]
            split_text = dict(map(lambda x: str.split(x, "=", 1), split_text[1:])) 
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

    
def load_data(text_file, fact_file):
    text = codecs.open(text_file, encoding='utf-8').read()
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



def headed_sections(tags, max_title_lead=30):
    headers = filter(lambda x: x.name == "title", tags)
    sections = filter(lambda x: x.name == "sec", tags)
    structures = filter(lambda x: x.name == "STRUCTURE", tags)
    title_structures = filter(lambda x: x.attributes["TYPE"] == "TITLE", structures)
    text_structures = filter(lambda x: x.attributes["TYPE"][:4] == "TEXT", structures)

    
    matches = []
    
    for header in headers:
        for section in sections:
            if (header.start_index == section.start_index):
                matches.append((header,section))
                break
    for title in title_structures:
        for text_structure in text_structures:
            if (title.end_index < text_structure.start_index
                and text_structure.start_index - title.end_index < max_title_lead):
                matches.append((title, text_structure))
                break
    return matches

def find_abstracts(tags):
    return filter(lambda x: x.name == "abstract", tags)


