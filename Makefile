#
# make clean
# make
# make publish
#
# TODO: add tests.
#

CATEGORIES_JSON = ./blastradius/server/static/js/categories.json
CATEGORIES_JS   = ./blastradius/server/static/js/categories.js

.PHONY: clean
clean:
	-find . -type d -name __pycache__ -exec rm -r {} \+
	-rm $(CATEGORIES_JSON)
	-rm $(CATEGORIES_JS)

# build pypi package
.PHONY: dist
dist:
	-python3 setup.py sdist

# build docker image
.PHONY: docker
docker:
	-docker build -t 28mm/blast-radius .

# push pypi and docker images to public repos
.PHONY: publish
publish:
	-twine upload dist/*
	-docker push 28mm/blast-radius:latest

# rebuild categories.js from upstream docs
.PHONY: categories
categories: $(CATEGORIES_JS)

$(CATEGORIES_JSON):
	-./utilities/providers/provider-category-json.py > $(CATEGORIES_JSON).new && mv $(CATEGORIES_JSON).new $(CATEGORIES_JSON)

$(CATEGORIES_JS): $(CATEGORIES_JSON)
	-sed -e '1s/{/resource_groups \= {/' $(CATEGORIES_JSON) > $(CATEGORIES_JS).new && mv $(CATEGORIES_JS).new $(CATEGORIES_JS)

# probably best to clean 1st
all: categories dist docker