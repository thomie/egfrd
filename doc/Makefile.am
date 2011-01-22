
# BUILT
if HAVE_PDFLATEX
# Automake manual 18.2 Handling new file extensions
.tex.pdf:
	pdflatex $<

# Compile and install; do not distribute.
pdf_DATA = \
	implementation_notes.pdf\
	p1_fp.pdf
endif


math/*.nb:
	ls

# INSTALL
# Install and distribute.
nobase_dist_doc_DATA = \
	testing.txt\
	math/*.nb

#	math/hkmemo.nb\
#	math/fppairtheta.nb\
#	math/onlysigma.nb\
#	math/wosigma.nb\
#	math/psurvival.nb\
#	math/bd.nb\
#	math/prt.nb\
#	math/rR.nb\
#	math/fppairsurv.nb\
#	math/Pair2D.nb\
#	math/falphasurv.nb\
#	math/p_irr.nb\
#	math/PairSolution.nb\
#	math/p1fpmemo.nb\
#	math/fppair.nb\
#	math/pfree.nb\
#	math/p_rev.nb

# DIST
# Distribute; do not install.
EXTRA_DIST = \
	implementation_notes.tex \
	p1_fp.tex


# CLEAN
clean-local:
	rm -f *.log *.aux *.pdf

