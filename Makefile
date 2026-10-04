# Hugo does the whole build; this Makefile exists so the commands are
# discoverable and so the output path matches the sibling Materia Medica
# project (out/, gitignored, never committed).

SITE_DIR := ./out/site

.PHONY: all
all: site

.PHONY: site
site:
	@hugo --minify

# No --baseURL flag needed: `hugo server` runs in the "development"
# environment, and config/development/hugo.toml pins the preview to the
# localhost root. Plain `hugo server` therefore works too.
.PHONY: serve
serve:
	@hugo server --buildDrafts --navigateToChanged

# Serve the BUILT site locally. The production build hardcodes /egeria/ into
# every link, so it is rebuilt here against a root baseURL -- otherwise every
# page 404s when served from localhost.
.PHONY: preview
preview:
	@hugo --minify --baseURL http://localhost:8080/ --destination out/preview
	@echo "serving the built site at http://localhost:8080/ (ctrl-c to stop)"
	@python3 -m http.server 8080 --directory out/preview

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
	@rm -rf $(SITE_DIR) ./out/preview ./resources
