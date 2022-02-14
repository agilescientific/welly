
# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help html

html:
	python pre_process_ipynb.py $(SOURCEDIR)/notebooks
	$(SPHINXBUILD) -E -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	python post_process_html.py $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."
