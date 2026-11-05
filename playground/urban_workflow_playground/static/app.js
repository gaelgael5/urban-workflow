/* Playground DSL urban-workflow : éditeur, intellisense, paramétrage, simulation. */
(function () {
  "use strict";

  // ------------------------------------------------------------------
  // Mode CodeMirror du DSL (coloration)
  // ------------------------------------------------------------------

  var KEYWORDS = [
    "NAME", "VERSION", "CONCURENCY", "DESCRIPTION", "MATCHING", "AS", "UNIQUE",
    "DEFINE", "EVENT", "RULE", "ACTION", "CONST",
    "INITIALIZE", "WORKFLOW", "ON", "WHEN", "RECURSIVE", "SWITCH",
    "STATE", "ENTER", "EXIT", "AND", "OR", "NOT",
    "EXECUTE", "STORE", "EXPIRE", "AFTER", "WAITING", "BEFORE",
    "MINUTE", "HOUR", "DAY", "TEXT", "INTEGER", "DECIMAL",
    "INCLUDE", "FRAGMENT",
  ];

  CodeMirror.defineSimpleMode("workflow-dsl", {
    start: [
      {regex: /--.*/, token: "comment"},
      {regex: /\/\*/, token: "comment", next: "comment"},
      // Chemin JSONPath vers l'événement entrant ($.Prop, $.Liste[0], $['p']) —
      // avant la règle des chaînes, qui avalerait le ['p'].
      {regex: /\$(?:\.[A-Za-z][\w$#]*|\[\d+\]|\['(?:[^'\n]|'')*'\])*/, token: "variable-3"},
      {regex: /'(?:[^'\n]|'')*'/, token: "string"},
      {regex: new RegExp("\\b(?:" + KEYWORDS.join("|") + ")\\b"), token: "keyword"},
      {regex: /@[A-Za-z][\w$#]*(?:\.[A-Za-z][\w$#]*)*/, token: "variable-2"},
      {regex: /\b\d+\b/, token: "number"},
      {regex: /[A-Za-z][\w$#]*/, token: "variable"},
      {regex: /[();=,.\[\]]/, token: "punctuation"},
    ],
    comment: [
      {regex: /.*?\*\//, token: "comment", next: "start"},
      {regex: /.*/, token: "comment"},
    ],
  });

  // ------------------------------------------------------------------
  // État global
  // ------------------------------------------------------------------

  var symbols = {events: [], rules: [], actions: [], constants: [], states: []};
  var lastErrors = [];
  var ruleSettings = loadRules();
  var schemaSettings = loadSchemas();
  // Abonnés à chaque analyse (vue « Événements » : la liste suit le script).
  var analyzeListeners = [];

  var CONTEXT_PATHS = [
    "@Workflow.ExternalId", "@Workflow.CurrentState", "@Workflow.Uuid",
    "@Workflow.WorkflowName", "@Workflow.Version",
    "@IncomingEvent.Name", "@IncomingEvent.ExternalId", "@IncomingEvent.EventDate",
    "@Event.Name", "@Event.FromState", "@Event.ToState",
  ];

  function loadRules() {
    try {
      return JSON.parse(localStorage.getItem("uw-playground-rules")) || [];
    } catch (e) { return []; }
  }
  function saveRules() {
    try { localStorage.setItem("uw-playground-rules", JSON.stringify(ruleSettings)); }
    catch (e) { /* stockage indisponible : on continue sans persistance */ }
  }
  function loadSchemas() {
    try {
      return JSON.parse(localStorage.getItem("uw-playground-schemas")) || [];
    } catch (e) { return []; }
  }
  function saveSchemas() {
    try { localStorage.setItem("uw-playground-schemas", JSON.stringify(schemaSettings)); }
    catch (e) { /* idem */ }
  }

  // ------------------------------------------------------------------
  // Éditeur + lint (analyse serveur)
  // ------------------------------------------------------------------

  var editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
    mode: "workflow-dsl",
    lineNumbers: true,
    indentUnit: 4,
    gutters: ["CodeMirror-lint-markers"],
    lint: {async: true, getAnnotations: lintScript, delay: 450},
    extraKeys: {"Ctrl-Space": "autocomplete"},
  });

  function lintScript(text, updateLinting) {
    fetch("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({script: text, rules: ruleSettings, schemas: schemaSettings}),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        symbols = data.symbols || symbols;
        lastErrors = data.errors || [];
        analyzeListeners.forEach(function (fn) { fn(data); });
        renderStatus(data);
        renderDiagnostics();
        renderStructure(data.summary);
        updateLinting(lastErrors.map(function (e) {
          var line = Math.max(0, (e.line || 1) - 1);
          var ch = Math.max(0, e.column || 0);
          return {
            from: CodeMirror.Pos(line, ch),
            to: CodeMirror.Pos(line, ch + 1),
            message: e.message,
            severity: e.severity || "error",
          };
        }));
      })
      .catch(function () {
        document.getElementById("status").textContent = "serveur injoignable";
        updateLinting([]);
      });
  }

  // ------------------------------------------------------------------
  // Intellisense contextuelle
  // ------------------------------------------------------------------

  function callCompletion(def) {
    var params = (def.params || []).map(function (p) { return p.name + " = "; });
    return {
      text: def.name + "(" + (params.length === 1 ? params[0] : "") + ")",
      displayText: def.name + "(" + (def.params || []).map(function (p) {
        return p.type + " " + p.name;
      }).join(", ") + ")",
    };
  }

  /** Événement du bloc ON EVENT qui contient le curseur (null hors bloc). */
  function enclosingEvent(textBefore) {
    var re = /\bON\s+EVENT\s+([A-Za-z][\w$#]*)|\bEXPIRE\s+AFTER\b|\bDEFINE\s+STATE\b|\bON\s+(?:ENTER|EXIT)\b/gi;
    var last = null, m;
    // Les commentaires ne comptent pas : un « ON EVENT » commenté ne
    // définit pas le contexte.
    var text = textBefore.replace(/--[^\n]*/g, "").replace(/\/\*[\s\S]*?\*\//g, "");
    while ((m = re.exec(text)) !== null) { last = m; }
    return last && last[1] ? last[1] : null;
  }

  function eventPathCompletions(cm) {
    var before = cm.getRange(CodeMirror.Pos(0, 0), cm.getCursor());
    var eventName = enclosingEvent(before);
    var byEvent = symbols.event_properties || {};
    var paths = (eventName && byEvent[eventName]) || null;
    if (!paths) {
      // Hors d'un bloc ON EVENT (ou événement inconnu) : seul le socle,
      // commun à tous les événements, est certain (fourni par le serveur,
      // source unique BASE_EVENT_SCHEMA).
      paths = symbols.base_paths || [];
    }
    return paths.map(function (p) {
      return {
        text: "$." + p.path,
        displayText: "$." + p.path + "  ·  " + p.type +
          (eventName ? "" : "  (socle)"),
      };
    });
  }

  function completionsFor(context) {
    if (context === "path") {
      return CONTEXT_PATHS.map(function (p) { return {text: p, displayText: p}; });
    }
    if (context === "schema") {
      return plain((symbols.schemas || []).map(function (s) { return "@" + s; }));
    }
    if (context === "unique") {
      return plain(symbols.payload_properties ||
                   ["ExternalId", "EventDate", "DedupKey"]);
    }
    if (context === "event") { return plain(symbols.events); }
    if (context === "state") { return plain(symbols.states); }
    if (context === "action") { return symbols.actions.map(callCompletion); }
    if (context === "rule") {
      return symbols.rules.map(callCompletion)
        .concat([{text: "NOT ", displayText: "NOT"}]);
    }
    if (context === "constant") {
      return plain(symbols.constants.map(function (c) { return c.name || c; }))
        .concat(CONTEXT_PATHS.map(function (p) { return {text: p, displayText: p}; }));
    }
    // défaut : mots-clés + tous les symboles
    return plain(KEYWORDS.map(function (k) { return k + " "; }))
      .concat(plain(symbols.events), plain(symbols.states));
  }

  function plain(list) {
    return (list || []).map(function (s) { return {text: s, displayText: s}; });
  }

  function detectContext(before) {
    if (/\$[\w.\[\]']*$/.test(before)) { return "eventpath"; }
    if (/\bAS\s+@?\w*$/i.test(before)) { return "schema"; }
    if (/\bUNIQUE\s*\([^)]*$/i.test(before)) { return "unique"; }
    if (/@[\w.]*$/.test(before)) { return "path"; }
    if (/=\s*\w*$/.test(before)) { return "constant"; }
    if (/\bON\s+EVENT\s+\w*$/i.test(before)) { return "event"; }
    if (/\bSWITCH\s+\w*$/i.test(before)) { return "state"; }
    if (/\bEXECUTE\s+\w*$/i.test(before)) { return "action"; }
    if (/\b(WHEN|AND|OR|NOT)\s+\w*$/i.test(before)) { return "rule"; }
    return "default";
  }

  function dslHint(cm) {
    var cursor = cm.getCursor();
    var token = cm.getTokenAt(cursor);
    if (token.type === "string" || token.type === "comment") { return null; }
    var lineText = cm.getLine(cursor.line).slice(0, cursor.ch);
    var context = detectContext(lineText);
    if (context === "eventpath") {
      var pathMatch = /\$[\w.\[\]']*$/.exec(lineText);
      var typedPath = pathMatch[0].toLowerCase();
      return {
        list: eventPathCompletions(cm).filter(function (item) {
          return item.text.toLowerCase().indexOf(typedPath) === 0;
        }),
        from: CodeMirror.Pos(cursor.line, cursor.ch - pathMatch[0].length),
        to: CodeMirror.Pos(cursor.line, cursor.ch),
      };
    }

    var match = /[@\w.]*$/.exec(lineText);
    var start = cursor.ch - (match ? match[0].length : 0);
    var typed = (match ? match[0] : "").toLowerCase();

    var list = completionsFor(context).filter(function (item) {
      return !typed || item.text.toLowerCase().indexOf(typed) === 0 ||
             item.displayText.toLowerCase().indexOf(typed) === 0;
    });

    return {
      list: list,
      from: CodeMirror.Pos(cursor.line, start),
      to: CodeMirror.Pos(cursor.line, cursor.ch),
    };
  }

  CodeMirror.registerHelper("hint", "workflow-dsl", dslHint);

  editor.on("inputRead", function (cm, change) {
    if (cm.state.completionActive) { return; }
    var token = cm.getTokenAt(cm.getCursor());
    if (token.type === "string" || token.type === "comment") { return; }
    // $ et . ouvrent aussi la complétion : « $. » doit proposer les
    // propriétés de l'événement sans attendre une lettre.
    if (/[\w@$.\[]/.test(change.text[0])) {
      cm.showHint({hint: dslHint, completeSingle: false});
    }
  });

  // ------------------------------------------------------------------
  // Rendu : statut, erreurs, structure
  // ------------------------------------------------------------------

  function renderStatus(data) {
    var el = document.getElementById("status");
    if (data.ok) {
      el.textContent = data.is_fragment ? "fragment valide" : "script valide";
      el.className = "status ok";
    } else {
      el.textContent = lastErrors.length + " erreur(s)";
      el.className = "status ko";
    }
  }

  function renderDiagnostics() {
    var el = document.getElementById("diagnostics");
    el.innerHTML = "";
    lastErrors.forEach(function (e) {
      var div = document.createElement("div");
      div.className = "diag";
      div.textContent = "ligne " + e.line + ":" + e.column + " — " + e.message;
      div.onclick = function () {
        editor.setCursor({line: Math.max(0, e.line - 1), ch: e.column || 0});
        editor.focus();
      };
      el.appendChild(div);
    });
  }

  function renderStructure(summary) {
    var el = document.getElementById("structure");
    if (!summary) {
      el.innerHTML = "<p class='hint-text'>Structure affichée quand le script est valide.</p>";
      return;
    }
    var html = "<h3>" + esc(summary.name) + " <small>v" + summary.version +
      " · concurrence " + summary.concurrency + "</small></h3>";
    if (Object.keys(summary.filters).length) {
      html += "<p class='hint-text'>MATCHING : " + esc(JSON.stringify(summary.filters)) + "</p>";
    }
    (summary.events || []).forEach(function (ev) {
      if (!ev.schema_ref && !(ev.unique || []).length) { return; }
      html += "<div class='node event-decl'>✉ " + esc(ev.name) +
        (ev.schema_ref ? " <small>AS @" + esc(ev.schema_ref) + "</small>" : "") +
        ((ev.unique || []).length
          ? " <small>UNIQUE(" + esc(ev.unique.join(", ")) + ")</small>" : "") +
        "</div>";
    });
    summary.initializers.forEach(function (init) {
      init.switchs.forEach(function (sw) {
        html += "<div class='node init'>⚡ " + esc(init.event) +
          (sw.when ? " <em>si " + esc(sw.when) + "</em>" : "") +
          " → <b>" + esc(sw.target) + "</b>" +
          (init.recursive ? " <small>(récursif)</small>" : "") + "</div>";
      });
    });
    summary.states.forEach(function (state) {
      html += "<div class='node state'><b>" + esc(state.name) + "</b>" +
        (state.label ? " <small>" + esc(state.label) + "</small>" : "") + "</div>";
      state.events.forEach(function (event) {
        event.transitions.forEach(function (t) {
          html += "<div class='node transition'>↳ " + esc(event.name) +
            (t.when ? " <em>si " + esc(t.when) + "</em>" : "") +
            (t.target ? " → " + esc(t.target) : " (actions seules)") + "</div>";
        });
        if (!event.transitions.length) {
          html += "<div class='node transition'>↳ " + esc(event.name) + "</div>";
        }
      });
    });
    el.innerHTML = html;
  }

  function esc(text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  // ------------------------------------------------------------------
  // Paramétrage des règles
  // ------------------------------------------------------------------

  function renderRules() {
    var el = document.getElementById("rules-list");
    el.innerHTML = "";
    if (!ruleSettings.length) {
      el.innerHTML = "<p class='hint-text'>Aucune règle paramétrée. " +
        "Les conditions WHEN exigeront leur enregistrement.</p>";
    }
    ruleSettings.forEach(function (rule, index) {
      var row = document.createElement("div");
      row.className = "rule-row";
      var signature = rule.name + "(" + rule.params.map(function (p) {
        return p.type + " " + p.name;
      }).join(", ") + ")";
      row.innerHTML = "<code>" + esc(signature) + "</code>" +
        "<label class='inline'><input type='checkbox' " +
        (rule.result ? "checked" : "") + "> vraie</label>" +
        "<button class='remove' title='Supprimer'>✕</button>";
      row.querySelector("input").onchange = function (e) {
        ruleSettings[index].result = e.target.checked;
        saveRules(); revalidate();
      };
      row.querySelector(".remove").onclick = function () {
        ruleSettings.splice(index, 1);
        saveRules(); renderRules(); revalidate();
      };
      el.appendChild(row);
    });
  }

  function renderSchemas() {
    var el = document.getElementById("schemas-list");
    el.innerHTML = "";
    if (!schemaSettings.length) {
      el.innerHTML = "<p class='hint-text'>Aucun schéma. Les références " +
        "AS @… resteront non résolues (erreur à l'analyse).</p>";
    }
    schemaSettings.forEach(function (schema, index) {
      var row = document.createElement("div");
      row.className = "rule-row";
      row.innerHTML = "<code title=\"" +
        esc(schema.yaml).replace(/"/g, "&quot;") + "\">@" + esc(schema.name) +
        "</code><button class='remove' title='Supprimer'>✕</button>";
      row.querySelector(".remove").onclick = function () {
        schemaSettings.splice(index, 1);
        saveSchemas(); renderSchemas(); revalidate();
      };
      el.appendChild(row);
    });
  }

  document.getElementById("schema-form").onsubmit = function (e) {
    e.preventDefault();
    var name = document.getElementById("schema-name").value.trim();
    var yaml = document.getElementById("schema-yaml").value;
    if (!name || !yaml.trim()) { return; }
    schemaSettings = schemaSettings.filter(function (s) { return s.name !== name; });
    schemaSettings.push({name: name, yaml: yaml});
    saveSchemas(); renderSchemas(); revalidate();
    e.target.reset();
  };

  document.getElementById("rule-form").onsubmit = function (e) {
    e.preventDefault();
    var name = document.getElementById("rule-name").value.trim();
    var paramsText = document.getElementById("rule-params").value.trim();
    var params = [];
    if (paramsText) {
      paramsText.split(",").forEach(function (part) {
        var m = /^\s*(TEXT|INTEGER|DECIMAL)?\s*([A-Za-z]\w*)\s*$/i.exec(part);
        if (m) { params.push({name: m[2], type: (m[1] || "TEXT").toUpperCase()}); }
      });
    }
    ruleSettings = ruleSettings.filter(function (r) { return r.name !== name; });
    ruleSettings.push({
      name: name, params: params,
      result: document.getElementById("rule-result").checked,
    });
    saveRules(); renderRules(); revalidate();
    e.target.reset();
    document.getElementById("rule-result").checked = true;
  };

  function revalidate() {
    editor.performLint();
  }

  // ------------------------------------------------------------------
  // Simulation
  // ------------------------------------------------------------------

  document.getElementById("run-simulation").onclick = function () {
    var out = document.getElementById("simulation-result");
    var events;
    try {
      events = JSON.parse(document.getElementById("events-input").value || "[]");
    } catch (e) {
      out.innerHTML = "<div class='diag'>JSON des événements invalide : " + esc(e.message) + "</div>";
      return;
    }
    out.innerHTML = "<p class='hint-text'>Simulation…</p>";
    fetch("/api/simulate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        script: editor.getValue(), rules: ruleSettings,
        schemas: schemaSettings, events: events,
      }),
    })
      .then(function (r) { return r.json(); })
      .then(renderSimulation)
      .catch(function (e) {
        out.innerHTML = "<div class='diag'>" + esc(String(e)) + "</div>";
      });
  };

  function renderSimulation(data) {
    var out = document.getElementById("simulation-result");
    if (!data.ok) {
      out.innerHTML = "<div class='diag'>" + esc(data.error) + "</div>";
      return;
    }
    var html = "";
    data.steps.forEach(function (step, index) {
      html += "<div class='sim-step'><h4>" + (index + 1) + ". " + esc(step.event) + "</h4>";
      if (step.error) {
        html += "<div class='diag'>" + esc(step.error) + "</div>";
      } else if (!step.impacted.length) {
        html += "<p class='hint-text'>Aucun workflow impacté (filtre MATCHING, " +
          "événement non déclaré ou pas d'initialiseur).</p>";
      }
      (step.impacted || []).forEach(function (ctx) {
        html += "<div class='sim-ctx'><b>" + esc(ctx.workflow) + "</b> [" +
          esc(ctx.external_id) + "] : " + esc(ctx.from_state || "∅") +
          " → <b>" + esc(ctx.to_state || "∅") + "</b>";
        ctx.actions.forEach(function (action) {
          html += "<div class='sim-action'>▸ " + esc(action.name) +
            " <small>" + esc(action.kind) + "</small>" +
            "<pre>" + esc(JSON.stringify(action.message, null, 1)) + "</pre></div>";
        });
        if (ctx.log.length) {
          html += "<div class='sim-log'>" + ctx.log.map(esc).join("<br>") + "</div>";
        }
        html += "</div>";
      });
      html += "</div>";
    });
    html += "<h4>État final du stockage</h4>";
    if (!data.workflows.length) { html += "<p class='hint-text'>Aucun workflow créé.</p>"; }
    data.workflows.forEach(function (w) {
      html += "<div class='sim-ctx'><b>" + esc(w.workflow) + "</b> [" +
        esc(w.external_id) + "] — état <b>" + esc(w.state) + "</b>" +
        "<div class='sim-log'>" + (w.events || []).map(function (e) {
          // Historique avec la date d'intégration posée par le moteur.
          return esc(e.name) + " : " + esc(e.from || "∅") + " → " + esc(e.to || "∅") +
            (e.integration_date ? " · intégré le " + esc(e.integration_date) : "");
        }).join("<br>") + "</div>" +
        "<pre>" + esc(JSON.stringify(w.extended_datas, null, 1)) + "</pre></div>";
    });
    out.innerHTML = html;
  }

  // ------------------------------------------------------------------
  // Onglets + exemples
  // ------------------------------------------------------------------

  // [data-tab] : le bouton de repli vit dans la même barre mais n'est pas un
  // onglet — sans ce filtre il désactiverait l'onglet courant.
  document.querySelectorAll(".tabs button[data-tab]").forEach(function (button) {
    button.onclick = function () {
      document.querySelectorAll(".tabs button[data-tab]").forEach(function (b) {
        b.classList.toggle("active", b === button);
      });
      document.querySelectorAll(".tab").forEach(function (tab) {
        tab.classList.toggle("active", tab.id === "tab-" + button.dataset.tab);
      });
    };
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
    // CodeMirror mesure sa largeur au rendu : sans refresh, l'éditeur garde
    // l'ancienne largeur jusqu'à la prochaine frappe. X6 suit seul (autoResize).
    editor.refresh();
  }
  sideToggle.onclick = function () {
    setSideCollapsed(!sidePane.classList.contains("collapsed"));
  };
  try {
    if (localStorage.getItem(SIDE_KEY) === "1") { setSideCollapsed(true); }
  } catch (err) { /* privé */ }

  document.getElementById("example-select").onchange = function (e) {
    var example = window.PLAYGROUND_EXAMPLES[e.target.value];
    if (!example) { return; }
    editor.setValue(example.script);
    if (example.rules.length) {
      ruleSettings = example.rules.slice();
      saveRules(); renderRules();
    }
    if (example.schemas && example.schemas.length) {
      example.schemas.forEach(function (schema) {
        schemaSettings = schemaSettings.filter(function (s) {
          return s.name !== schema.name;
        });
        schemaSettings.push(schema);
      });
      saveSchemas(); renderSchemas();
    }
    document.getElementById("events-input").value =
      JSON.stringify(example.events, null, 2);
    e.target.value = "";
  };

  // ------------------------------------------------------------------
  // Pont vers la vue diagramme (diagram.js)
  // ------------------------------------------------------------------

  window.PlaygroundBridge = {
    getScript: function () { return editor.getValue(); },
    setScript: function (value) { editor.setValue(value); },
    getRules: function () { return ruleSettings; },
    getSchemas: function () { return schemaSettings; },
    refreshEditor: function () { editor.refresh(); },
    getSymbols: function () { return symbols; },
    onAnalyze: function (fn) { analyzeListeners.push(fn); },
    // Création/remplacement d'un schéma du panneau, puis ré-analyse : même
    // effet que le formulaire « Ajouter le schéma », sans passer par lui.
    setSchema: function (name, yaml) {
      var found = schemaSettings.some(function (s) {
        if (s.name === name) { s.yaml = yaml; return true; }
        return false;
      });
      if (!found) { schemaSettings.push({name: name, yaml: yaml}); }
      saveSchemas(); renderSchemas(); revalidate();
    },
    // Insertion ponctuelle dans le script (index = position dans le texte) :
    // replaceRange garde le curseur et l'historique d'annulation, là où un
    // setValue complet les perdrait.
    insertText: function (index, text) {
      editor.replaceRange(text, editor.posFromIndex(index));
    },
  };

  // ------------------------------------------------------------------
  // Démarrage
  // ------------------------------------------------------------------

  renderRules();
  renderSchemas();
  var initial = window.PLAYGROUND_EXAMPLES.validation;
  if (!ruleSettings.length) {
    ruleSettings = initial.rules.slice();
    saveRules(); renderRules();
  }
  if (!schemaSettings.length && initial.schemas) {
    schemaSettings = initial.schemas.slice();
    saveSchemas(); renderSchemas();
  }
  editor.setValue(initial.script);
  document.getElementById("events-input").value =
    JSON.stringify(initial.events, null, 2);
})();
