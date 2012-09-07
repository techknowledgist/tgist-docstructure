#!/usr/bin/perl

# ----------------------------------------------------------------------------------------
# create_standoff.pl
# ----------------------------------------------------------------------------------------
#
# Takes an XML file and creates series of files containing the text, tags, meta data, and
# the full file with annotation in UIMA's CAS format.
#
# Usage:
#
#     perl create_strandoff.pl <xmlfile>
#
# This will create four new files:
#
#   <tmlfile>.txt contains the text with all tags stripped out
#   <tmlfile>.tag contains the tags only in standoff format
#   <tmlfile>.meta contains meta information about <tmlfile>
#   <tmlfile>.cas contains all data from <xmlfile> in CAS format
#
# This script is based on a script with the same name that was written for TimeML. Only
# minor changes were made.
#
# NOTES:
# - this script leaves in the DOCTYPE declaration
# - this script may or may not do the right thing with encodings
# - the CAS format is disabled, edit the line with $print_cas to change this
#
# Marc Verhagen, June 2012.
#
# ----------------------------------------------------------------------------------------


use XML::Parser;
use Data::Dumper;

# set to 1 if you want to see a dump file with results of the XML parse
$print_dump = 0;

# set to 1 if you also want the CAS format
$print_cas = 0;


my $tmlfile = shift;
my $base = $tmlfile;
my $dump_file = "$base.dmp";
my $text_file = "$base.txt";
my $tags_file = "$base.tag";
my $meta_file = "$base.meta";
my $cas_file = "$base.cas";

print "Parsing $tmlfile...\n";
my $doc = &parse($tmlfile);

&create_standoff($doc);
&create_cas();



# Simple XML Parsing. Dump everything in a flat list with <type, text>
# pairs where type is one of 'opentag', 'closetag' or 'text', and text
# is the actual text string (this text string is '' for the closing
# tag of an empty tag). 

sub parse
{
    my $file = shift;

    my $parser = new XML::Parser(Style=>'Tree');
    my $parser = new XML::Parser();
    $parser->setHandlers(
        Start    => \&handle_start,
        End      => \&handle_end,
        XMLDecl  => \&handle_xmldecl,
        Proc     => \&handle_proc,
        Default  => \&handle_default
        );
    local @doc;
    local $docCounter = 0;
    
    my $result = $parser->parsefile($file);
    if ($print_dump) {
        open DUMP, "> $dump_file" or die;
        print DUMP Dumper(\@doc);
        close DUMPER;
    }
    return \@doc;
}

sub handle_start
{
    local $expat = shift;
    local $tag = shift;
    $doc[$docCounter] = ['opentag', $tag, $expat->original_string()];
    $docCounter++;
}

sub handle_end
{
    local $expat = shift;
    local $tag = shift;
    $doc[$docCounter] = ['closetag', $tag, $expat->original_string()];
    $docCounter++;
}

sub handle_xmldecl
{
    local $expat = shift;
    $doc[$docCounter] = ['xmldec', $expat->original_string()];
    $docCounter++;
}

sub handle_proc
{
    #local $expat = shift;
    #$doc[$docCounter] = ['xmldec', $expat->original_string()];
    #$docCounter++;
}

sub handle_default
{
    local $expat = shift;
    $doc[$docCounter] = ['text', $expat->original_string()];
    $docCounter++;
}


# Creating the standoff annotation files: text file with all tags
# stripped out, a tag file, and a meta data file that holds the
# document size. 

sub create_standoff
{
    my $doc = shift;

    open TEXT, "> $text_file" or die;
    open TAGS, "> $tags_file" or die;
    open META, "> $meta_file" or die;
    if ($print_case) {
	open CAS, "> $cas_file" or die; }

    my $offset = 0;
    my @taglist = ();
    my @tagstack = ();

    foreach $element (@$doc)
    {
        my $type = $element->[0];
    
        if ($type eq 'text') {
            my $text = $element->[1];
            $offset += length($text);
            print TEXT $text;
        }
        elsif ($type eq 'opentag') {
            my $tag = $element->[1];
            my $text = $element->[2];
            $currenttag = { _tag => $tag, _begin => $offset };
            push @tagstack, "$text -- $offset";
        }   
        elsif ($type eq 'closetag') {
            my $tag = $element->[1];
            my $text = $element->[2];
            my $retrievedtag = pop @tagstack;
            push @taglist, "$retrievedtag -- $offset";
        }
        elsif ($type eq 'xmldec') {
            # nothing needed
        }
    }

    print META "DOCUMENT_SIZE = $offset\n";

    foreach $element (sort by_offset @taglist) {
        $element =~ s/\s+/ /gm;
        if ($element =~ /(.*) -- (\d+) -- (\d+)$/mg) {
            my ($tag, $begin, $end) = ($1, $2, $3);
            $tag =~ s|^<||;
            $tag =~ s|/?>$||;
            print TAGS "$begin $end $tag\n";
        } else {
            print "WARNING, weird input: $element\n";
        }
    }

    close TEXT;
    close TAGS;
    close META;
}

sub by_offset {
    $a =~ /(\d+) -- (\d+)/;
    $a_begin = $1;
    $a_end = $2;
    $b =~ /(\d+) -- (\d+)/;
    $b_begin = $1;
    $b_end = $2;
    if ($a_begin != $b_begin) {
        return $a_begin <=> $b_begin;
    } else {
        return $b_end <=> $a_end;
    }
}


# Create the CAS format.

sub create_cas
{
    return if not $print_cas;

    open TEXT, $text_file or die;
    open TAGS, $tags_file or die;
    open META, $meta_file or die;
    open CAS, "> $cas_file" or die;

    print CAS '<?xml version="1.0" encoding="UTF-8"?><CAS><uima.tcas.Document _content="text">';

    while (<TEXT>)
    {
        print CAS;
    }

    $metadata = <META>;
    $metadata =~ /DOCUMENT_Size = (\d+)/;
    $doc_size = $1;

    print CAS "</uima.tcas.Document>\n";
    print CAS "<uima.tcas.DocumentAnnotation _indexed=\"1\" _id=\"8\" sofa=\"1\" begin=\"0\" end=\"$doc_size\" language=\"en\"/>\n";
    print CAS "<com.ibm.uima.examples.SourceDocumentInformation _indexed=\"1\" _id=\"13\" sofa=\"1\" begin=\"0\" end=\"0\" uri=\"file:/Applications/ADDED/UIMA_SDK_1/docs/examples/data/TimeML-example.xml\" offsetInSource=\"0\" documentSize=\"$doc_size\"/>\n";

$id = 2;
    while (<TAGS>) {
        if (/^(\d+) (\d+) (\S+)(.*)/) {
            my ($begin, $end, $tag, $atts) = ($1, $2, $3, $4);
            $tag = &rewriteTag($tag);
            $attributes = &renameAttributes($tag, $atts);
            next if $tag eq 'lex';
            print CAS "<xbank.$tag _indexed=\"1\" _id=\"$id\" sofa=\"1\" begin=\"$begin\" end=\"$end\"$attributes/>\n";
            $id++;
        }
    } 
        
    print CAS "</CAS>\n";
}


sub rewriteTag
{
    my $tag = shift;
    return 'Event' if $tag eq 'EVENT';
    return 'Timex3' if $tag eq 'TIMEX3';
    return 'Rel' if $tag eq 'rel';
    return 'P_Arg0' if $tag eq 'P_ARG0';
    return 'P_Arg1' if $tag eq 'P_ARG1';
    return 'P_Arg2' if $tag eq 'P_ARG2';
    return 'Nomrel' if $tag eq 'nomrel';
    return 'N_Arg1' if $tag eq 'N_ARG1';
    return $tag;
}

sub renameAttributes
{
    my $tag = shift;
    my $atts = shift;
    if ($tag =~ /^(Event|Timex3)$/) {
        print "EVENT: $tag $atts\n";
        $atts =~ s/(\w+)="/tml_$1="/g;
    }
    if ($tag =~ /^(Rel|P_.*)$/) {
        print "PROP: $tag $atts\n";
        $atts =~ s/(\w+)="/prop_$1="/g;
    }
    if ($tag =~ /^(Nomrel|N_.*)$/) {
        print "NOM: $tag $atts\n";
        $atts =~ s/(\w+)="/nom_$1="/g;
        print "NOM: $tag $atts\n";
    }
    return $atts;
}
