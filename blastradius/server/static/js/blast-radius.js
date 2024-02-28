//
// terraform-graph.js 
//

// enumerate the various kinds of edges that Blast Radius understands.
// only NORMAL and LAYOUT_SHOWN will show up in the <SVG>, but all four
// will likely appear in the json representation.
const edge_types = {
    NORMAL: 1, // what we talk about when we're talking about edges.
    HIDDEN: 2, // these are normal edges, but aren't drawn.
    LAYOUT_SHOWN: 3, // these edges are drawn, but aren't "real" edges
    LAYOUT_HIDDEN: 4, // these edges are not drawn, aren't "real" edges, but inform layout.
}

// Sometimes we have escaped newlines (\n) in json strings. we want <br> instead.
// FIXME: much better line wrapping is probably possible.
var replacer = function (key, value) {
    if (typeof value == 'string') {
        return value.replace(/\n/g, '<br>');
    }
    return value;
}

build_uri = function (url, params) {
    url += '?'
    for (var key in params)
        url += key + '=' + params[key] + '&';
    return url.slice(0, -1);
}

let uploadRequest = (url, formData, selector) => {

    fetch(url, {
        method: "POST",
        body: formData
    })
        .then(response => (response.json()))
        .then(async function (resjson) {
            let br_state = {
                selector: {}
            }

            xml = $.parseXML(resjson.SVG);
            json = JSON.parse(resjson.JSON);
            await blastradius(selector, '/graph.svg', '/graph.json', br_state, xml, json)
        });
}

let uploadFile = function (file, tabNumber) {
    let fileType = file.type;
    let selector = "#graph-" + tabNumber;
    let validExtensions = ["text/plain"];
    if (validExtensions.includes(fileType)) {
        let formData = new FormData();
        formData.set('file', file);
        uploadRequest('/upload', formData, selector)
    } else {
        alert("This is not a valid File!");
    }
}

let inputGraph = async () => {
    let graphinput = prompt("Please paste Graphviz DOT script ");

    if (graphinput != null) {
        let lastTabContent = $("div.tabcontent").last()[0]
        if (lastTabContent != null) {
            let prevNumber = parseInt(lastTabContent.id.split("-")[1])
            let curNumber = parseInt(prevNumber) + 1
            let selector = "#graph-" + curNumber;
            await insertTabContent(prevNumber)
            await createTab(`input-graph${curNumber}`, curNumber);

            let formData = new FormData();
            formData.set('input', graphinput);

            await uploadRequest('/input', formData, selector);

            $('#tablink-' + curNumber).click();
        } else {
            console.log("Last tab's content could not be retrieved.")
        }

    } else {
        alert("Invalid graph input or empty input!")
    }
}
/**
 * @param {string} filename - The filename
 * @param {int} tabNumber - The number of the tab (can be found in ID of tab)
 */
let createTab = (filename, tabNumber) => {
    let newTab = `<li class="nav-item nav-item-tab" id="nav-item-${tabNumber}">
                <div class="tabdiv" id="tabdiv-${tabNumber}" style="display: flex;">
                <button class="btn btn-primary btn-animate tablink" id="tablink-${tabNumber}" title="${filename}">
                ${filename}
                </button>
                <button class="btn btn-primary btn-animate tablink close-tab" id="close-tab-${tabNumber}" title="close tab ${filename}">
                    <i class="fas fa-times"></i>
                </button></div></li>`;

    $('ul.navbar-nav.tab-ul').append(newTab);
    var x = Math.round(0xffffff * Math.random()).toString(16);
    var y = (6 - x.length);
    var z = "000000".substring(0, y);
    var randomColor = "#" + z + x;
    $('#tablink-' + tabNumber).css("color", "white");
    $('#close-tab-' + tabNumber).css("color", "white")

    document.getElementById("tablink-" + tabNumber).onclick = function () {
        displayTabContent(tabNumber, randomColor)
    }
    document.getElementById("close-tab-" + tabNumber).onclick = function () {
        closeTab(tabNumber);
    }

    let firstTabNum = parseInt($("div.tabcontent").first()[0].id.split("-")[1])
    let firstXButton = $(`#close-tab-${firstTabNum}`);

    //If the first tab's X has been removed
    if (firstXButton.prop("disabled") || firstXButton.prop("hidden")) {
        firstXButton.prop("disabled", false);
        firstXButton.prop("hidden", false);
    }

}

let displayTabContent = (tabNumber, color) => {
    let tabContents = document.getElementsByClassName("tabcontent");
    let tabLinks = document.getElementsByClassName("tablink");
    let closeTabs = document.getElementsByClassName("close-tab");
    let currentTab = $('#tablink-' + tabNumber)
    let currentTabContent = $('#tab-' + tabNumber)
    let currentCloseTab = $('#close-tab-' + tabNumber)

    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
    }

    for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].style.backgroundColor = "";
        tabLinks[i].style.color = "#5256ad";
    }

    for (let i = 0; i < closeTabs.length; i++) {
        closeTabs[i].style.backgroundColor = "";
        closeTabs[i].style.color = "#5256ad";
    }

    currentTabContent.css("display", "block");
    currentCloseTab.css("background-color", color);
    currentCloseTab.css("color", "white");
    currentTab.css("background-color", color);
    currentTab.css("color", "white");
    currentTab.addClass("open-tab");
}
/**
 * @param {int} tabNumber - The tab number
 */
let closeTab = (tabNumber) => {

    $(`#tab-${tabNumber}`).remove();
    $(`#nav-item-${tabNumber}`).remove();
    $(`.graph-${tabNumber}-d3-tip`).remove();

    let newLastTabNum = parseInt($("div.tabcontent").last()[0].id.split("-")[1])
    $(`#tablink-${newLastTabNum}`).click(); //open last tab

    let xButton = $(`#close-tab-${newLastTabNum}`)
    //If there's only one tab left after closing the current tab  (first element == last element)
    if ($("div.tabcontent").last()[0] === $("div.tabcontent").first()[0]) {
        xButton.prop("disabled", true);
        xButton.prop("hidden", true);
    }

}

let insertTabContent = (prevNumber) => {
    let curNum = prevNumber + 1
    let graphSelector = 'graph-' + curNum
    let helpButton = $(`#tab-${prevNumber}`).children("nav").children("ul").children("li").last().children("div.dropdown").parent()[0].innerHTML
    let topNavBar = '<!-- navigation and controls -->' +
        '            <nav class="navbar fixed-top navbar-expand bg-light">' +
        '                <ul class="navbar-nav">' +
        '                    <li class="nav-item">' +
        '                        <form class="form-inline my-2 my-lg-0 graph-search-form" id="' + graphSelector + '-search-form">' +
        '                            <select style="width: 400px;" id="' + graphSelector + '-search"></select>' +
        '                        </form></li>' +
        '                    <li class="nav-item">' +
        '                        <button class="btn btn-danger graph-refocus" id="' + graphSelector + '-refocus" title="prune to selection">&nbsp;<i' +
        '                                class="fas fa-code-branch"></i></button>' +
        '                    </li>' +
        '                    <li class="nav-item">' +
        '                        <button class="btn btn-primary graph-zoom-out" id="' + graphSelector + '-zoom-out" title="zoom out">&nbsp;<i' +
        '                                class="fas fa-search-minus"></i></button>' +
        '                    </li>' +
        '                    <li class="nav-item">' +
        '                        <button class="btn btn-primary graph-zoom-in" id="' + graphSelector + '-zoom-in" title="zoom in">&nbsp;<i' +
        '                                class="fas fa-search-plus"></i></button>' +
        '                    </li>' +
        '                    <li class="nav-item">' +
        '                        <button class="btn btn-primary graph-download" id="' + graphSelector + '-download" title="download svg">&nbsp;<i' +
        '                                class="fas fa-download"></i></button>' +
        '                    </li>' +
        '                    <li class="nav-item">' +
        '                        <button class="btn btn-primary btn-animate graph-upload" id="' + graphSelector + '-upload" title="upload ">&nbsp;<i' +
        '                                class="fas fa-cloud-upload-alt"></i>' +
        '                        </button>' +
        '                        <input type="file" class = "graph-input-upload" id="' + graphSelector + '-input-upload" hidden>' +
        '                    </li>' +
        '                    <li class="nav-item">' +
        '                        <button class="btn btn-primary btn-animate graph-text-input" id="' + graphSelector + '-text-input" title="input" onclick = "inputGraph()">&nbsp;<i' +
        '                                class="fas fa-keyboard"></i>' +
        '                        </button> </li>' +
        '              <li class="nav-item">' +
        '                        <div class="btn-group">' +
        '                            <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown"' +
        '                                aria-haspopup="true" aria-expanded="false" title="tooltip options">' +
        '                                <i class="fas fa-magic"></i>' +
        '                            </button>' +
        '                            <div class="dropdown-menu">' +
        '                                <div class="dropdown-item">' +
        '                                    <label><b>Tooltip Options</b></label>' +
        '                                </div>' +
        '                                <div class="dropdown-divider"></div>' +
        '                                <!-- Resource Name-->' +
        '                                <div class="dropdown-item form-check">' +
        '                                    <label class="form-check-label">' +
        '                                        <input class="form-check-input graph-tooltip-title" type="checkbox" value=""' +
        '                                            id="' + graphSelector + '-tooltip-title" checked>' +
        '                                        Resource Name' +
        '                                    </label></div>' +

        '<div class="dropdown-item form-check">' +
        '<label class="form-check-label">' +
        '<input class="form-check-input" type="checkbox" value="" class="graph-tooltip-json" id="' + graphSelector + '-tooltip-json"' +
        '                                            checked>' +
        '                                        JSON Definition' +
        '</label></div>' +

        '<div class="dropdown-item form-check">' +
        '<label class="form-check-label">' +
        '<input class="form-check-input graph-tooltip-deps" type="checkbox" value="" id="' + graphSelector + '-tooltip-deps" checked>' +
        'Dependencies</label></div></div></div></li>' +
        `<li class="nav-item"><button class="btn btn-primary graph-print" id="` + graphSelector + `-print" title="print this page">&nbsp;<i
                class="fas fa-print"></i></button></li>` + `<li class="nav-item">` + helpButton + `</li>` + `</ul></nav>` +
        `<div class="container" height="70"></div>`

    let newTabContentDiv = '<div id="tab-' + curNum + '" class="tabcontent"></div>'
    let newTabGraph = '<div id="' + graphSelector + '" class="graph"></div>'
    $('.drag-area').append(newTabContentDiv);
    $(`#tab-${curNum}`).append(topNavBar, newTabGraph);


}

var to_list = function (obj) {
    var lst = [];
    for (var k in obj)
        lst.push(obj[k]);
    return lst;
}

var Queue = function () {
    this._oldestIndex = 1;
    this._newestIndex = 1;
    this._storage = {};
}

Queue.prototype.size = function () {
    return this._newestIndex - this._oldestIndex;
};

Queue.prototype.enqueue = function (data) {
    this._storage[this._newestIndex] = data;
    this._newestIndex++;
};

Queue.prototype.dequeue = function () {
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
blastradius = function (selector, svg_url, json_url, br_state = {}, uploadXML = null, uploadJSON = null) {

    if ((uploadJSON == null && uploadXML != null) || (uploadJSON != null && uploadXML == null)) {
        return
    }

    // TODO: remove scale.
    scale = null

    // mainly for d3-tips
    class_selector = '.' + selector.slice(1, selector.length);

    // if we haven't already got an entry in br_state to manage our
    // state with, go ahead and create one.
    if (!br_state[selector]) {
        br_state[selector] = {};
    }

    var state = br_state[selector];
    var container = d3.select(selector);

    // color assignments (resource_type : rgb) are stateful. If we use a new palette
    // every time the a subgraph is selected, the color assignments would differ and
    // become confusing.
    var color = (state['color'] ? state['color'] : d3.scaleOrdinal(d3['schemeCategory20']));
    state['color'] = color;

    // 1st pull down the svg, and append it to the DOM as a child
    // of our selector. If added as <img src="x.svg">, we wouldn't
    // be able to manipulate x.svg with d3.js, or other DOM fns.
    d3.xml(svg_url, function (error, xml) {

        if (uploadXML != null) {
            xml = uploadXML;
        }

        container.node()
            .appendChild(document.importNode(xml.documentElement, true));

        // The xml.documentElement node by default imports a <g> element under <svg> that has an id of "graph0",
        //which may causes problems like inability to upload a file with the same filename,
        // so the code below replaces the id to a unique value
        let repetitiveId = $(`${selector}`).children("svg").children("g#graph0.graph")[0].id
        $(`#${repetitiveId}`).prop("id", `graph${selector.substring(selector.indexOf('-') + 1)}`);

        // remove <title>s in svg; graphviz leaves these here and they
        // trigger useless tooltips.
        d3.select(selector).selectAll('title').remove();

        // remove any d3-tips we've left lying around
        d3.selectAll(class_selector + '-d3-tip').remove();

        // make sure the svg uses 100% of the viewport, so that pan/zoom works
        // as expected and there's no clipping.
        d3.select(selector + ' svg').attr('width', '100%').attr('height', '100%');

        // Obtain the graph description. Doing this within the
        // d3.xml success callback, to gurantee the svg/xml
        // has loaded.
        d3.json(json_url, function (error, data) {

            if (uploadJSON !== null) {
                data = uploadJSON
            }

            if (error) {
                console.error("No Terraform files were found, so JSON details will not be available. The graph is still usable but without all features enabled such as filtering content");
                // alert("No Terraform files were found, so JSON details will not be available. The graph is still usable but without all features enabled such as filtering content");
            }

            // if (!error) {
            var edges = data.edges;
            var svg_nodes = [];
            var nodes = {};
            data.nodes.forEach(function (node) {
                if (!(node.type in resource_groups))
                    if (node.label === '[root] root') { // FIXME: w/ tf 0.11.2, resource_name not set by server.
                        node.resource_name = 'root';
                    }
                node.group = (node.type in resource_groups) ? resource_groups[node.type] : -1;
                nodes[node['label']] = node;
                svg_nodes.push(node);
            });


            // convenient to access edges by their source.
            var edges_by_source = {}
            for (let i in edges) {
                if (edges[i].source in edges_by_source)
                    edges_by_source[edges[i].source].push(edges[i]);
                else
                    edges_by_source[edges[i].source] = [edges[i]];
            }

            // convenient access to edges by their target.
            var edges_by_target = {}
            for (let i in edges) {
                if (edges[i].target in edges_by_target)
                    edges_by_target[edges[i].target].push(edges[i]);
                else
                    edges_by_target[edges[i].target] = [edges[i]];
            }

            var svg = container.select('svg');
            if (scale != null) {
                svg.attr('height', scale).attr('width', scale);
            }

            var render_tooltip = function (d) {
                var title_cbox = document.querySelector(selector + '-tooltip-title');
                var json_cbox = document.querySelector(selector + '-tooltip-json');
                var deps_cbox = document.querySelector(selector + '-tooltip-deps');

                if ((!title_cbox) || (!json_cbox) || (!deps_cbox))
                    return title_html(d) + (d.definition.length === 0 ? '' : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>" + child_html(d));

                var ttip = '';
                if (title_cbox.checked)
                    ttip += title_html(d);
                if (json_cbox.checked)
                    ttip += (d.definition.length === 0 ? '' : "<p class='explain'>" + JSON.stringify(d.definition, replacer, 2) + "</p><br>");
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
            var title_html = function (d) {
                var node = d;
                var title = ['<div class="header">']
                if (node.modules.length <= 1 && node.modules[0] === 'root') {
                    title[title.length] = '<span class="title" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                    title[title.length] = '<span class="title" style="background:' + color(node.group) + ';">' + node.resource_name + '</span>';
                } else {
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
            var searchbox_listing = function (d) {
                var node = d;
                var title = ['<div class="sbox-listings">']
                if (node.modules.length <= 1 && node.modules[0] === 'root') {
                    if (node.type)
                        title[title.length] = '<span class="sbox-listing" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                    title[title.length] = '<span class="sbox-listing" style="background:' + color(node.group) + ';">' + node.resource_name + '</span>';
                } else {
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
            var child_html = function (d) {
                var children = [];
                var edges = edges_by_source[d.label];
                for (i in edges) {
                    edge = edges[i];
                    if (edge.edge_type == edge_types.NORMAL || edge.edge_type == edge_types.HIDDEN) {
                        var node = nodes[edge.target];
                        if (node.modules.length <= 1 && node.modules[0] === 'root') {
                            children[children.length] = '<span class="dep" style="background:' + color(node.group) + ';">' + node.type + '</span>';
                            children[children.length] = '<span class="dep" style="background:' + color(node.group) + ';">' + node.resource_name + '</span></br>';
                        } else {
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
                var children = {};
                children[node.label] = node;
                var visit_queue = new Queue();
                visit_queue.enqueue(node);
                while (visit_queue.size() > 0) {
                    var cur_node = visit_queue.dequeue();
                    var edges = edges_by_source[cur_node.label];
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
                    var edges = edges_by_target[cur_node.label];
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

            var get_downstream_edges = function (node) {
                var ret_edges = new Set();
                var children = new Set();
                var visit_queue = new Queue();

                visit_queue.enqueue(node);
                while (visit_queue.size() > 0) {
                    var cur_node = visit_queue.dequeue();
                    var edges = edges_by_source[cur_node.label];
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

            var get_upstream_edges = function (node) {
                var ret_edges = new Set();
                var parents = new Set();
                var visit_queue = new Queue();

                visit_queue.enqueue(node);
                while (visit_queue.size() > 0) {
                    var cur_node = visit_queue.dequeue();
                    var edges = edges_by_target[cur_node.label];
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
            var node_mousedown = function (d, x, y, z, no_tip_p) {
                if (sticky_node == d && click_count === 1) {
                    tip.hide(d);
                    highlight(d, true, true);
                    click_count += 1;
                } else if (sticky_node == d && click_count === 2) {
                    unhighlight(d);
                    tip.hide(d);
                    sticky_node = null;
                    click_count = 0;
                } else {
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

            var node_mouseleave = function (d) {
                tip.hide(d);
            }

            var node_mouseenter = function (d) {
                tip.show(d)
                    .direction(tipdir(d))
                    .offset(tipoff(d));
            }

            var node_mouseover = function (d) {
                if (!sticky_node)
                    highlight(d, true, false);
            }

            var node_mouseout = function (d) {
                if (sticky_node == d) {
                    return;
                } else if (!sticky_node) {
                    unhighlight(d);
                } else {
                    if (click_count === 2)
                        highlight(sticky_node, true, true);
                    else
                        highlight(sticky_node, true, false);
                }

            }

            var tipdir = function () {
                return 'n';
            }

            var tipoff = function () {
                return [-10, 0];
            }

            var highlight = function (d, downstream, upstream) {

                var highlight_nodes = [];
                var highlight_edges = [];

                if (downstream) {
                    highlight_nodes = highlight_nodes.concat(get_downstream_nodes(d));
                    highlight_edges = highlight_edges.concat(get_downstream_edges(d));
                }

                if (upstream) {
                    highlight_nodes = highlight_nodes.concat(get_upstream_nodes(d));
                    highlight_edges = highlight_edges.concat(get_upstream_edges(d));
                }

                svg.selectAll('g.node')
                    .data(highlight_nodes, function (d) {
                        return (d && d.svg_id) || d3.select(this).attr("id");
                    })
                    .attr('opacity', 1.0)
                    .exit()
                    .attr('opacity', 0.2);

                svg.selectAll('g.edge')
                    .data(highlight_edges, function (d) {
                        return d && d.svg_id || d3.select(this).attr("id");
                    })
                    .attr('opacity', 1.0)
                    .exit()
                    .attr('opacity', 0.0);
            }

            var unhighlight = function () {
                svg.selectAll('g.node')
                    .attr('opacity', 1.0);
                svg.selectAll('g.edge')
                    .attr('opacity', 1.0)

            }

            // colorize nodes, and add mouse candy.
            if (svg_nodes) {
                svg.selectAll('g.node')
                    .data(svg_nodes, function (d) {
                        return (d && d.svg_id) || d3.select(this).attr("id");
                    })
                    .on('mouseenter', node_mouseenter)
                    .on('mouseleave', node_mouseleave)
                    .on('mouseover', node_mouseover)
                    .on('mouseout', node_mouseout)
                    .on('mousedown', node_mousedown)
                    .attr('fill', function (d) {
                        return color(d.group);
                    })
                    .select('polygon:nth-last-of-type(2)')
                    .style('fill', (function (d) {
                        if (d)
                            return color(d.group);
                        else
                            return '#000';
                    }));
            } else {
                console.log("SVG nodes could not be colorized, and mouse functionality could not be added either.")
            }


            // colorize modules
            svg.selectAll('polygon')
                .each(function (d) {
                    if (d != undefined)
                        return undefined;
                    sibling = this.nextElementSibling;
                    if (sibling) {
                        if (sibling.innerHTML.match(/\(M\)/)) {
                            this.setAttribute('fill', color(sibling.innerHTML));
                        }
                    }
                });

            // hack to make mouse events and coloration work on the root node again.
            if (nodes) {
                var root = nodes['[root] root'];

                if (root == undefined) {
                    if (confirm("Invalid graph detected! Would you like to reload the page?") === true) {
                        window.location.reload()
                    }
                }

                svg.selectAll('g.node#' + root.svg_id)
                    .data(svg_nodes, function (d) {
                        return (d && d.svg_id) || d3.select(this).attr("id");
                    })
                    .on('mouseover', node_mouseover)
                    .on('mouseout', node_mouseout)
                    .on('mousedown', node_mousedown)
                    .select('polygon')
                    .attr('fill', function (d) {
                        return color(d.group);
                    })
                    .style('fill', (function (d) {
                        if (d)
                            return color(d.group);
                        else
                            return '#000';
                    }));
            } else {
                console.warn("Mouse events and coloration may not work due to nodes being undefined.")
            }

            // stub, in case we want to do something with edges on init.
            svg.selectAll('g.edge')
                .data(edges, function (d) {
                    return d && d.svg_id || d3.select(this).attr("id");
                });

            // blast-radius --serve mode stuff. check for a zoom-in button as a proxy
            // for whether other facilities will be available.
            if (d3.select(selector + '-zoom-in')) {
                let zin_btn = document.querySelector(selector + '-zoom-in');
                let zout_btn = document.querySelector(selector + '-zoom-out');
                let refocus_btn = document.querySelector(selector + '-refocus');
                let download_btn = document.querySelector(selector + '-download');
                let upload_btn = document.querySelector(selector + "-upload");
                let upload_input = document.querySelector(selector + "-input-upload");
                let svg_el = document.querySelector(selector + ' svg');
                let print_btn = document.querySelector(selector + '-print');
                let panzoom = svgPanZoom(svg_el).disableDblClickZoom();
                let dropArea = document.querySelector(".drag-area");
                let prevNumber = parseInt($("div.tabcontent").last()[0].id.split("-")[1]);


                if (prevNumber === 1) {
                    document.getElementById("tablink-1").onclick = function () {
                        displayTabContent(1, "#555")
                    }
                    document.getElementById("close-tab-1").onclick = function () {
                        closeTab(1, "#555")
                    }
                }

                if (state['no_scroll_zoom'] === true) {
                    panzoom.disableMouseWheelZoom();
                }

                var handle_zin = function (ev) {
                    ev.preventDefault();
                    panzoom.zoomIn();
                }
                zin_btn.addEventListener('click', handle_zin);

                var handle_zout = function (ev) {
                    ev.preventDefault();
                    panzoom.zoomOut();
                }
                zout_btn.addEventListener('click', handle_zout);

                var handle_refocus = function () {
                    if (sticky_node) {
                        $(selector + ' svg').remove();
                        clear_listeners();
                        if (!state['params']) {
                            state.params = {}
                        }
                        state.params.refocus = encodeURIComponent(sticky_node.label);

                        svg_url = svg_url.split('?')[0];
                        json_url = json_url.split('?')[0];

                        blastradius(selector, build_uri(svg_url, state.params), build_uri(json_url, state.params), br_state, uploadXML, uploadJSON);
                    }
                }

                // this feature is disabled for embedded images on static sites...
                if (refocus_btn) {
                    refocus_btn.addEventListener('click', handle_refocus);
                }

                var handle_download = function () {
                    // svg extraction and download as data url borrowed from
                    // http://bl.ocks.org/curran/7cf9967028259ea032e8
                    var svg_el = document.querySelector(selector + ' svg')
                    var svg_as_xml = (new XMLSerializer).serializeToString(svg_el);
                    var svg_data_url = "data:image/svg+xml," + encodeURIComponent(svg_as_xml);
                    var dl = document.createElement("a");
                    document.body.appendChild(dl);
                    dl.setAttribute("href", svg_data_url);
                    dl.setAttribute("download", "blast-radius.svg");
                    dl.click();
                }
                download_btn.addEventListener('click', handle_download);

                upload_btn.onclick = () => {
                    upload_input.click()
                }

                dropArea.addEventListener("dragover", (event) => {
                    console.log("dragover")
                    event.preventDefault(); //preventing from default behaviour
                    dropArea.classList.add("active");
                }, {
                    once: true
                });

                let handle_dragleave = () => {
                    console.log("dragleave")
                    dropArea.classList.remove("active");
                }
                dropArea.addEventListener("dragleave", handle_dragleave, {
                    once: true
                });

                dropArea.addEventListener("drop", function (event) {
                    console.log("drop")
                    event.preventDefault(); //preventing from default behaviour
                    event.stopImmediatePropagation();
                    //getting user select file and [0] this means if user select multiple files then we'll select only the first one
                    let file = event.dataTransfer.files[0];

                    handle_upload(file, file.name);
                }, {
                    once: true,
                    passive: false
                });

                var handle_upload = async (file, filename) => {
                    let prevNumber = parseInt($("div.tabcontent").last()[0].id.split("-")[1])
                    insertTabContent(prevNumber)
                    curNumber = parseInt(prevNumber) + 1
                    await createTab(filename, curNumber)
                    await uploadFile(file, curNumber);
                    $('#tablink-' + curNumber).click();
                }

                var handle_upload_input = async function () {
                    let file = this.files[0];
                    dropArea.classList.add("active");
                    handle_upload(file, file.name);
                }
                upload_input.addEventListener('change', handle_upload_input, {
                    once: true
                });

                var handle_print = function () {
                    window.print();
                }
                print_btn.addEventListener('click', handle_print)

                var clear_listeners = function () {
                    zin_btn.removeEventListener('click', handle_zin);
                    zout_btn.removeEventListener('click', handle_zout);
                    refocus_btn.removeEventListener('click', handle_refocus);
                    download_btn.removeEventListener('click', handle_download);
                    upload_input.removeEventListener('click', handle_upload);
                    print_btn.removeEventListener('click', handle_print)
                    panzoom = null;

                    //
                    tip.hide();
                }

                var render_searchbox_node = function (d) {
                    return searchbox_listing(d);
                }

                var select_node = function (d) {
                    if (d === undefined || d.length === 0) {
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

                if ($(selector + '-search.selectized').length > 0) {
                    $(selector + '-search').selectize()[0].selectize.clear();
                    $(selector + '-search').selectize()[0].selectize.clearOptions();

                    for (let i in svg_nodes) {
                        $(selector + '-search').selectize()[0].selectize.addOption(svg_nodes[i]);
                    }
                    // if (state.params.refocus && state.params.refocus.length > 0) {
                    //     var n = state.params.refocus;
                    // }

                    // because of scoping, we need to change the onChange callback to the new version
                    // of select_node(), and delete the old callback associations.
                    $(selector + '-search').selectize()[0].selectize.settings.onChange = select_node;
                    $(selector + '-search').selectize()[0].selectize.swapOnChange();

                } else {
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
                            item: render_searchbox_node
                        },
                        options: svg_nodes
                    });
                }

                // without this, selecting an item with <enter> will submit the form
                // and force a page refresh. not the desired behavior.
                $(selector + '-search-form').submit(function () {
                    return false;
                });

            } // end if(interactive)
        }); // end json success callback
    }); // end svg success callback

} // end blastradius()