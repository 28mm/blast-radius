//
// terraform-graph.js 
//

// Sometimes we have escaped newlines (\n) in
// json strings. we want <br> instead.
var replacer = function (key, value) {
    if (typeof value == 'string') {
        return value.replace(/\n/g, '<br>');
    }
    return value;
}

// Takes a unique selector, e.g. "#demo-1", and
// appends svg xml from svg_url, and takes graph
// info from json_url to highlight/annotate it.
svg_activate = function (selector, svg_url, json_url) {

    var container = d3.select(selector);
    var color     = d3.scaleOrdinal(d3['schemeCategory20']);

    var lookup = function (list, key, value) {
        for (var i in list)
            if (i in list && key in list[i] && list[i][key] == value)
                return list[i];
    }

    // 1st pull down the svg, and append it to the DOM as a child
    // of our selector. If added as <img src="x.svg">, we wouldn't
    // be able to manipulate x.svg with d3.js, or other DOM fns. 
    d3.xml(svg_url, function (error, xml) {

        container.node()
            .appendChild(document.importNode(xml.documentElement, true));

        // remove <title>s in svg; graphviz leaves these here and they
        // trigger useless tooltips.
        d3.select(selector).selectAll('title').remove();

        // Obtain the graph description. Doing this within the
        // d3.xml success callback, to guaruntee the svg/xml
        // has loaded.
        d3.json(json_url, function (error, data) {
            var edges = data.edges;
            var svg_nodes = [];
            var nodes = {};
            data.nodes.forEach(function (node) {
                if (!(node.type in resource_groups))
                    console.log(node);
                node.group = (node.type in resource_groups) ? resource_groups[node.type] : -1;
                nodes[node['label']] = node;
                svg_nodes.push(node);
            });
            console.log(nodes);

            var svg = container.select('svg');

            // setup tooltips
            var tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function (d) {
                    return "<span style='background:" + color(d.group) + ";' class='header'>" + d.simple_name + "</span>" + (d.definition.length == 0 ? child_html(d) : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>" + child_html(d));
                });
            svg.call(tip);

            // returns <span> elements representing a node's direct children 
            var child_html = function (d) {
                ret_str = '';
                for (var src in data.edges) {
                    if (d.label == edges[src].source) {
                        var node = lookup(data.nodes, 'label', data.edges[src].target);
                        ret_str += '<span class="dep" style="background:' + color(node.group) + ';">' + node.simple_name + '</span><br>';
                    }

                }
                //console.log(ret_str);
                return ret_str;
            }

            // FIXME: this is grosssssssss.
            var get_dependencies = function (node) {

                var ret_children = [];

                for (var i in edges) {
                    if (edges[i].source == node.label) {
                        ret_children.push(nodes[edges[i].target]);
                        if (edges[i].target in nodes) {
                            var children = get_dependencies(nodes[edges[i].target]);
                            for (var j in children) {
                                ret_children.push(children[j]);
                            }
                        }
                    }
                }
                //console.log(ret_children);
                return ret_children;
            }

            // FIXME: also grossss.
            var get_dependency_edges = function(node) {
                var ret_edges = [];
                var children  = [];

                for (var i in edges) {

                    if (edges[i].source == node.label) {
                        ret_edges.push(edges[i]);
                        children.push(nodes[edges[i].target]);
                    }
                }
                for (var c in children) {
                    var dep_edges = get_dependency_edges(children[c]);
                    for (var i in dep_edges) {
                        ret_edges.push(dep_edges[i]);
                    }
                }
                return ret_edges;
            }

            var highlight = function (d) {
                tip.show(d);

                var dependencies = get_dependencies(d);
                dependencies.push(d);

                var dependency_edges = get_dependency_edges(d);

                // transtition()s add a little frustration to mouse interaction.
                // if the user mouseout()s before the transition completes, the
                // figure doesn't always return to normal....
                svg.selectAll('g.node')
                    .data(dependencies, function (d) { return (d && d.svg_id) || d3.select(this).attr("id"); })
                    .attr('opacity', 1.0)
                    .exit()
                    //.transition()
                    .attr('opacity', 0.2);

                svg.selectAll('g.edge')
                    .data(dependency_edges, function(d) { return d && d.svg_id || d3.select(this).attr("id"); })
                    .attr('opacity', 1.0)
                    .exit()
                    //.transition()
                    .attr('opacity', 0.0);
            }

            var unhighlight = function (d) {
                svg.selectAll('g.node')
                    .attr('opacity', 1.0);
                svg.selectAll('g.edge')
                    .attr('opacity', 1.0)
                tip.hide(d);
            }

            // colorize nodes, and add mouse candy.
            svg.selectAll('g.node')
                .data(svg_nodes, function (d) {
                    return (d && d.svg_id) || d3.select(this).attr("id");
                })
                .on('mouseover', highlight)
                .on('mouseout', unhighlight)
                .on('mousedown', highlight)
                .attr('fill', function (d) { return color(d.group); })
                .select('polygon')
                .style('fill', (function (d) {
                    if (d)
                        return color(d.group);
                    else
                        return '#000';
                }));

            // stub, in case we want to do something with edges on init.
            svg.selectAll('g.edge')
                .data(edges, function(d) { return d && d.svg_id || d3.select(this).attr("id"); });
        });


    });

};

