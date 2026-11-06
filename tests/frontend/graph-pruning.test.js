const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(
    "blastradius/server/static/js/blast-radius.js",
    "utf8"
);

function createBrowserContext() {
    const requests = [];
    const renders = [];
    const context = {
        console,
        document: {
            querySelector(query) {
                if (query.endsWith(" svg")) {
                    return {remove() {}};
                }
                return null;
            }
        },
        DOMParser: class {
            parseFromString() {
                return {
                    documentElement: {},
                    querySelector() {
                        return null;
                    }
                };
            }
        },
        fetch: async (_url, options) => {
            requests.push(JSON.parse(options.body));
            return {
                ok: true,
                async json() {
                    return {
                        svg: "<svg></svg>",
                        graph: {nodes: [], edges: []},
                        warnings: []
                    };
                }
            };
        },
        Map,
        Set
    };

    vm.createContext(context);
    vm.runInContext(source, context);
    context.blastradius = async (...arguments_) => {
        renders.push(arguments_);
    };
    return {context, renders, requests};
}

function render(context, dot, selector, options = {}) {
    return vm.runInContext(
        `renderDotSource(
            ${JSON.stringify(dot)},
            ${JSON.stringify(selector)},
            ${JSON.stringify(options)}
        )`,
        context
    );
}

test("each tab prunes its own original DOT and retains render options", async () => {
    const {context, renders, requests} = createBrowserContext();
    const uploadedDot = 'digraph { "upload.a" -> "upload.b" }';
    const pastedDot = 'digraph { "paste.a" -> "paste.b" }';

    await render(context, uploadedDot, "#graph-2", {module_depth: 1});
    await render(context, pastedDot, "#graph-3");
    await vm.runInContext(
        `renderDotSource(
            graphSources.get("#graph-2").dot,
            "#graph-2",
            Object.assign({}, graphSources.get("#graph-2").options, {
                refocus: "upload.a"
            })
        )`,
        context
    );

    assert.equal(requests.length, 3);
    assert.deepEqual(requests[2], {
        dot: uploadedDot,
        module_depth: 1,
        refocus: "upload.a"
    });
    assert.equal(
        vm.runInContext('graphSources.get("#graph-3").dot', context),
        pastedDot
    );
    assert.equal(renders.length, 3);
    assert.equal(renders[2][0], "#graph-2");
    assert.equal(renders[2][1], null);
    assert.equal(renders[2][2], null);
});
