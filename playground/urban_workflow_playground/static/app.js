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
      {regex: /'(?:[^'\n]|'')*'/, token: "string"},
      {regex: new RegExp("\\b(?:" + KEYWORDS.join("|") + ")\\b"), token: "keyword"},
      {regex: /@[A-Za-z][\w$#]*(?:\.[A-Za-z][\w$#]*)*/, token: "variable-2"},
      {regex: /\b\d+\b/, token: "number"},
      {regex: /[A-Za-z][\w$#]*/, token: "variable"},
      {regex: /[();=,.]/, token: "punctuation"},
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
      body: JSON.stringify({script: text, rules: ruleSettings}),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        symbols = data.symbols || symbols;
        lastErrors = data.errors || [];
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

  function completionsFor(context) {
    if (context === "path") {
      return CONTEXT_PATHS.map(function (p) { return {text: p, displayText: p}; });
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
    if (/[\w@]/.test(change.text[0])) {
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
        script: editor.getValue(), rules: ruleSettings, events: events,
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
        "<pre>" + esc(JSON.stringify(w.extended_datas, null, 1)) + "</pre></div>";
    });
    out.innerHTML = html;
  }

  // ------------------------------------------------------------------
  // Onglets + exemples
  // ------------------------------------------------------------------

  document.querySelectorAll(".tabs button").forEach(function (button) {
    button.onclick = function () {
      document.querySelectorAll(".tabs button").forEach(function (b) {
        b.classList.toggle("active", b === button);
      });
      document.querySelectorAll(".tab").forEach(function (tab) {
        tab.classList.toggle("active", tab.id === "tab-" + button.dataset.tab);
      });
    };
  });

  document.getElementById("example-select").onchange = function (e) {
    var example = window.PLAYGROUND_EXAMPLES[e.target.value];
    if (!example) { return; }
    editor.setValue(example.script);
    if (example.rules.length) {
      ruleSettings = example.rules.slice();
      saveRules(); renderRules();
    }
    document.getElementById("events-input").value =
      JSON.stringify(example.events, null, 2);
    e.target.value = "";
  };

  // ------------------------------------------------------------------
  // Démarrage
  // ------------------------------------------------------------------

  renderRules();
  var initial = window.PLAYGROUND_EXAMPLES.validation;
  if (!ruleSettings.length) {
    ruleSettings = initial.rules.slice();
    saveRules(); renderRules();
  }
  editor.setValue(initial.script);
  document.getElementById("events-input").value =
    JSON.stringify(initial.events, null, 2);
})();
