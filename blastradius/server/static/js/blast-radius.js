//
// terraform-graph.js 
//

// enumerate the various kinds of edges that Blast Radius understands.
// only NORMAL and LAYOUT_SHOWN will show up in the <SVG>, but all four
// will likely appear in the json representation.
var edge_types = {
    NORMAL        : 1, // what we talk about when we're talking about edges.
    HIDDEN        : 2, // these are normal edges, but aren't drawn.
    LAYOUT_SHOWN  : 3, // these edges are drawn, but aren't "real" edges
    LAYOUT_HIDDEN : 4, // these edges are not drawn, aren't "real" edges, but inform layout.
}

// Sometimes we have escaped newlines (\n) in json strings. we want <br> instead.
// FIXME: much better line wrapping is probably possible.
var replacer = function (key, value) {
    if (typeof value == 'string') {
        return value.replace(/\n/g, '<br>');
    }
    return value;
}

build_uri = function(url, params) {
    url += '?'
    for (var key in params)
        url += key + '=' + params[key] + '&';
    return url.slice(0,-1);
}

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
blastradius = function (selector, svg_url, json_url, br_state) {

    // TODO: remove scale.
    scale = null

    // mainly for d3-tips
    class_selector = '.' + selector.slice(1,selector.length);


    // we should have an object to keep track of state with, but if we
    // don't, just fudge one.
    if (! br_state) {
        var br_state = {};
    }

    // if we haven't already got an entry in br_state to manage our
    // state with, go ahead and create one.
    if (! br_state[selector]) {
        br_state[selector] = {};
    }

    var state     = br_state[selector];
    var container = d3.select(selector);

    // color assignments (resource_type : rgb) are stateful. If we use a new palette
    // every time the a subgraph is selected, the color assignments would differ and
    // become confusing.
    var color = (state['color'] ? state['color'] : d3.scaleOrdinal(d3['schemeCategory20']));
    state['color'] = color;

    //console.log(state);

    // 1st pull down the svg, and append it to the DOM as a child
    // of our selector. If added as <img src="x.svg">, we wouldn't
    // be able to manipulate x.svg with d3.js, or other DOM fns. 
    d3.xml(svg_url, function (error, xml) {

        container.node()
            .appendChild(document.importNode(xml.documentElement, true));

        // remove <title>s in svg; graphviz leaves these here and they
        // trigger useless tooltips.
        d3.select(selector).selectAll('title').remove();

        // remove any d3-tips we've left lying around
        d3.selectAll(class_selector + '-d3-tip').remove();

        // make sure the svg uses 100% of the viewport, so that pan/zoom works
        // as expected and there's no clipping.
        d3.select(selector + ' svg').attr('width', '100%').attr('height', '100%');

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
                if (node.label == '[root] root') { // FIXME: w/ tf 0.11.2, resource_name not set by server.
                    node.resource_name = 'root';
                }
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

            var render_tooltip = function(d) {
                var title_cbox  = document.querySelector(selector + '-tooltip-title');
                var json_cbox   = document.querySelector(selector + '-tooltip-json');
                var deps_cbox   = document.querySelector(selector + '-tooltip-deps');

                if ((! title_cbox) || (! json_cbox) || (! deps_cbox)) 
                    return title_html(d) + (d.definition.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>" + child_html(d));

                var ttip = ''; 
                if (title_cbox.checked)
                    ttip += title_html(d);
                if (json_cbox.checked)
                    ttip += (d.definition.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>");
                if (deps_cbox.checked)
                    ttip += child_html(d);
                return ttip;
            }

            // setup tooltips
            var tip = d3.tip()
                .attr('class', class_selector.slice(1, class_selector.length) + '-d3-tip d3-tip')
                .offset([-10, 0])
                .html(render_tooltip);
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

            // returns <div> element representing node's title and module namespace.
            // intended for use in an interactive searchbox. 
            var searchbox_listing = function(d) {
                var node = d;
                var title = [ '<div class="sbox-listings">']
                if (node.modules.length <= 1 && node.modules[0] == 'root') {
                    if (node.type)
                        title[title.length] = '<span class="sbox-listing" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                    title[title.length] = '<span class="sbox-listing" style="background:' + color(node.group) + ';">' + node.resource_name + '</span>';
                }
                else {
                    for (var i in node.modules) {
                        title[title.length] = '<span class="sbox-listing" style="background: ' + color('(M) ' + node.modules[i]) + ';">' + node.modules[i] + '</span>';
                    }
                    title[title.length] = '<span class="sbox-listing" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                    title[title.length] = '<span class="sbox-listing" style="background:' + color(node.group) + ';">' + node.resource_name + '</span>';
                }
                title[title.length] = '</div>'
                return title.join('');
            }

            // returns <span> elements representing a node's direct children 
            var child_html = function(d) {
                var children = [];
                var edges   = edges_by_source[d.label];
                //console.log(edges);
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

            // FIXME: these x,y,z-s pad out parameters I haven't looked up,
            // FIXME: but don't seem to be necessary for display
            var node_mousedown = function(d, x, y, z, no_tip_p) {
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
                    if (no_tip_p === undefined) {
                        tip.show(d)
                            .direction(tipdir(d))
                            .offset(tipoff(d));
                    }
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

            // blast-radius --serve mode stuff. check for a zoom-in button as a proxy
            // for whether other facilities will be available.
            if (d3.select(selector + '-zoom-in')) {
                var zin_btn      = document.querySelector(selector + '-zoom-in');
                var zout_btn     = document.querySelector(selector + '-zoom-out');
                var refocus_btn  = document.querySelector(selector + '-refocus');
                var download_btn = document.querySelector(selector + '-download')
                var svg_el       = document.querySelector(selector + ' svg');
                var panzoom      = svgPanZoom(svg_el).disableDblClickZoom();

                console.log('bang');
                console.log(state);
                if (state['no_scroll_zoom'] == true) {
                    console.log('bang');
                    panzoom.disableMouseWheelZoom();
                }

                var handle_zin = function(ev){
                    ev.preventDefault();
                    panzoom.zoomIn();
                }
                zin_btn.addEventListener('click', handle_zin);

                var handle_zout = function(ev){
                    ev.preventDefault();
                    panzoom.zoomOut();
                }
                zout_btn.addEventListener('click', handle_zout);

                var handle_refocus = function() {
                    if (sticky_node) {
                        $(selector + ' svg').remove();
                        clear_listeners();
                        if (! state['params'])
                            state.params = {}
                        state.params.refocus = encodeURIComponent(sticky_node.label);

                        svg_url  = svg_url.split('?')[0];
                        json_url = json_url.split('?')[0];

                        blastradius(selector, build_uri(svg_url, state.params), build_uri(json_url, state.params), br_state);
                    }
                }

                // this feature is disabled for embedded images on static sites...
                if (refocus_btn) {
                    refocus_btn.addEventListener('click', handle_refocus);
                }

                var handle_download = function() {
                    // svg extraction and download as data url borrowed from
                    // http://bl.ocks.org/curran/7cf9967028259ea032e8
                    var svg_el        = document.querySelector(selector + ' svg')
                    var svg_as_xml    = (new XMLSerializer).serializeToString(svg_el);
                    var svg_data_url  = "data:image/svg+xml," + encodeURIComponent(svg_as_xml);
                    var dl            = document.createElement("a");
                    document.body.appendChild(dl);
                    dl.setAttribute("href", svg_data_url);
                    dl.setAttribute("download", "blast-radius.svg");
                    dl.click();
                }
                download_btn.addEventListener('click', handle_download);

                var clear_listeners = function() {
                    zin_btn.removeEventListener('click', handle_zin);
                    zout_btn.removeEventListener('click', handle_zout);
                    refocus_btn.removeEventListener('click', handle_refocus);
                    download_btn.removeEventListener('click', handle_download);
                    panzoom = null;

                    //
                    tip.hide();
                }

                var render_searchbox_node = function(d) {
                    return searchbox_listing(d);
                }
                
                var select_node = function(d) {
                    if (d === undefined || d.length == 0) {
                        return true;
                    }
                    // FIXME: these falses pad out parameters I haven't looked up,
                    // FIXME: but don't seem to be necessary for display
                    if (sticky_node) {
                        unhighlight(sticky_node);
                        sticky_node = null;
                    }
                    click_count = 0;
                    node_mousedown(nodes[d], false, false, false, true);
                }

                if ( $(selector + '-search.selectized').length > 0 ) {
                    $(selector + '-search').selectize()[0].selectize.clear();
                    $(selector + '-search').selectize()[0].selectize.clearOptions();
                    for (var i in svg_nodes) {
                        //console.log(svg_nodes[i]);
                        $(selector + '-search').selectize()[0].selectize.addOption(svg_nodes[i]);
                    }
                    if( state.params.refocus && state.params.refocus.length > 0  ) {
                        var n = state.params.refocus;
                    }

                    // because of scoping, we need to change the onChange callback to the new version
                    // of select_node(), and delete the old callback associations.
                    $(selector + '-search').selectize()[0].selectize.settings.onChange = select_node;
                    $(selector + '-search').selectize()[0].selectize.swapOnChange();
                }
                else {
                    $(selector + '-search').selectize({
                        valueField: 'label',
                        searchField: ['label'],
                        maxItems: 1,
                        create: false,
                        multiple: false,
                        maximumSelectionSize: 1,
                        onChange: select_node,
                        render: {
                            option: render_searchbox_node,
                            item : render_searchbox_node
                        },
                        options: svg_nodes
                    });
                }

                // without this, selecting an item with <enter> will submit the form
                // and force a page refresh. not the desired behavior.
                $(selector + '-search-form').submit(function(){return false;});

            } // end if(interactive)
        });   // end json success callback
    });       // end svg scuccess callback

}             // end blastradius()

