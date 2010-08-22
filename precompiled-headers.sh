#!/bin/sh

ALL_FILES=`find . -name "*.[ch]pp"`
FILES=`find . -maxdepth 1 -name "*.[ch]pp" | grep -v GreensFunction`

FILES=$ALL_FILES

# Check if we didn't miss any complicated includes.
grep -e 'ifdef\|defined' $FILES | \
grep HAVE | \
grep -v CONFIG | \
grep -v FUNCTIONAL | \
grep -v HASH | \
grep -v UNORDERED_MAP | \
grep -v HAVE_PYINT_FROMSIZE_T | \
grep -v HAVE_PYBASEEXCEPTIONOBJECT

echo '#ifndef HEADERS_HH
#define HEADERS_HH

/* This file was created by the script called 'precompiled-headers.sh'.
Also see: http://gcc.gnu.org/onlinedocs/gcc/Precompiled-Headers.html */

#include "config.h"

#if defined(HAVE_TR1_FUNCTIONAL)
#include <tr1/functional>
#elif defined(HAVE_STD_HASH)
#include <functional>
#elif defined(HAVE_BOOST_FUNCTIONAL_HASH_HPP)
#include <boost/functional/hash.hpp>
#endif

#if defined(HAVE_UNORDERED_MAP)
#include <unordered_map>
#elif defined(HAVE_TR1_UNORDERED_MAP)
#include <tr1/unordered_map>
#elif defined(HAVE_BOOST_UNORDERED_MAP_HPP)
#include <boost/unordered_map.hpp>
#endif
' > headers.hh


grep '#include ' $ALL_FILES | \
grep -v '<' | \
#grep boost | \
#grep -v config | \
#grep -v functional | \
#grep -v unordered_map | \
#grep -v gsl | \
cut -d ':' -f 2 | \
sed 's|\.\./||' | \
sort | \
uniq -c |
grep -v ' 1 ' | \
#cut -b9- | \
sort \
>> headers.hh

echo "\n#endif /* HEADERS_HH */" >> headers.hh

#grep '#include <boost' *.hpp *.cpp | grep -v functional | cut -d ':' -f 2 | sort | uniq >> headers.hh
#echo >> headers.hh
#grep '#include ' $FILES | grep -v '<' | grep -v config | cut -d ':' -f 2 | sort | uniq >> headers.hh
#echo >> headers.hh



#sed -i '1 i #include "headers.hh"\n' $FILES

sed -i '/CLEANFILES/ a\	headers.hh.gch' Makefile.am
#sed -i '/BUILT_SOURCES/ a\	headers.hh.gch' Makefile.am

echo '
%.hpp.gch: %.hpp
	$(CXXCOMPILE) -fPIC -DPIC -m128bit-long-double -maccumulate-outgoing-args $<' >> Makefile.am
