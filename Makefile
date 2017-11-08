.PHONY: clean
clean:
	#-find . -type f -name *~ -exec rm {} \+
	-find . -type d -name __pycache__ -exec rm -r {} \+

# categories.js & categories.json help with resource coloration.
# new resource types are added all the time, so we regenerate them
# from HashiCorp documentation.
./blastradius/server/static/js/categories.json:
	-./utilities/providers/provider-category-json.py > blastradius/server/static/js/categories.json.new && mv blastradius/server/static/js/categories.json.new blastradius/server/static/js/categories.json

./blastradius/server/static/js/categories.js: ./blastradius/server/static/js/categories.json
	-sed -e '1s/{/resource_groups \= {/' blastradius/server/static/js/categories.json > blastradius/server/static/js/categories.js.new && mv blastradius/server/static/js/categories.js.new blastradius/server/static/js/categories.js

all: ./blastradius/server/static/js/categories.json ./blastradius/server/static/js/categories.js