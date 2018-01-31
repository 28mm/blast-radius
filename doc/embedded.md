# Embedded Figures

You may wish to embed figures produced with *Blast Radius* in other documents. You will need the following:

 1. an `svg` file and `json` document representing the graph and its layout. These are produced with *Blast Radius*, as follows

````bash
[...]$ terraform graph | blast-radius --svg > graph.svg
[...]$ terraform graph | blast-radius --json > graph.json
````

  2. `javascript` and `css`. You can find these in the `.../blastradius/server/static` directory. Copy these files to an appropriate location, and ammend the following includes to reflect those locations.

  ````html
<script src="/static/js/d3.v4.js"></script>
<script src="/static/js/d3-tip.js"></script>
<script src="/static/js/blast-radius.js"></script>
<script src="/static/js/categories.js"></script>
<link rel="stylesheet" type="text/css" href="/static/css/style.css">
  ````

  3. A uniquely identified DOM element, where the `<svg>` should appear, and a call to `blastradius(...)` somewhere after (usually at the end of the `<html>` document. 

  ````html
<div id="graph"></div> 
<script>
blastradius('#graph', '/graph.svg', '/graph.json');
</script>
````

That's it. Ideas to simplify this process strongly desired. 