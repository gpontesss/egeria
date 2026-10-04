# Hugo does the whole build; this Makefile exists so the commands are
# discoverable and so the output path matches the sibling Materia Medica
# project (out/, gitignored, never committed).

SITE_DIR := ./out/site

.PHONY: all
all: site

.PHONY: site
site:
	@hugo --minify

# baseURL carries a path (a GitHub Pages *project* site), and the dev server
# would otherwise serve the pages at / while their assets point at /egeria/,
# which renders the site completely unstyled. --baseURL pins the preview to
# the root so local and published both work.
.PHONY: serve
serve:
	@hugo server --buildDrafts --navigateToChanged --baseURL http://localhost:1313/

.PHONY: check
check:
	@hugo --minify --printPathWarnings --panicOnWarning

# make new REGION=athens SLUG=agia-eirini
.PHONY: new
new:
	@test -n "$(REGION)" || { echo "usage: make new REGION=athens SLUG=some-church"; exit 1; }
	@test -n "$(SLUG)" || { echo "usage: make new REGION=athens SLUG=some-church"; exit 1; }
	@hugo new content "content/$(REGION)/$(SLUG).md"

.PHONY: clean
clean:
	@rm -rf $(SITE_DIR) ./resources
