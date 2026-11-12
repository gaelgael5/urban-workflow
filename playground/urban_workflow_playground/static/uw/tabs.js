/* Composant « tabs » : un conteneur à onglets, au choix de l'application.
 *
 *   UrbanWorkflow.mount("tabs", el, {
 *     workspace,
 *     tabs: [
 *       {label: "Éditeur", component: "editor"},
 *       {label: "Diagramme", component: "diagram", options: {layoutStore}},
 *       {label: "Paramétrage", components: ["rules", "schemas"]},
 *     ],
 *     active: 0,
 *   })
 *
 * Rien n'impose de passer par lui : chaque composant se monte aussi seul
 * dans n'importe quel élément. Les onglets ne font que trois choses :
 * montrer un panneau à la fois, prévenir le composant qui redevient visible
 * (activate : CodeMirror et X6 remesurent), et répondre aux demandes
 * d'affichage de l'espace de travail (ws.reveal("scripts", …) active
 * l'onglet qui porte le composant Scripts).
 */
(function () {
  "use strict";

  var UW = window.UrbanWorkflow;

  UW.define("tabs", function (el, options) {
    var ws = options.workspace;
    var specs = options.tabs || [];
    el.innerHTML = "<nav class='tabs' data-ref='nav'></nav><div class='uw-tab-panels' data-ref='panels'></div>";
    var nav = UW.util.ref(el, "nav");
    var panels = UW.util.ref(el, "panels");
    var tabs = [];
    var current = -1;

    specs.forEach(function (spec, index) {
      var names = spec.components || (spec.component ? [spec.component] : []);
      var button = UW.util.h("button", {type: "button", text: spec.label || names.join(" + "),
                                        title: spec.title || ""});
      button.onclick = function () { show(index); };
      nav.appendChild(button);
      var panel = UW.util.h("div", {class: "uw-tab-panel"});
      panels.appendChild(panel);
      var children = names.map(function (entry) {
        var name = typeof entry === "string" ? entry : entry.component;
        var childOptions = Object.assign({}, spec.options || {},
                                         typeof entry === "string" ? {} : entry.options || {},
                                         {workspace: ws});
        var host = UW.util.h("div", {class: "uw-tab-part"});
        panel.appendChild(host);
        return UW.mount(name, host, childOptions);
      });
      if (children.length === 1) { panel.classList.add("single"); }
      tabs.push({spec: spec, button: button, panel: panel, children: children,
                 names: children.map(function (c) { return c.name; })});
    });

    function show(index) {
      if (index < 0 || index >= tabs.length) { return; }
      current = index;
      tabs.forEach(function (tab, i) {
        tab.button.classList.toggle("active", i === index);
        tab.panel.classList.toggle("active", i === index);
      });
      tabs[index].children.forEach(function (child) { child.activate(); });
      if (options.onChange) { options.onChange(index, tabs[index].spec); }
    }

    var off = ws.on("reveal", function (r) {
      for (var i = 0; i < tabs.length; i++) {
        if (tabs[i].names.indexOf(r.component) >= 0) {
          if (i !== current) { show(i); }
          return;
        }
      }
    });

    var start = typeof options.active === "number" ? options.active : 0;
    if (typeof options.active === "string") {
      tabs.forEach(function (tab, i) { if (tab.names.indexOf(options.active) >= 0) { start = i; } });
    }
    show(start);

    return {
      show: show,
      current: function () { return current; },
      /** Instance du composant monté dans les onglets (premier de ce nom). */
      component: function (name) {
        for (var i = 0; i < tabs.length; i++) {
          for (var j = 0; j < tabs[i].children.length; j++) {
            if (tabs[i].children[j].name === name) { return tabs[i].children[j]; }
          }
        }
        return null;
      },
      activate: function () { if (current >= 0) { show(current); } },
      destroy: function () {
        off();
        tabs.forEach(function (tab) { tab.children.forEach(function (c) { c.destroy(); }); });
      },
    };
  }, {label: "Onglets", description: "Conteneur à onglets de composants"});
})();
