"""

Quick and dirty script to view results of processing.

Usage example:

   % python view.py elsevier-simple.txt elsevier-simple.sect out.html

   The first file is the raw text, the second the output of the docstructure parser. The
   third file is created by the script and contains a pretty print of the text with blue
   boxes added around the sections, headers are not marked, but the types associated with
   the section are printed in a red box preceding the section.
   
This will probably break if there are overlapping sections. It is also quite rigid on what
the expected format of the sect file is, expected is

   SECTION ID=5 TYPE="CONCLUSION" START=8912 END=9025

Any changes may break this script.


"""


import sys, codecs, re
import html_fragments


def createHTML(text_file, sect_file, html_file):

    fh_html = codecs.open(html_file,'w', encoding='utf-8')
    fh_text = codecs.open(text_file, encoding='utf-8')
    fh_sect = codecs.open(sect_file, encoding='utf-8')

    starts = {}
    ends = {}
    for line in fh_sect:
        p1 = line.find('START')
        p2 = line.find('END')
        p3 = line.find('TYPE')
        start = line[p1+6:].split()[0] 
        end = line[p2+4:].split()[0]
        label = line[p3+5:p1].strip()
        starts[int(start)]= label
        ends[int(end)] = True
        
    fh_html.write(html_fragments.HTML_PREFIX)
    text = fh_text.read()
    p = 0
    for char in text:
        if starts.has_key(p):
            fh_html.write("<p><div class=header>%s</div></p>\n" % starts[p])
            fh_html.write("<p><div class=section></p>\n")
        fh_html.write(char)
        if ends.has_key(p):
            fh_html.write('</div>')
        if char == "\n":
            fh_html.write('</br>')
        p += 1
    fh_html.write(html_fragments.HTML_END)
    fh_html.close()



if __name__ == '__main__':
    text_file, sect_file, html_file = sys.argv[1:4]
    createHTML(text_file, sect_file, html_file)
