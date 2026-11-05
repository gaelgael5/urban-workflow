/* Vue diagramme : dessiner le workflow (X6) et générer le DSL.
 *
 * Source de vérité de la vue : un « modèle de surface » (le JSON de
 * /api/diagram — états, transitions, déclarations, expressions en texte
 * brut). Toute édition passe par le modèle puis reconstruit le graphe ;
 * « Générer » envoie le modèle à /api/generate (rendu canonique + analyse
 * réelle) et pousse le script dans l'éditeur.
 */
(function () {
  "use strict";

  var bridge = window.PlaygroundBridge;

  var COLORS = {
    bg: "#11151c", panel: "#1a2029", border: "#2b3442", text: "#d8dee9",
    muted: "#7f8ea3", accent: "#5fb3f0", ok: "#4cc38a", sel: "#ecc48d",
    expire: "#b58ee6",
  };
  var IDENTIFIER = /^[A-Za-z][A-Za-z0-9_]*$/;
  var INIT_ID = "$init";

  var model = null;          // modèle de surface courant (null = pas importé)
  var positions = {};        // nom d'état -> {x, y}
  var linkMode = false;
  var selected = null;       // descripteur de sélection (voir select())
  var uidSeq = 0;

  // ------------------------------------------------------------------
  // Graphe X6
  // ------------------------------------------------------------------

  var graph = new X6.Graph({
    container: document.getElementById("diagram-canvas"),
    autoResize: true,
    // Rendu SYNCHRONE, obligatoire ici : rebuildGraph() fait clearCells()
    // puis ré-ajoute les MÊMES ids. En rendu asynchrone (défaut X6), la
    // suppression des vues est différée dans willRemoveViews[id] ; le
    // ré-ajout écrase l'entrée et l'ancienne vue n'est jamais retirée du
    // DOM — chaque reconstruction doublait les états à l'écran (fantômes
    // visibles en glissant un état). Coût négligeable à cette taille.
    async: false,
    background: { color: COLORS.bg },
    grid: { visible: true, size: 14, args: { color: "#1c2330", thickness: 1 } },
    interacting: {
      nodeMovable: function () { return !linkMode; },
      edgeMovable: false,
      edgeLabelMovable: false,
    },
    connecting: {
      allowBlank: false,
      allowLoop: true,
      allowMulti: true,
      allowNode: true,
      allowEdge: false,
      connector: { name: "rounded" },
      validateMagnet: function () { return linkMode; },
      validateConnection: function (args) {
        return !!args.targetCell && args.targetCell.isNode() &&
               args.targetCell.id !== INIT_ID;
      },
      createEdge: function () {
        return graph.createEdge({
          attrs: { line: { stroke: COLORS.accent, strokeWidth: 1.6,
                           targetMarker: { name: "block", size: 7 } } },
        });
      },
    },
  });

  // ------------------------------------------------------------------
  // Accès au modèle
  // ------------------------------------------------------------------

  function stateByUid(uid) {
    for (var i = 0; i < model.states.length; i++) {
      if (model.states[i]._uid === uid) { return model.states[i]; }
    }
    return null;
  }

  function assignUids() {
    model.states.forEach(function (state) {
      if (!state._uid) { state._uid = "s" + (++uidSeq); }
    });
  }

  function eventNames() {
    var names = {};
    model.events.forEach(function (e) { names[e.name] = 1; });
    model.initializers.forEach(function (i) { if (i.event) { names[i.event] = 1; } });
    model.states.forEach(function (s) {
      s.handlers.forEach(function (h) { if (h.event) { names[h.event] = 1; } });
    });
    return Object.keys(names).sort();
  }

  function ensureEventDeclarations() {
    var declared = {};
    model.events.forEach(function (e) { declared[e.name] = 1; });
    eventNames().forEach(function (name) {
      if (!declared[name]) {
        model.events.push({ name: name, label: name, schema_ref: "", unique: [] });
      }
    });
  }

  function findOrCreateHandler(state, eventName) {
    for (var i = 0; i < state.handlers.length; i++) {
      if (!state.handlers[i].expire_after && state.handlers[i].event === eventName) {
        return state.handlers[i];
      }
    }
    var handler = { event: eventName, expire_after: "", transitions: [] };
    state.handlers.push(handler);
    return handler;
  }

  function dropEmptyHandlers(state) {
    state.handlers = state.handlers.filter(function (h) {
      return h.transitions.length > 0;
    });
  }

  function renameState(state, newName) {
    var old = state.name;
    if (old === newName) { return; }
    state.name = newName;
    model.initializers.forEach(function (init) {
      if (init.switch === old) { init.switch = newName; }
    });
    model.states.forEach(function (s) {
      s.handlers.forEach(function (h) {
        h.transitions.forEach(function (t) {
          if (t.switch === old) { t.switch = newName; }
        });
      });
    });
    if (positions[old]) { positions[newName] = positions[old]; delete positions[old]; }
    savePositions();
  }

  function deleteState(state) {
    model.states = model.states.filter(function (s) { return s !== state; });
    model.initializers = model.initializers.filter(function (init) {
      return init.switch !== state.name;
    });
    model.states.forEach(function (s) {
      s.handlers.forEach(function (h) {
        h.transitions = h.transitions.filter(function (t) {
          return t.switch !== state.name;
        });
      });
      dropEmptyHandlers(s);
    });
    delete positions[state.name];
    savePositions();
  }

  // ------------------------------------------------------------------
  // Positions (persistées par nom de workflow)
  // ------------------------------------------------------------------

  function positionsKey() {
    return "uw-playground-diagram:" + (model && model.name ? model.name : "?");
  }
  function loadPositions() {
    try { return JSON.parse(localStorage.getItem(positionsKey())) || {}; }
    catch (e) { return {}; }
  }
  function savePositions() {
    try { localStorage.setItem(positionsKey(), JSON.stringify(positions)); }
    catch (e) { /* stockage indisponible : positions de session seulement */ }
  }

  function autoLayout() {
    var level = {};
    var queue = [];
    var adjacency = {};
    model.states.forEach(function (state) {
      adjacency[state.name] = [];
      state.handlers.forEach(function (handler) {
        handler.transitions.forEach(function (t) {
          if (t.switch) { adjacency[state.name].push(t.switch); }
        });
      });
    });
    model.initializers.forEach(function (init) {
      if (level[init.switch] === undefined) {
        level[init.switch] = 0;
        queue.push(init.switch);
      }
    });
    while (queue.length) {
      var name = queue.shift();
      (adjacency[name] || []).forEach(function (next) {
        if (level[next] === undefined) {
          level[next] = level[name] + 1;
          queue.push(next);
        }
      });
    }
    var deepest = 0;
    model.states.forEach(function (state) {
      if (level[state.name] !== undefined) {
        deepest = Math.max(deepest, level[state.name]);
      }
    });
    var rows = {};
    model.states.forEach(function (state) {
      var l = level[state.name] !== undefined ? level[state.name] : deepest + 1;
      rows[l] = rows[l] || 0;
      positions[state.name] = {
        x: 280 + l * 320,
        y: 60 + rows[l] * 160 + (l % 2) * 40,
      };
      rows[l]++;
    });
    savePositions();
  }

  // ------------------------------------------------------------------
  // Construction du graphe depuis le modèle
  // ------------------------------------------------------------------

  function shorten(text, max) {
    text = text.replace(/\s+/g, " ");
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  }

  function ordinal(index) {
    return index < 20 ? String.fromCharCode(0x2460 + index) : "#" + (index + 1);
  }

  function transitionLabel(handler, transition, index) {
    var head = handler.expire_after
      ? "⏰ EXPIRE AFTER " + handler.expire_after
      : handler.event;
    if (handler.transitions.length > 1) { head += "  " + ordinal(index); }
    var parts = [head];
    if (transition.when) { parts.push("[ " + shorten(transition.when, 46) + " ]"); }
    if (transition.executes.length) {
      parts.push("✉ " + transition.executes.length + " action(s)");
    }
    return parts.join("\n");
  }

  function initializerLabel(init) {
    var parts = [init.event + (init.recursive ? " · RECURSIVE" : "")];
    if (init.when) { parts.push("[ " + shorten(init.when, 46) + " ]"); }
    return parts.join("\n");
  }

  function addStateNode(state) {
    var pos = positions[state.name] || { x: 260, y: 220 };
    var text = state.name;
    if (state.label) { text += "\n" + shorten(state.label, 24); }
    if (state.actions.length) {
      text += "\n⚙ " + state.actions.length + " ON ENTER/EXIT";
    }
    graph.addNode({
      id: state._uid, x: pos.x, y: pos.y, width: 170, height: 62, shape: "rect",
      data: { kind: "state", su: state._uid },
      attrs: {
        body: { fill: COLORS.panel, stroke: COLORS.border, strokeWidth: 1.4,
                rx: 8, ry: 8, magnet: true },
        label: { text: text, fill: COLORS.text, fontSize: 12.5,
                 fontFamily: "Segoe UI, sans-serif", magnet: true,
                 textWrap: { width: -14, height: -8, ellipsis: true } },
      },
    });
  }

  function addEdgeFor(sourceId, targetId, text, data, color, dashed, labelPos) {
    var edge = {
      source: { cell: sourceId }, target: { cell: targetId },
      connector: { name: "rounded" },
      data: data,
      attrs: { line: { stroke: color, strokeWidth: 1.4,
                       targetMarker: { name: "block", size: 7 } } },
      labels: [{ position: labelPos || 0.5, attrs: {
        label: { text: text, fill: COLORS.text, fontSize: 11,
                 fontFamily: "Segoe UI, sans-serif" },
        body: { fill: COLORS.panel, stroke: color, rx: 4, ry: 4 },
      } }],
    };
    if (dashed) { edge.attrs.line.strokeDasharray = "5 3"; }
    if (sourceId === targetId) {
      var pos = positions[stateByUid(sourceId).name] || { x: 260, y: 220 };
      edge.vertices = [
        { x: pos.x + 205, y: pos.y - 22 },
        { x: pos.x + 205, y: pos.y + 80 },
      ];
    }
    graph.addEdge(edge);
  }

  function rebuildGraph() {
    graph.clearCells();

    var initY = 200;
    var firstTarget = model.initializers.length &&
      positions[model.initializers[0].switch];
    if (firstTarget) { initY = firstTarget.y + 10; }
    graph.addNode({
      id: INIT_ID, x: 40, y: initY, width: 42, height: 42, shape: "circle",
      data: { kind: "init" },
      attrs: {
        body: { fill: "#243242", stroke: COLORS.accent, strokeWidth: 1.6,
                magnet: true },
        label: { text: "⚡", fontSize: 16 },
      },
    });

    var byName = {};
    model.states.forEach(function (state) {
      byName[state.name] = state;
      addStateNode(state);
    });

    model.initializers.forEach(function (init, index) {
      var target = byName[init.switch];
      if (!target) { return; }
      addEdgeFor(INIT_ID, target._uid, initializerLabel(init),
                 { kind: "init", ii: index }, COLORS.accent, false, 0.62);
    });

    model.states.forEach(function (state) {
      state.handlers.forEach(function (handler, hi) {
        handler.transitions.forEach(function (transition, ti) {
          var color = handler.expire_after ? COLORS.expire : COLORS.muted;
          var data = { kind: "transition", su: state._uid, hi: hi, ti: ti };
          var target = byName[transition.switch];
          if (target) {
            addEdgeFor(state._uid, target._uid,
                       transitionLabel(handler, transition, ti),
                       data, color, false);
          } else {
            // Branche sans SWITCH (ou cible disparue) : boucle en pointillé.
            addEdgeFor(state._uid, state._uid,
                       transitionLabel(handler, transition, ti) +
                       "\n(sans SWITCH)",
                       data, color, true);
          }
        });
      });
    });

    restoreSelection();
  }

  // ------------------------------------------------------------------
  // Sélection + inspecteur
  // ------------------------------------------------------------------

  function sameSelection(a, b) {
    if (!a || !b || a.kind !== b.kind) { return false; }
    if (a.kind === "state") { return a.su === b.su; }
    if (a.kind === "init") { return a.ii === b.ii; }
    return a.su === b.su && a.hi === b.hi && a.ti === b.ti;
  }

  function highlight() {
    graph.getEdges().forEach(function (edge) {
      var isSel = sameSelection(edge.getData(), selected);
      edge.attr("line/strokeWidth", isSel ? 2.4 : 1.4);
      if (isSel) { edge.attr("line/stroke", COLORS.sel); }
    });
    graph.getNodes().forEach(function (node) {
      var data = node.getData() || {};
      var isSel = selected && selected.kind === "state" &&
        data.kind === "state" && data.su === selected.su;
      node.attr("body/stroke", isSel ? COLORS.sel : COLORS.border);
    });
  }

  function select(descriptor) {
    selected = descriptor;
    highlight();
    renderInspector();
  }

  function restoreSelection() {
    if (!selected) { renderInspector(); return; }
    if (selected.kind === "state" && !stateByUid(selected.su)) { selected = null; }
    if (selected && selected.kind === "transition") {
      var state = stateByUid(selected.su);
      var handler = state && state.handlers[selected.hi];
      if (!handler || !handler.transitions[selected.ti]) { selected = null; }
    }
    if (selected && selected.kind === "init" &&
        !model.initializers[selected.ii]) { selected = null; }
    highlight();
    renderInspector();
  }

  // En mode « Relier », on ne sélectionne pas : une sélection active
  // perturbe la recherche de cible de X6 pendant le tracé d'une arête.
  graph.on("node:click", function (args) {
    if (linkMode) { return; }
    var data = args.node.getData() || {};
    if (data.kind === "state") { select({ kind: "state", su: data.su }); }
    else { select(null); }
  });
  graph.on("edge:click", function (args) {
    if (linkMode) { return; }
    var data = args.edge.getData();
    if (data) { select(data); } else { select(null); }
  });
  graph.on("blank:click", function () { select(null); });

  graph.on("node:moved", function (args) {
    var data = args.node.getData() || {};
    if (data.kind !== "state") { return; }
    var state = stateByUid(data.su);
    if (!state) { return; }
    var position = args.node.getPosition();
    positions[state.name] = { x: position.x, y: position.y };
    savePositions();
    rebuildGraph(); // repositionne les boucles et sommets dépendants
  });

  graph.on("edge:connected", function (args) {
    if (!args.isNew) { return; }
    var sourceCell = args.edge.getSourceCell();
    var targetCell = args.edge.getTargetCell();
    graph.removeCell(args.edge);
    if (!sourceCell || !targetCell) { return; }
    var targetData = targetCell.getData() || {};
    var targetState = stateByUid(targetData.su);
    if (!targetState) { return; }

    if (sourceCell.id === INIT_ID) {
      model.initializers.push({
        event: eventNames()[0] || "Evenement",
        switch: targetState.name, when: "", recursive: false,
      });
      selected = { kind: "init", ii: model.initializers.length - 1 };
    } else {
      var sourceData = sourceCell.getData() || {};
      var sourceState = stateByUid(sourceData.su);
      if (!sourceState) { return; }
      var handler = findOrCreateHandler(
        sourceState, eventNames()[0] || "Evenement");
      handler.transitions.push({ when: "", executes: [], switch: targetState.name });
      selected = {
        kind: "transition", su: sourceState._uid,
        hi: sourceState.handlers.indexOf(handler),
        ti: handler.transitions.length - 1,
      };
    }
    exitLinkMode(); // retour au mode normal : la nouvelle branche s'édite
    rebuildGraph();
  });

  function exitLinkMode() {
    linkMode = false;
    var button = document.getElementById("dg-link-mode");
    button.classList.remove("on");
    button.textContent = "Relier";
  }

  // ------------------------------------------------------------------
  // Inspecteur (panneau de propriétés)
  // ------------------------------------------------------------------

  var inspector = document.getElementById("inspector");

  function h(tag, attrs, children) {
    var element = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      if (key === "text") { element.textContent = attrs[key]; }
      else if (key.indexOf("on") === 0) { element[key] = attrs[key]; }
      else if (key === "checked" || key === "value" || key === "hidden") {
        element[key] = attrs[key];
      } else { element.setAttribute(key, attrs[key]); }
    });
    (children || []).forEach(function (child) { element.appendChild(child); });
    return element;
  }

  function row(labelText, control) {
    return h("div", { class: "insp-row" }, [
      h("label", { text: labelText }), control,
    ]);
  }

  function eventInput(value, onchange) {
    var list = document.getElementById("dsl-event-names");
    if (!list) {
      list = h("datalist", { id: "dsl-event-names" });
      document.body.appendChild(list);
    }
    list.innerHTML = "";
    eventNames().forEach(function (name) {
      list.appendChild(h("option", { value: name }));
    });
    return h("input", {
      value: value, list: "dsl-event-names", spellcheck: "false",
      onchange: onchange,
    });
  }

  function stateSelect(value, onchange) {
    var select = h("select", { onchange: onchange });
    model.states.forEach(function (state) {
      var option = h("option", { value: state.name, text: state.name });
      if (state.name === value) { option.selected = true; }
      select.appendChild(option);
    });
    return select;
  }

  function executesEditor(list) {
    var container = h("div", {});
    list.forEach(function (text, index) {
      container.appendChild(h("div", { class: "exec-item" }, [
        h("textarea", {
          value: text, spellcheck: "false", rows: Math.min(4, text.split("\n").length + 1),
          onchange: function (e) {
            var value = e.target.value.trim();
            if (value) { list[index] = value; } else { list.splice(index, 1); }
            rebuildGraph();
          },
        }),
        h("button", {
          class: "remove", title: "Supprimer", text: "✕",
          onclick: function () { list.splice(index, 1); rebuildGraph(); },
        }),
      ]));
    });
    container.appendChild(h("button", {
      class: "insp-add", text: "＋ EXECUTE / STORE…",
      onclick: function () {
        list.push("EXECUTE MonAction(param = 'valeur')");
        rebuildGraph();
      },
    }));
    return container;
  }

  function renderInspector() {
    if (!selected || !model) { inspector.hidden = true; return; }
    inspector.hidden = false;
    inspector.innerHTML = "";

    if (selected.kind === "state") { renderStateInspector(); }
    else if (selected.kind === "init") { renderInitInspector(); }
    else { renderTransitionInspector(); }
  }

  function renderStateInspector() {
    var state = stateByUid(selected.su);
    if (!state) { inspector.hidden = true; return; }

    inspector.appendChild(h("h3", { text: "État" }));
    inspector.appendChild(row("Nom", h("input", {
      value: state.name, spellcheck: "false",
      onchange: function (e) {
        var name = e.target.value.trim();
        if (!IDENTIFIER.test(name)) { e.target.value = state.name; return; }
        renameState(state, name);
        rebuildGraph();
      },
    })));
    inspector.appendChild(row("Libellé", h("input", {
      value: state.label,
      onchange: function (e) { state.label = e.target.value; rebuildGraph(); },
    })));

    var actions = h("div", {});
    state.actions.forEach(function (action, index) {
      var trigger = h("select", {
        onchange: function (e) { action.trigger = e.target.value; rebuildGraph(); },
      });
      ["ENTER", "EXIT", "ENTER AND EXIT"].forEach(function (value) {
        var option = h("option", { value: value, text: "ON " + value + " STATE" });
        if (action.trigger === value) { option.selected = true; }
        trigger.appendChild(option);
      });
      actions.appendChild(h("div", { class: "insp-row" }, [trigger]));
      actions.appendChild(h("div", { class: "exec-item" }, [
        h("textarea", {
          value: action.execute, spellcheck: "false",
          rows: Math.min(4, action.execute.split("\n").length + 1),
          onchange: function (e) { action.execute = e.target.value; rebuildGraph(); },
        }),
        h("button", {
          class: "remove", title: "Supprimer", text: "✕",
          onclick: function () {
            state.actions.splice(index, 1); rebuildGraph();
          },
        }),
      ]));
    });
    actions.appendChild(h("button", {
      class: "insp-add", text: "＋ ON ENTER/EXIT STATE…",
      onclick: function () {
        state.actions.push({ trigger: "ENTER",
                             execute: "EXECUTE MonAction(param = 'valeur')" });
        rebuildGraph();
      },
    }));
    inspector.appendChild(row("Actions d'entrée / sortie", actions));

    inspector.appendChild(h("div", { class: "insp-actions" }, [
      h("button", {
        text: "＋ Expiration (EXPIRE AFTER)",
        onclick: function () {
          state.handlers.push({
            event: "", expire_after: "3 DAY",
            transitions: [{ when: "", executes: [], switch: state.name }],
          });
          selected = { kind: "transition", su: state._uid,
                       hi: state.handlers.length - 1, ti: 0 };
          rebuildGraph();
        },
      }),
      h("button", {
        class: "danger", text: "Supprimer l'état",
        onclick: function () {
          if (!window.confirm("Supprimer l'état " + state.name +
                              " et toutes les transitions liées ?")) { return; }
          deleteState(state);
          selected = null;
          rebuildGraph();
        },
      }),
    ]));
  }

  function renderInitInspector() {
    var init = model.initializers[selected.ii];
    if (!init) { inspector.hidden = true; return; }

    inspector.appendChild(h("h3", { text: "Initialisation du workflow" }));
    inspector.appendChild(row("Sur événement", eventInput(init.event,
      function (e) {
        var name = e.target.value.trim();
        if (!IDENTIFIER.test(name)) { e.target.value = init.event; return; }
        init.event = name;
        rebuildGraph();
      })));
    inspector.appendChild(row("Condition WHEN (optionnelle)", h("textarea", {
      value: init.when, spellcheck: "false", rows: 2,
      onchange: function (e) { init.when = e.target.value.trim(); rebuildGraph(); },
    })));
    var recursive = h("input", { type: "checkbox", checked: init.recursive,
      onchange: function (e) { init.recursive = e.target.checked; rebuildGraph(); },
    });
    inspector.appendChild(h("div", { class: "insp-row" }, [
      h("label", { class: "inline" }, [
        recursive, document.createTextNode(
          " RECURSIVE (un nouveau workflow par événement)"),
      ]),
    ]));
    inspector.appendChild(row("État initial (SWITCH)", stateSelect(init.switch,
      function (e) { init.switch = e.target.value; rebuildGraph(); })));
    inspector.appendChild(h("div", { class: "insp-actions" }, [
      h("button", {
        class: "danger", text: "Supprimer l'initialiseur",
        onclick: function () {
          model.initializers.splice(selected.ii, 1);
          selected = null;
          rebuildGraph();
        },
      }),
    ]));
  }

  function renderTransitionInspector() {
    var state = stateByUid(selected.su);
    var handler = state && state.handlers[selected.hi];
    var transition = handler && handler.transitions[selected.ti];
    if (!transition) { inspector.hidden = true; return; }

    var title = handler.expire_after
      ? "Expiration · " + state.name
      : "Transition · " + state.name +
        (transition.switch ? " → " + transition.switch : "");
    inspector.appendChild(h("h3", { text: title }));

    if (handler.expire_after) {
      inspector.appendChild(row("Délai (ex. 30 MINUTE, 2 HOUR, 3 DAY)", h("input", {
        value: handler.expire_after, spellcheck: "false",
        onchange: function (e) {
          handler.expire_after = e.target.value.trim();
          rebuildGraph();
        },
      })));
    } else {
      inspector.appendChild(row("Sur événement", eventInput(handler.event,
        function (e) {
          var name = e.target.value.trim();
          if (!IDENTIFIER.test(name)) { e.target.value = handler.event; return; }
          if (name === handler.event) { return; }
          handler.transitions.splice(selected.ti, 1);
          var target = findOrCreateHandler(state, name);
          target.transitions.push(transition);
          dropEmptyHandlers(state);
          selected = { kind: "transition", su: state._uid,
                       hi: state.handlers.indexOf(target),
                       ti: target.transitions.length - 1 };
          rebuildGraph();
        })));
    }

    inspector.appendChild(row("Condition WHEN (optionnelle)", h("textarea", {
      value: transition.when, spellcheck: "false", rows: 2,
      onchange: function (e) {
        transition.when = e.target.value.trim();
        rebuildGraph();
      },
    })));
    inspector.appendChild(row("Actions avant la bascule",
                              executesEditor(transition.executes)));
    inspector.appendChild(row("Bascule vers (SWITCH)", stateSelect(
      transition.switch || state.name,
      function (e) { transition.switch = e.target.value; rebuildGraph(); })));

    var actionsRow = h("div", { class: "insp-actions" }, []);
    if (handler.transitions.length > 1) {
      actionsRow.appendChild(h("button", {
        text: "↑ Priorité", title: "Monter cette branche",
        onclick: function () {
          if (selected.ti === 0) { return; }
          var list = handler.transitions;
          list.splice(selected.ti - 1, 0, list.splice(selected.ti, 1)[0]);
          selected.ti -= 1;
          rebuildGraph();
        },
      }));
      actionsRow.appendChild(h("button", {
        text: "↓", title: "Descendre cette branche",
        onclick: function () {
          var list = handler.transitions;
          if (selected.ti >= list.length - 1) { return; }
          list.splice(selected.ti + 1, 0, list.splice(selected.ti, 1)[0]);
          selected.ti += 1;
          rebuildGraph();
        },
      }));
    }
    actionsRow.appendChild(h("button", {
      class: "danger",
      text: handler.expire_after ? "Supprimer l'expiration" : "Supprimer la branche",
      onclick: function () {
        handler.transitions.splice(selected.ti, 1);
        dropEmptyHandlers(state);
        selected = null;
        rebuildGraph();
      },
    }));
    inspector.appendChild(actionsRow);

    if (handler.transitions.length > 1) {
      inspector.appendChild(h("p", {
        class: "hint-text",
        text: "Branches de " + (handler.expire_after ? "l'expiration" : handler.event) +
          " : la première garde vraie l'emporte ; une branche sans WHEN sert de défaut.",
      }));
    }
  }

  // ------------------------------------------------------------------
  // Statut + imports / génération
  // ------------------------------------------------------------------

  var statusEl = document.getElementById("diagram-status");

  function setStatus(text, ok) {
    statusEl.textContent = text || "";
    statusEl.className = "hint-text " + (ok === undefined ? "" : ok ? "ok" : "ko");
  }

  function importFromEditor() {
    setStatus("import du script…");
    fetch("/api/diagram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script: bridge.getScript() }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) {
          setStatus("script non importable : " +
                    (data.errors[0] ? data.errors[0].message : "?"), false);
          return;
        }
        model = data.model;
        assignUids();
        positions = loadPositions();
        var missing = model.states.some(function (s) { return !positions[s.name]; });
        if (missing) { autoLayout(); }
        selected = null;
        rebuildGraph();
        setStatus("diagramme importé · " + model.states.length + " état(s)", true);
      })
      .catch(function () { setStatus("serveur injoignable", false); });
  }

  function generateToEditor() {
    if (!model) { return; }
    if (!model.states.length) {
      setStatus("ajoute au moins un état avant de générer", false);
      return;
    }
    ensureEventDeclarations();
    setStatus("génération…");
    fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: model, rules: bridge.getRules(), schemas: bridge.getSchemas(),
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        bridge.setScript(data.script);
        if (data.ok) {
          setStatus("script généré ✓", true);
        } else {
          setStatus("script généré avec " + data.errors.length +
                    " erreur(s) — voir l'éditeur", false);
        }
        showView("editor");
      })
      .catch(function () { setStatus("serveur injoignable", false); });
  }

  // ------------------------------------------------------------------
  // Barre d'outils + bascule de vue
  // ------------------------------------------------------------------

  var VIEWS = ["editor", "diagram", "events"];

  function showView(which) {
    VIEWS.forEach(function (name) {
      document.getElementById("view-" + name).classList.toggle("active", name === which);
      document.getElementById(name + "-view").classList.toggle("active", name === which);
    });
    document.getElementById("diagram-tools").hidden = which !== "diagram";
    if (which === "editor") {
      bridge.refreshEditor();
    } else if (which === "diagram" && !model) {
      importFromEditor();
    }
    // Les autres vues (events.js) se branchent sur cet événement plutôt que
    // d'être connues d'ici.
    document.dispatchEvent(new CustomEvent("uw:view", {detail: which}));
  }

  VIEWS.forEach(function (name) {
    document.getElementById("view-" + name).onclick = function () { showView(name); };
  });
  document.getElementById("dg-import").onclick = importFromEditor;
  document.getElementById("dg-generate").onclick = generateToEditor;
  document.getElementById("dg-layout").onclick = function () {
    if (!model) { return; }
    autoLayout();
    rebuildGraph();
  };
  document.getElementById("dg-link-mode").onclick = function () {
    linkMode = !linkMode;
    this.classList.toggle("on", linkMode);
    this.textContent = linkMode ? "Relier ✓" : "Relier";
    if (linkMode) { select(null); }
  };
  // Poignée de debug / tests UI (non documentée, API non garantie).
  window.PlaygroundDiagram = {
    graph: graph,
    getModel: function () { return model; },
    select: select,
  };

  document.getElementById("dg-add-state").onclick = function () {
    if (!model) { return; }
    var base = "Etat";
    var index = model.states.length + 1;
    while (model.states.some(function (s) { return s.name === base + index; })) {
      index++;
    }
    var state = { name: base + index, label: "", actions: [], handlers: [],
                  _uid: "s" + (++uidSeq) };
    model.states.push(state);
    positions[state.name] = {
      x: 240 + (model.states.length % 4) * 70,
      y: 160 + (model.states.length % 5) * 60,
    };
    savePositions();
    selected = { kind: "state", su: state._uid };
    rebuildGraph();
  };
})();
