# Hugo does the whole build; this Makefile exists so the commands are
# discoverable and so the output path matches the sibling Materia Medica
# project (out/, gitignored, never committed).

SITE_DIR := ./out/site

.PHONY: all
all: site

.PHONY: site
site:
	@hugo --minify

.PHONY: serve
serve:
	@hugo server --buildDrafts --navigateToChanged

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
