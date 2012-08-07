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

def find_abstracts(tags):
    return filter(lambda x: x.name == "abstract", tags)
