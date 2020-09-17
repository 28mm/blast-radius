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

blastradiusnew = function (selector, svg_url, json_url,br_state) {

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

    // console.log(color);

    // 1st pull down the svg, and append it to the DOM as a child
    // of our selector. If added as <img src="x.svg">, we wouldn't
    // be able to manipulate x.svg with d3.js, or other DOM fns. 
    d3.xml(svg_url, function (error, xml) {

        d3.select(selector).selectAll("svg").remove();

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
            
            
            x=svg.selectAll('g.node');
            console.log('g.node')
            
            var render_plan = function(d) {
                var plan_title = "plan info"
                var ttip = ''; 
                ttip += title_html(d);
                ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + plan_title + '</span><br><br>'+(d.plan.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.plan, replacer, 2) + "</p><br>"+ '<hr style="background-color:black"/>') ;
                ttip += child_html(d);
                
               
                return ttip;
            }

            var render_cost = function(d) {
                var cost_title = "cost info"
                var ttip = ''; 
                ttip += title_html(d);
                ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + cost_title + '</span><br><br>'+(d.cost.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.cost, replacer, 2) + "</p><br>"+ '<hr style="background-color:black"/>') ;
                ttip += child_html(d);
                
               
                return ttip;
            }

            var render_policy = function(d) {
                var policy_title = "policy info"
                var ttip = ''; 
                ttip += title_html(d);
                ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + policy_title + '</span><br><br>'+(d.policy.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.policy, replacer, 2) + "</p><br>"+ '<hr style="background-color:black"/>');
                ttip += child_html(d);  
                return ttip;
            }

            var render_apply = function(d) {
                var apply_title = "apply info"
                var ttip = ''; 
                ttip += title_html(d);
                if (d.apply == "not yet applied" )
                {
                    ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + apply_title + '</span><br><br>'+("<p class='explain'>" + "not yet applied" + "</p><br>"+ '<hr style="background-color:black"/>');
                }
                else {
                    if( d.apply == null || d.apply.instances[0] == null)
                    {
                        ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + apply_title + '</span><br><br>'+("<p class='explain'>" + "resource apply failed" + "</p><br>"+ '<hr style="background-color:black"/>');
                    }
                    else
                    {
                         ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + apply_title + '</span><br><br>'+(d.apply.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.apply, replacer, 2) + "</p><br>"+ '<hr style="background-color:black"/>');
                    }
                }
                ttip += child_html(d);
                return ttip;
            }

            var render_tfstate = function(d) {
                var title = "tf state info"
                var ttip = ''; 
                ttip += title_html(d);
                ttip += '<hr style="background-color:black"/><br><span class="title" style="background:' + color("#ffbf00") + ';">' + title + '</span><br><br>' +(d.definition.length == 0 ? '' : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>"+ '<hr style="background-color:black"/>');
                ttip += child_html(d);
                return ttip;
            }
      
            var title_html = function(d) {
                var node = d;
                var title = [ '<div class="header">']
                var head = "resource name"
                title[title.length] = '<span class="title" style="background:' + color("#ffbf00") + ';">' + head + '</span><br><br>';
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
                var foot = "child nodes";
                //console.log(edges);
                children[children.length] = '<span class="title" style="background:' + color("#ffbf00") + ';">' + foot + '</span><br><br>';
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
                
                if ( sticky_node == d && click_count == 1) {
                   
                    highlight(d, true, true);
                    click_count += 1;
                }
                else if (sticky_node == d && click_count == 2) {
                    unhighlight(d);
                   
                   sticky_node = null;
                    click_count = 0;
                }
                else {
                    if (sticky_node) {
                        unhighlight(sticky_node);
                      
                    }
                    sticky_node = d;
                    click_count = 1;
                    highlight(d, true, false);
                }
            }
            
            var plan_click = function(d) {
               openNav()

               var renderInfo = render_plan(d);
               $('div.test').html(renderInfo);
               
            }

            var tfstate_click = function(d) {
                openNav()
 
                var renderInfo = render_tfstate(d);
                $('div.test').html(renderInfo);
                
             }

            var apply_click = function(d) {
                openNav()
 
                var renderInfo = render_apply(d);
                $('div.test').html(renderInfo);
                
             }

             var cost_click = function(d) {
                openNav()
 
                var renderInfo = render_cost(d);
                $('div.test').html(renderInfo);
                
             }

             var policy_click = function(d) {
                openNav()
 
                var renderInfo = render_policy(d);
                $('div.test').html(renderInfo);
                
             }
            
            function openNav() {
                document.getElementById("mySidenav").style.width = "350px";
                
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


            node = svg.selectAll('g.node')
                   .data(svg_nodes, function (d) {
                        return (d && d.svg_id) || d3.select(this).attr("id");
                    })

            

            
            node.attr('fill', function (d) { return color(d.group); })
                .select('polygon:nth-of-type(1)')
                .on('click', node_mousedown)
                .style('fill', (function (d) {
                    if (d)
                        return color(d.group);
                        
                    else
                        return '#000';
                }));

            
            node.select('polygon:nth-of-type(3)')
                .on('click',(function (d) {
                    
                      return tfstate_click(d);
                  
            }))
                .style('fill', (function (d) {
                    if (d)
                      
                        return "#00CCFF";
                        
                    else
                        return '#000';
                }));

            
            node.attr('fill', function (d) { return color(d.group); })
                .select('polygon:nth-of-type(4)')
                .on('click',(function (d) {
                    
                      if (d.type == "var" || d.type == "provider" || d.type == "meta" || d.type == "output")
                        return "";
                        
                      else
                        return plan_click(d);
                    
                }))
                .style('fill', (function (d) {
                    if (d)
                    {
                    if (d.type == "var" || d.type == "provider" || d.type == "meta" || d.type == "output")
                        
                        return "fff";
                    else
                       return "#ffff00";

                    }
                        
                    else
                        return '#000';
                }));
  
            
            node.select('polygon:nth-of-type(5)')
                .on('click',apply_click)
                .style('fill', (function (d) {
                    if (d)
                    {
                     if(d.apply == "not yet applied")
                      {
                          return "#808080";
                      }
                     else if(d.apply == null || d.apply.instances == null )
                      {
                        return "#ff0000";
                      }
                      else{
                        return "#00ff40";
                      }
                    }   
                    else
                        return '#000';
                }));

            
            node.select('polygon:nth-of-type(6)')
                    .on('click',cost_click)
                    .style('fill', (function (d) {
                        if (d)
                      
                        if(d.cost == "no cost available" || d.cost == null)
                        {
                          return "#808080";
                        }
                        else{
                          return "#fff";
                        }
                        
                        else
                            return '#000';
                    }));
            
            
            node.select('polygon:nth-of-type(7)')

                    .on('click',policy_click)
                    .style('fill', (function (d) {
                            if (d){
                                if(d.policy == "no policy available" || d.policy == null)
                                {
                                  return "#808080";
                                }
                                else if(d.policy != null && d.policy.decision == "failed" )
                                {
                                  return "#ff0000";
                                }
                                else{
                                  return "#00ff40";
                                }
            
                            }   
                                else
                                    return '#000';
                            }));
                    
                    
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
            var refocus_btn  = document.querySelector(selector + '-refocus');
            if (d3.select(selector + '-zoom-in')) {
                var zin_btn      = document.querySelector(selector + '-zoom-in');
                var zout_btn     = document.querySelector(selector + '-zoom-out');
                // var refocus_btn  = document.querySelector(selector + '-refocus');
                var download_btn = document.querySelector(selector + '-download')
                var svg_el       = document.querySelector(selector + ' svg');
                var panzoom      = svgPanZoom(svg_el).disableDblClickZoom();

                
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
                    console.log('handle_refocus', sticky_node)
                    if (sticky_node) {
                        
                        $(selector + ' svg').remove();
                        clear_listeners();
                        if (! state['params'])
                            state.params = {}
                        state.params.refocus = encodeURIComponent(sticky_node.label);

                        svg_url  = svg_url.split('?')[0];
                        json_url = json_url.split('?')[0];

                        blastradiusnew(selector, build_uri(svg_url, state.params), build_uri(json_url, state.params), br_state);
                    }
                }


                // this feature is disabled for embedded images on static sites...
                if (refocus_btn) {
                    console.log('refocus_btn.addEventListener');
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
                    dl.setAttribute("download", "blast-radius-new.svg");
                    dl.click();
                }
                download_btn.addEventListener('click', handle_download);

                var clear_listeners = function() {
                    zin_btn.removeEventListener('click', handle_zin);
                    zout_btn.removeEventListener('click', handle_zout);
                    refocus_btn.removeEventListener('click', handle_refocus);
                    download_btn.removeEventListener('click', handle_download);
                    panzoom = null;
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
                    // console.log(d)
                    node_mousedown(nodes[d], false, false, false, true);
                }

                if ( $(selector + '-search.selectized').length > 0 ) {
                    $(selector + '-search').selectize()[0].selectize.clear();
                    $(selector + '-search').selectize()[0].selectize.clearOptions();
                    for (var i in svg_nodes) {
                        
                        $(selector + '-search').selectize()[0].selectize.addOption(svg_nodes[i]);
                    }
                    if( state && state.params && state.params.refocus && state.params.refocus.length > 0  ) {
                        var n = state.params.refocus;
                    }
                    console.log(svg_nodes);
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