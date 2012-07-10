import med_read,sections,os

def sections_in_file(filename):
    """
    Takes a filename, extracts the sections from it. Preprocessing must have
    been done with create_standoff.pl.
    """
    article=med_read.load_data(filename)
    a_text=article[0]
    a_tags=article[1]
    raw_sections=med_read.headed_sections(a_tags)
    abstracts=med_read.find_abstracts(a_tags)
    return sections.make_sections(raw_sections, abstracts, a_text,filename)
    
def convert_file(filename):
    """
    Takes a filename, creates a .sections file with the section data.
    Preprocessing must have been done with create_standoff.pl.
    """
    sections=sorted(sections_in_file(filename), key= lambda x: x.start_index)
    f=open(filename+".sections","w")
    f.write(sections_to_output(sections))
    f.close()

def sections_to_output(sections):
    """
    Converts section data into an output string.
    """
    output=""
    for section in sections:
        line=("SECTION Type=\"" + "|".join(section.types) + "\" Title=\""
            + section.header+"\" Start=" + str(section.start_index) + " End="
            + str(section.end_index) + "\n")
        output+=line
    return output


def convert_files(file_list):
    """
    Takes either a list of filenames or a filename of a file containing a list
    of filenames, and creates .sections files with the section data in those
    files. Preprocessing must have been done with create_standoff.pl.
    """
    if isinstance(file_list,str):
        for line in open(filename_filename):
            basename=line.strip().split("/")[-1]
            convert_file(basename)
    else:
        for basename in file_list:
            convert_file(basename)

def convert_all(path="."):
    """
    Creates .sections files from all the files with ending .nxml at the given
    path.  Preprocessing must have been done with create_standoff.pl.
    """
    listing=os.listdir(path)
    basenames=filter(lambda x: x[-5:]==".nxml",listing)
    convert_files(basenames)
    
