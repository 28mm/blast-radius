CATEGORIES_JSON = ./blastradius/server/static/js/categories.json
CATEGORIES_JS = ./blastradius/server/static/js/categories.js

.PHONY: clean
clean:
	-find . -type d -name __pycache__ -exec rm -r {} \+
	-rm $(CATEGORIES_JSON)
	-rm $(CATEGORIES_JS)

# build pypi package
.PHONY: dist
dist:
	-python3 setup.py sdist

.PHONY: docker
docker:
	-docker build -t 28mm/blast-radius .

.PHONY: publish
publish:
	-twine upload dist/*
	-docker push 28mm/blast-radius:latest


.PHONY: categories
categories: $(CATEGORIES_JS)
# categories.js & categories.json help with resource coloration. new resource types are added all the time, 
# so we regenerate them from HashiCorp documentation.
$(CATEGORIES_JSON):
	-./utilities/providers/provider-category-json.py > $(CATEGORIES_JSON).new && mv $(CATEGORIES_JSON).new $(CATEGORIES_JSON)

$(CATEGORIES_JS): $(CATEGORIES_JSON)
	-sed -e '1s/{/resource_groups \= {/' $(CATEGORIES_JSON) > $(CATEGORIES_JS).new && mv $(CATEGORIES_JS).new $(CATEGORIES_JS)

all: categories dist docker