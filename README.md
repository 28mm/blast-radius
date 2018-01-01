# Blast Radius

[![PyPI version](https://badge.fury.io/py/BlastRadius.svg)](https://badge.fury.io/py/BlastRadius)

*Blast Radius* is a tool for reasoning about *Terraform* dependency graphs with interactive visualizations. Use *Blast Radius* to:
  * **Learn** about *Terraform* or one of its cloud providers, through [example configurations](https://28mm.github.io/blast-radius-docs/).
  * **Document** your infrastructure
  * **Reason** about relationships between resources, and evaluate changes to them.

![Blast Radius Preview](doc/blast-radius-demo.svg)

  * **Interact** with this diagram (and many others) [here](https://28mm.github.io/blast-radius-docs/).

# Quickstart

Install *Blast Radius* with pip, and *Graphviz* through your system's package manager.

````bash
[...]$ pip3 install BlastRadius
[...]$ brew install graphviz
````

Point *Blast Radius* at an `init-ed` *Terraform* project, and connect with your browser.

````bash
[...]$ blast-radius --serve /path/to/terraform-project
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
````

*Alternatively*, you can launch *Blast Radius* in a docker container. (In this example, the current working directory contains a *Terraform* project.)

```bash
[...]$ docker run -it --rm -p 5000:5000 -v $(pwd):/workdir 28mm/blast-radius
````

# Embeded Figures

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
<script src="/static/js/terraform-graph.js"></script>
<script src="/static/js/categories.js"></script>
<link rel="stylesheet" type="text/css" href="/static/css/style.css">
  ````

  3. A uniquely identified DOM element, where the `<svg>` should appear, and a call to `svg_activate(...)` somewhere after (usually at the end of the `<html>` document. 

  ````html
<div id="graph"></div> 
<script>
svg_activate('#graph', '/graph.svg', '/graph.json');
</script>
````

That's it. Ideas to simplify this process strongly desired. 

# Implementation Details

*Blast Radius* uses the [*Graphviz*](http://graphviz.org/) package to layout graph diagrams, [*PyHCL*](https://github.com/virtuald/pyhcl) to parse [*Terraform*](https://www.terraform.io/) configurations, and [*d3.js*](https://d3js.org/) to implement interactive features and animations.

# Further Reading

  * The motivations for *Blast Radius* are documented in a series of [blog](https://28mm.github.io) posts: [part 1](https://28mm.github.io/notes/d3-terraform-graphs), [part 2](https://28mm.github.io/notes/d3-terraform-graphs-2), and [part 3](https://28mm.github.io/notes/terraform-graphs-3).
  * A catalog of example *Terraform* configurations, and their dependency graphs can be found at [https://28mm.github.io/blast-radius-docs/](https://28mm.github.io/blast-radius-docs/).
