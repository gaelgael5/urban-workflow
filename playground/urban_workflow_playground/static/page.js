/* Page de référence du playground : une composition des composants
 * urban-workflow parmi d'autres possibles. Tout ce qu'elle fait, une
 * application cliente peut le faire avec les mêmes appels publics. */
(function () {
  "use strict";

  var UW = window.UrbanWorkflow;
  var ws = UW.createWorkspace();

  UW.mount("examples", "#examples", {workspace: ws});
  UW.mount("status", "#status", {workspace: ws});

  var main = UW.mount("tabs", "#main-tabs", {
    workspace: ws,
    tabs: [
      {label: "Éditeur", component: "editor"},
      {label: "Diagramme", component: "diagram"},
      {label: "Événements", component: "events",
       title: "Lister les événements et éditer leur structure"},
      {label: "États", component: "states",
       title: "Lister les états et éditer leur structure"},
      {label: "Scripts", component: "scripts",
       title: "Scripts des règles (AS @script) et des artefacts (USING @script)"},
    ],
  });

  var side = UW.mount("tabs", "#side-tabs", {
    workspace: ws,
    tabs: [
      {label: "Paramétrage", components: ["rules", "schemas"]},
      {label: "Structure", component: "structure"},
      {label: "Simulation", component: "simulation"},
      {label: "Aide", component: "help"},
    ],
  });

  // Repli du panneau de droite, mémorisé par navigateur (préférence
  // d'affichage, pas une donnée : un localStorage indisponible = déplié).
  var SIDE_KEY = "uw-playground-side-collapsed";
  var sidePane = document.querySelector(".side-pane");
  var sideToggle = document.getElementById("side-collapse");
  function setSideCollapsed(collapsed) {
    sidePane.classList.toggle("collapsed", collapsed);
    var label = collapsed ? "Déplier le panneau" : "Replier le panneau";
    sideToggle.textContent = collapsed ? "«" : "»";
    sideToggle.title = label;
    sideToggle.setAttribute("aria-label", label);
    sideToggle.setAttribute("aria-expanded", String(!collapsed));
    try { localStorage.setItem(SIDE_KEY, collapsed ? "1" : "0"); } catch (err) { /* privé */ }
    // La largeur de la zone principale change : l'onglet visible remesure.
    main.activate();
  }
  sideToggle.onclick = function () {
    setSideCollapsed(!sidePane.classList.contains("collapsed"));
  };
  try {
    if (localStorage.getItem(SIDE_KEY) === "1") { setSideCollapsed(true); }
  } catch (err) { /* privé */ }

  // Premier chargement : l'exemple « validation », sans écraser les règles,
  // schémas et scripts que l'utilisateur a déjà dans son navigateur.
  var initial = UW.examples.validation;
  if (!ws.getRules().length) { ws.setRules(initial.rules); }
  if (!ws.getSchemas().length && initial.schemas) { ws.setSchemas(initial.schemas); }
  (initial.scripts || []).forEach(function (script) {
    if (!ws.findScript(script.name)) {
      ws.setScriptSource(script.name, script.source, script.language || "expression");
    }
  });
  ws.setEvents(initial.events);
  ws.setScript(initial.script, "page");

  // Poignée de tests UI (non documentée, API non garantie).
  window.Playground = {workspace: ws, main: main, side: side};
})();
