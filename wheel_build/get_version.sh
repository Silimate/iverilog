BASE_VER=$(perl -ne 'print "$1." if /\#\s*define\s+VERSION_(?:MAJOR|MINOR)\s+(\d+)/' version_base.h)
BASE_VER=${BASE_VER%.*}
printf $BASE_VER
