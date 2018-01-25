//
// terraform-graph.js 
//

//
var edge_types = {
    NORMAL        : 1, // what we talk about when we're talking about edges.
    HIDDEN        : 2, // these are normal edges, but aren't drawn.
    LAYOUT_SHOWN  : 3, // these edges are drawn, but aren't "real" edges
    LAYOUT_HIDDEN : 4, // these edges are not drawn, aren't "real" edges, but inform layout.
}

// Sometimes we have escaped newlines (\n) in
// json strings. we want <br> instead.
var replacer = function (key, value) {
    if (typeof value == 'string') {
        return value.replace(/\n/g, '<br>');
    }
    return value;
}

//
// Utilities
//

var to_list = function(obj) {
    var lst = [];
    for (var k in obj)
        lst.push(obj[k]);
    return lst;
}

var Queue = function() {
    this._oldestIndex = 1;
    this._newestIndex = 1;
    this._storage = {};
}
 
Queue.prototype.size = function() {
    return this._newestIndex - this._oldestIndex;
};
 
Queue.prototype.enqueue = function(data) {
    this._storage[this._newestIndex] = data;
    this._newestIndex++;
};
 
Queue.prototype.dequeue = function() {
    var oldestIndex = this._oldestIndex,
        newestIndex = this._newestIndex,
        deletedData;
 
    if (oldestIndex !== newestIndex) {
        deletedData = this._storage[oldestIndex];
        delete this._storage[oldestIndex];
        this._oldestIndex++;
 
        return deletedData;
    }
};

// Takes a unique selector, e.g. "#demo-1", and
// appends svg xml from svg_url, and takes graph
// info from json_url to highlight/annotate it.
svg_activate = function (selector, svg_url, json_url, scale) {

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
                    console.log(node.type)
                node.group = (node.type in resource_groups) ? resource_groups[node.type] : -1;
                nodes[node['label']] = node;
                svg_nodes.push(node);
            });

            // convenient to access edges by their source.
            var edges_by_source = {}
            for (var i in edges) {
                if(edges[i].source in edges_by_source)
                    edges_by_source[edges[i].source].push(edges[i]);
                else
                    edges_by_source[edges[i].source] = [edges[i]];
            }

            // convenient access to edges by their target.
            var edges_by_target = {}
            for (var i in edges) {
                if(edges[i].target in edges_by_target)
                    edges_by_target[edges[i].target].push(edges[i]);
                else
                    edges_by_target[edges[i].target] = [edges[i]];
            }

            var svg = container.select('svg');
            if (scale != null) {
                svg.attr('height', scale).attr('width', scale);
            }

            // setup tooltips
            var tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function (d) {
                    return title_html(d) + (d.definition.length == 0 ? child_html(d) : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>" + child_html(d));
                });
            svg.call(tip);

            // returns <div> element representinga  node's title and module namespace.
            var title_html = function(d) {
                var node = d;
                var title = [ '<div class="header">']
                if (node.modules.length <= 1 && node.modules[0] == 'root') {
                    title[title.length] = '<span class="title" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                    title[title.length] = '<span class="title" style="background:' + color(node.group) + ';">' + node.resource_name + '</span>';
                }
                else {
                    for (var i in node.modules) {
                        title[title.length] = '<span class="title" style="background: ' + color('(M) ' + node.modules[i]) + ';">' + node.modules[i] + '</span>';
                    }
                    title[title.length] = '<span class="title" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                    title[title.length] = '<span class="title" style="background:' + color(node.group) + ';">' + node.resource_name + '</span>';
                }
                title[title.length] = '</div>'
                return title.join('');
            }

            // returns <span> elements representing a node's direct children 
            var child_html = function(d) {
                var children = [];
                var edges   = edges_by_source[d.label];
                console.log(edges);
                for (i in edges) {
                    edge = edges[i];
                    if (edge.edge_type == edge_types.NORMAL || edge.edge_type == edge_types.HIDDEN) {
                        var node = nodes[edge.target];
                        if (node.modules.length <= 1 && node.modules[0] == 'root') {
                            children[children.length] = '<span class="dep" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                            children[children.length] = '<span class="dep" style="background:' + color(node.group) + ';">' + node.resource_name + '</span></br>';
                        }
                        else {
                            for (var i in node.modules) {
                                children[children.length] = '<span class="dep" style="background: ' + color('(M) ' + node.modules[i]) + ';">' + node.modules[i] + '</span>';
                            }
                            children[children.length] = '<span class="dep" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                            children[children.length] = '<span class="dep" style="background:' + color(node.group) + ';">' + node.resource_name + '</span></br>';
                        }

                    }
                }
                return children.join('');
            }

            var get_downstream_nodes = function (node) {
                var children    = {};
                children[node.label] = node;
                var visit_queue = new Queue();
                visit_queue.enqueue(node);
                while (visit_queue.size() > 0 ) {
                    var cur_node = visit_queue.dequeue();
                    var edges    = edges_by_source[cur_node.label];
                    for (var i in edges) {
                        if (edges[i].target in children)
                            continue;
                        var n = nodes[edges[i].target];
                        children[n.label] = n;
                        visit_queue.enqueue(n);
                    }
                }
                return to_list(children);
            }

            var get_upstream_nodes = function (node) {
                var parents = {};
                parents[node.label] = node;
                var visit_queue = new Queue();
                visit_queue.enqueue(node);
                while (visit_queue.size() > 0) {
                    var cur_node = visit_queue.dequeue();
                    var edges    = edges_by_target[cur_node.label];
                    for (var i in edges) {
                        if (edges[i].source in parents)
                            continue;
                        var n = nodes[edges[i].source];
                        parents[n.label] = n;
                        visit_queue.enqueue(n);
                    }
                }
                return to_list(parents);
            }

            var get_downstream_edges = function(node) {
                var ret_edges   = new Set();
                var children    = new Set();
                var visit_queue = new Queue();

                visit_queue.enqueue(node);
                while (visit_queue.size() > 0) {
                    var cur_node = visit_queue.dequeue();
                    var edges    = edges_by_source[cur_node.label];
                    for (var i in edges) {
                        e = edges[i];
                        if (e in ret_edges || e.edge_type == edge_types.HIDDEN || e.edge_type == edge_types.LAYOUT_HIDDEN)
                            continue;
                        var n = nodes[edges[i].target];
                        ret_edges.add(e);
                        children.add(n);
                        visit_queue.enqueue(n);
                    }
                }
                return Array.from(ret_edges);
            }

            var get_upstream_edges = function(node) {
                var ret_edges   = new Set();
                var parents     = new Set();
                var visit_queue = new Queue();

                visit_queue.enqueue(node);
                while (visit_queue.size() > 0) {
                    var cur_node = visit_queue.dequeue();
                    var edges    = edges_by_target[cur_node.label];
                    for (var i in edges) {
                        e = edges[i];
                        if (e in ret_edges || e.edge_type == edge_types.HIDDEN || e.edge_type == edge_types.LAYOUT_HIDDEN)
                            continue;
                        var n = nodes[edges[i].source];
                        ret_edges.add(e);
                        parents.add(n);
                        visit_queue.enqueue(n);
                    }
                }
                return Array.from(ret_edges);
            }

            //
            // mouse event handling
            //
            //  * 1st click (and mouseover): highlight downstream connections, only + tooltip
            //  * 2nd click: highlight upstream and downstream connections + no tooltip
            //  * 3rd click: return to normal (no-selection/highlights)
            //

            var click_count = 0;
            var sticky_node = null;

            var node_mousedown = function(d) {
                if (sticky_node == d && click_count == 1) {
                    tip.hide(d);
                    highlight(d, true, true);
                    click_count += 1;
                }
                else if (sticky_node == d && click_count == 2) {
                    unhighlight(d);
                    tip.hide(d);
                    sticky_node = null;
                    click_count = 0;
                }
                else {
                    if (sticky_node) {
                        unhighlight(sticky_node);
                        tip.hide(sticky_node);
                    }                    
                    sticky_node = d;
                    click_count = 1;
                    highlight(d, true, false);
                    tip.show(d)
                        .direction(tipdir(d))
                        .offset(tipoff(d));
                }
            }

            var node_mouseover = function(d) {
                tip.show(d)
                    .direction(tipdir(d))
                    .offset(tipoff(d));
                if (! sticky_node)
                    highlight(d, true, false);
            }

            var node_mouseout = function(d) {
                if (sticky_node == d) {
                    return;
                }
                else if (! sticky_node) {
                    unhighlight(d);
                    tip.hide(d);
                }
                else {
                    tip.hide(d);
                    if (click_count == 2)
                        highlight(sticky_node, true, true);
                    else
                        highlight(sticky_node, true, false);
                }

            }

            var tipdir = function(d) {
                return 'n';
            }

            var tipoff = function(d) {
                return [-10, 0];
            }

            var highlight = function (d, downstream, upstream) {

                var highlight_nodes = [];
                var highlight_edges = [];

                if (downstream) {
                    highlight_nodes     = highlight_nodes.concat(get_downstream_nodes(d));
                    highlight_edges     = highlight_edges.concat(get_downstream_edges(d));
                }

                if (upstream) {
                    highlight_nodes     = highlight_nodes.concat(get_upstream_nodes(d));
                    highlight_edges     = highlight_edges.concat(get_upstream_edges(d));
                }

                svg.selectAll('g.node')
                    .data(highlight_nodes, function (d) { return (d && d.svg_id) || d3.select(this).attr("id"); })
                    .attr('opacity', 1.0)
                    .exit()
                    .attr('opacity', 0.2);

                svg.selectAll('g.edge')
                    .data(highlight_edges, function(d) { return d && d.svg_id || d3.select(this).attr("id"); })
                    .attr('opacity', 1.0)
                    .exit()
                    .attr('opacity', 0.0);
            }

            var unhighlight = function (d) {
                svg.selectAll('g.node')
                    .attr('opacity', 1.0);
                svg.selectAll('g.edge')
                    .attr('opacity', 1.0)

            }

            // colorize nodes, and add mouse candy.
            svg.selectAll('g.node')
                .data(svg_nodes, function (d) {
                    return (d && d.svg_id) || d3.select(this).attr("id");
                })
                .on('mouseover', node_mouseover)
                .on('mouseout', node_mouseout)
                .on('mousedown', node_mousedown)
                .attr('fill', function (d) { return color(d.group); })
                .select('polygon:nth-last-of-type(2)')
                .style('fill', (function (d) {
                    if (d)
                        return color(d.group);
                    else
                        return '#000';
                }));

            // colorize modules
            svg.selectAll('polygon')
            .each(function(d, i) {
                if (d != undefined)
                    return undefined;
                sibling = this.nextElementSibling;
                if (sibling) {
                    if(sibling.innerHTML.match(/\(M\)/)) {
                        this.setAttribute('fill', color(sibling.innerHTML));
                    }
                }
            });

            // hack to make mouse events and coloration work on the root node again.
            var root = nodes['[root] root'];
            svg.selectAll('g.node#' + root.svg_id)
                .data(svg_nodes, function (d) {
                    return (d && d.svg_id) || d3.select(this).attr("id");
                })
                .on('mouseover', node_mouseover)
                .on('mouseout', node_mouseout)
                .on('mousedown', node_mousedown)
                .select('polygon')
                .attr('fill', function (d) { return color(d.group); })
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

