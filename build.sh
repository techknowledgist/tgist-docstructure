#!/bin/csh -f

# Shell script to create a directory that can be sent off to users like BAE.
# 
# Usage example:
#
#  % ./build.sh docstructure
#
# This will create a directory docstructure/YYYYMMDD with all python scripts and some of
# the example data.

set build_dir = $1 
set version = `date +"%Y%m%d"`

echo "CREATING DIRECTORY $build_dir-$version"

mkdir $build_dir
cp *.py $build_dir
mkdir $build_dir/data
cp data/f* $build_dir/data

echo mv $build_dir $build_dir$version
echo mv $build_dir ${build_dir}-${version}
mv $build_dir ${build_dir}-${version}
