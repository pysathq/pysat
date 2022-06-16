.PHONY: doc-serve shortcode-docs docs
.DEFAULT_GOAL := doc-serve


GH_ORG = scientific-python
TEAMS_DIR = doc/static/teams
TEAMS = theme-team
TEAMS_QUERY = python tools/team_query.py

$(TEAMS_DIR):
	mkdir -p $(TEAMS_DIR)

$(TEAMS_DIR)/%.md: $(TEAMS_DIR)
	$(eval TEAM_NAME=$(shell python -c "import re; print(' '.join(x.capitalize() for x in re.split('-|_', '$*')))"))
	$(TEAMS_QUERY) --org $(GH_ORG) --team "$*"  >  $(TEAMS_DIR)/$*.html

teams-clean:
	for team in $(TEAMS); do \
	  rm -f $(TEAMS_DIR)/$${team}.html ;\
	done

teams: | teams-clean $(patsubst %,$(TEAMS_DIR)/%.md,$(TEAMS))

doc/content/shortcodes.md: $(wildcard layouts/shortcodes/*.html)
	python tools/render_shortcode_docs.py > doc/content/shortcodes.md

doc-serve: doc/content/shortcodes.md
	(cd doc && hugo serve --themesDir="../..")

docs: doc/content/shortcodes.md
	(cd doc ; hugo --themesDir="../..")
