// svg extraction and download as data url borrowed from
// http://bl.ocks.org/curran/7cf9967028259ea032e8

function svgDataURL() {
    var svg_el   = document.querySelector('#graph svg');
    var svgAsXML = (new XMLSerializer).serializeToString(svg_el);
    return "data:image/svg+xml," + encodeURIComponent(svgAsXML);
}

function download(){
    var dataURL = svgDataURL();
    var dl = document.createElement("a");
    document.body.appendChild(dl); // This line makes it work in Firefox.
    dl.setAttribute("href", dataURL);
    dl.setAttribute("download", "blast-radius.svg");
    dl.click();
}