set -e
set -x
if command -v apk; then
    apk add curl bison flex flex-dev automake autoconf libtool \
        bzip2-dev gperf
fi
if command -v yum; then
    dnf groupinstall -y "Development Tools"
    dnf install -y swig flex zlib-devel readline-devel m4 perl-core \
        bzip2-devel gperf
fi

NPROC=$(getconf _NPROCESSORS_ONLN 2>/dev/null || sysctl -n hw.ncpu)
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
SUDO="sudo"
fi
    
# Bison
BISON_VERSION=3.8.2
BISON_SRC_HASH=06c9e13bdf7eb24d4ceb6b59205a4f67c2c7e7213119644430fe82fbd14a0abb
if ! printf '%s\n' '%require "3.8"' '%%' 'start: ;' | bison -o /dev/null /dev/stdin ; then
    WORKDIR=$(mktemp -d)
    (
        cd $WORKDIR
        curl -L --retry 5 --retry-delay 3 \
            https://ftp.gnu.org/gnu/bison/bison-${BISON_VERSION}.tar.gz > bison.tgz
        echo "$BISON_SRC_HASH bison.tgz" | sha256sum -c
        tar --strip-components=1 -xzC . -f bison.tgz
        ./configure
        make clean
        $SUDO make install -j$NPROC
    )
rm -rf "$WORKDIR"
fi
