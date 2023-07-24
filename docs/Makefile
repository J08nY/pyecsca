# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "  apidoc	to build api docs"

apidoc:
	mkdir -p api/
	sphinx-apidoc  ../pyecsca/ --implicit-namespaces --ext-autodoc --no-toc -M -f -e -o api/
	sphinx-apidoc ../../pyecsca-codegen/pyecsca/ --implicit-namespaces --ext-autodoc --no-toc -M -f -e -o api/
	rm api/pyecsca.rst  #It is jumbled anyway.

.PHONY: help apidoc Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
