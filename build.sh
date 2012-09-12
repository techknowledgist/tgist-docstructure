#!/bin/csh -f

# Shell script to create a directory that can be sent off to users like BAE. Running it
# will create a directory docstructure-YYYYMMDD with all python scripts, some of the
# example data, and housekeeping data in the info directory (with git-related stuff). It
# prints the directory created and the git status on the working directory, the latter to
# kame it easy for the user to relaize that what you are packagng is not versioned.

set version = `date +"%Y%m%d"`
set x = "docstructure-${version}"

echo; echo "CREATING DIRECTORY docstructure-$version"
echo; echo "GIT STATUS"; echo
git status -bs
echo

mkdir $x
cp *.py $x

mkdir $x/utils
cp utils/*py $x/utils

mkdir $x/readers
cp readers/*py $x/readers

mkdir $x/data
cp data/f* $x/data
cp data/e* $x/data
cp data/US* $x/data

mkdir $x/info
git status > $x/info/git-status.txt
git diff > $x/info/git-diff-working.txt
git diff --cached > $x/info/git-diff-cached.txt
git log --decorate --graph --all > $x/info/git-log.txt
