

CATEGORIES_JSON = ./blastradius/server/static/js/categories.js
CATEGORIES_JS = ./blastradius/server/static/js/categories.json
JS_FILES = ./blastradius/server/static/js/categories.json ./blastradius/server/static/js/categories.js

.PHONY: clean
clean:
	-find . -type d -name __pycache__ -exec rm -r {} \+
	-rm $(CATEGORIES_JSON)
	-rm $(CATEGORIES_JS)

# build pypi package
.PHONY: dist
dist: clean
	-python3 setup.py sdist

.PHONY: docker
docker: $(JS_FILES)
	-docker build -t 28mm/blast-radius .

# categories.js & categories.json help with resource coloration.
# new resource types are added all the time, so we regenerate them
# from HashiCorp documentation.
$(CATEGORIES_JSON):
	-./utilities/providers/provider-category-json.py > $(CATEGORIES_JSON).new && mv $(CATEGORIES_JSON).new $(CATEGORIES_JSON)

$(CATEGORIES_JS): $(CATEGORIES_JSON)
	-sed -e '1s/{/resource_groups \= {/' $(CATEGORIES_JSON) > $(CATEGORIES_JS).new && mv $(CATEGORIES_JS).new $(CATEGORIES_JS)

all: $(JS_FILES) docker