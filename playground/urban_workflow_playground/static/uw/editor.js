/* Composants « editor » (texte du workflow, intellisense, erreurs) et
 * « status » (badge de l'analyse).
 *
 *   UrbanWorkflow.mount("editor", el, {workspace, diagnostics: true})
 *
 * L'éditeur n'est pas propriétaire du script : il le lit et l'écrit dans
 * l'espace de travail, et se recharge quand un autre composant le modifie
 * (diagramme qui génère, vue Événements qui insère « AS @schema »…).
 */
(function () {
  "use strict";

  var UW = window.UrbanWorkflow;
  var esc = UW.util.esc;

  // Racines proposées après « @ ». @IncomingEvent. et @state. ouvrent
  // ensuite la complétion contextuelle de leurs propriétés. L'ancien
  // @Event.FromState/ToState n'est plus proposé : les états de départ et
  // d'arrivée ne sont pas des propriétés de l'événement (un événement peut
  // être traité par plusieurs workflows) — c'est l'état qui référence
  // l'événement (@state.EventId). Il reste résolu pour les scripts existants.
  var CONTEXT_PATHS = [
    "@IncomingEvent.", "@state.", "@artifact.",
    "@Workflow.ExternalId", "@Workflow.CurrentState", "@Workflow.Uuid",
    "@Workflow.WorkflowName", "@Workflow.Version",
  ];

  function stripComments(text) {
    return text.replace(/--[^\n]*/g, "").replace(/\/\*[\s\S]*?\*\//g, "");
  }

  /** Événement du bloc ON EVENT qui contient le curseur (null hors bloc). */
  function enclosingEvent(textBefore) {
    var re = /\bON\s+EVENT\s+([A-Za-z][\w$#]*)|\bEXPIRE\s+AFTER\b|\bDEFINE\s+STATE\b|\bON\s+(?:ENTER|EXIT)\b/gi;
    var last = null, m;
    // Les commentaires ne comptent pas : un « ON EVENT » commenté ne
    // définit pas le contexte.
    var text = stripComments(textBefore);
    while ((m = re.exec(text)) !== null) { last = m; }
    return last && last[1] ? last[1] : null;
  }

  /** État du bloc DEFINE STATE qui contient le curseur (null ailleurs,
   * notamment dans INITIALIZE WORKFLOW où aucun état n'existe encore). */
  function enclosingState(textBefore) {
    var re = /\bDEFINE\s+STATE\s+([A-Za-z][\w$#]*)|\bINITIALIZE\s+WORKFLOW\b|\bDEFINE\s+(?:EVENT|RULE|ACTION|CONST)\b/gi;
    var last = null, m;
    var text = stripComments(textBefore);
    while ((m = re.exec(text)) !== null) { last = m; }
    return last && last[1] ? last[1] : null;
  }

  function plain(list) {
    return (list || []).map(function (s) { return {text: s, displayText: s}; });
  }

  function callCompletion(def) {
    var params = (def.params || []).map(function (p) { return p.name + " = "; });
    return {
      text: def.name + "(" + (params.length === 1 ? params[0] : "") + ")",
      displayText: def.name + "(" + (def.params || []).map(function (p) {
        return p.type + " " + p.name;
      }).join(", ") + ")",
    };
  }

  function detectContext(before) {
    if (/@IncomingEvent\.[\w.\[\]']*$/i.test(before)) { return "eventpath"; }
    if (/@state\.[\w.\[\]']*$/i.test(before)) { return "statepath"; }
    if (/@artifact\.[\w.]*$/i.test(before)) { return "artifactpath"; }
    // USING @ d'un artefact → scripts (son AS @ reste un schéma, plus bas).
    if (/\bDEFINE\s+ARTIFACT\b[^;]*\bUSING\s+@?[\w.]*$/i.test(before)) { return "script"; }
    // AS @ d'une règle ou d'une action → scripts ; d'un événement, d'un
    // état ou d'un artefact → schémas.
    if (/\bDEFINE\s+(?:RULE|ACTION)\b[^;]*\bAS\s+@?[\w.]*$/i.test(before)) { return "script"; }
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

  /** Complétion du DSL, liée à un espace de travail (symboles de SA
   * dernière analyse : deux éditeurs sur deux espaces ne se mélangent pas). */
  function makeHint(ws) {
    function symbols() { return ws.getSymbols(); }

    // Chemins @IncomingEvent. / @state. : propriétés de l'objet du bloc
    // courant (métier d'abord, puis socle — ordre fourni par le serveur).
    var PATH_KINDS = {
      eventpath: {
        prefix: "@IncomingEvent.",
        owner: enclosingEvent,
        byName: function () { return symbols().event_properties || {}; },
        // Hors d'un bloc ON EVENT : seul le socle, commun à tous les
        // événements, est certain (source unique BASE_EVENT_SCHEMA).
        fallback: function () { return symbols().base_paths || []; },
      },
      statepath: {
        prefix: "@state.",
        owner: enclosingState,
        byName: function () { return symbols().state_properties || {}; },
        // Hors d'un bloc DEFINE STATE, @state n'existe pas (refusé à
        // l'analyse) : rien à proposer.
        fallback: function () { return []; },
      },
    };

    function pathCompletions(cm, context) {
      var spec = PATH_KINDS[context];
      var before = cm.getRange(CodeMirror.Pos(0, 0), cm.getCursor());
      var owner = spec.owner(before);
      var paths = (owner && spec.byName()[owner]) || spec.fallback(before);
      return paths.map(function (p) {
        return {
          text: spec.prefix + p.path,
          displayText: spec.prefix + p.path + "  ·  " + p.type + (owner ? "" : "  (socle)"),
        };
      });
    }

    /** « @artifact.Nom » puis, après le nom, les parties connues par le
     * schéma de l'artefact. N'a de sens que dans les arguments d'EXECUTE
     * (l'analyse le refuse ailleurs). */
    function artifactCompletions() {
      var items = [];
      (symbols().artifacts || []).forEach(function (a) {
        items.push({text: "@artifact." + a.name,
                    displayText: "@artifact." + a.name + "  ·  artefact" +
                      (a.label ? " — " + a.label : "")});
        ((symbols().artifact_properties || {})[a.name] || []).forEach(function (p) {
          items.push({text: "@artifact." + a.name + "." + p.path,
                      displayText: "@artifact." + a.name + "." + p.path + "  ·  " + p.type});
        });
      });
      return items;
    }

    /** Scripts connus : écrits (vue Scripts) puis seulement référencés. */
    function scriptNames() {
      var names = ws.getScripts().map(function (s) { return s.name; });
      // Fonctions Python fournies par le serveur : référençables comme les autres.
      (symbols().python_scripts || []).forEach(function (p) {
        if (names.indexOf(p.name) < 0) { names.push(p.name); }
      });
      (symbols().rules || []).concat(symbols().actions || [], symbols().artifacts || [])
        .forEach(function (d) {
          if (d.script && names.indexOf(d.script) < 0) { names.push(d.script); }
        });
      return names;
    }

    function completionsFor(context) {
      var s = symbols();
      if (context === "path") {
        return CONTEXT_PATHS.map(function (p) { return {text: p, displayText: p}; });
      }
      if (context === "script") {
        return plain(scriptNames().map(function (n) { return "@" + n; }));
      }
      if (context === "schema") {
        return plain((s.schemas || []).map(function (n) { return "@" + n; }));
      }
      if (context === "unique") {
        return plain(s.payload_properties || ["ExternalId", "EventDate", "DedupKey"]);
      }
      if (context === "event") { return plain(s.events); }
      if (context === "state") { return plain(s.states); }
      if (context === "action") { return (s.actions || []).map(callCompletion); }
      if (context === "rule") {
        return (s.rules || []).map(callCompletion)
          .concat([{text: "NOT ", displayText: "NOT"}]);
      }
      if (context === "constant") {
        return plain((s.constants || []).map(function (c) { return c.name || c; }))
          .concat(CONTEXT_PATHS.map(function (p) { return {text: p, displayText: p}; }));
      }
      // défaut : mots-clés + tous les symboles
      return plain(UW.KEYWORDS.map(function (k) { return k + " "; }))
        .concat(plain(s.events), plain(s.states));
    }

    return function dslHint(cm) {
      var cursor = cm.getCursor();
      var token = cm.getTokenAt(cursor);
      if (token.type === "string" || token.type === "comment") { return null; }
      var lineText = cm.getLine(cursor.line).slice(0, cursor.ch);
      var context = detectContext(lineText);
      if (PATH_KINDS[context]) {
        var pathMatch = /@(?:IncomingEvent|state)\.[\w.\[\]']*$/i.exec(lineText);
        var typedPath = pathMatch[0].toLowerCase();
        return {
          list: pathCompletions(cm, context).filter(function (item) {
            return item.text.toLowerCase().indexOf(typedPath) === 0;
          }),
          from: CodeMirror.Pos(cursor.line, cursor.ch - pathMatch[0].length),
          to: CodeMirror.Pos(cursor.line, cursor.ch),
        };
      }
      if (context === "artifactpath") {
        var artifactMatch = /@artifact\.[\w.]*$/i.exec(lineText);
        var typedArtifact = artifactMatch[0].toLowerCase();
        return {
          list: artifactCompletions().filter(function (item) {
            return item.text.toLowerCase().indexOf(typedArtifact) === 0;
          }),
          from: CodeMirror.Pos(cursor.line, cursor.ch - artifactMatch[0].length),
          to: CodeMirror.Pos(cursor.line, cursor.ch),
        };
      }
      var match = /[@\w.]*$/.exec(lineText);
      var start = cursor.ch - (match ? match[0].length : 0);
      var typed = (match ? match[0] : "").toLowerCase();
      return {
        list: completionsFor(context).filter(function (item) {
          return !typed || item.text.toLowerCase().indexOf(typed) === 0 ||
                 item.displayText.toLowerCase().indexOf(typed) === 0;
        }),
        from: CodeMirror.Pos(cursor.line, start),
        to: CodeMirror.Pos(cursor.line, cursor.ch),
      };
    };
  }

  // ------------------------------------------------------------------
  // Composant « editor »
  // ------------------------------------------------------------------

  UW.define("editor", function (el, options) {
    var ws = options.workspace;
    var showDiagnostics = options.diagnostics !== false;
    el.innerHTML = "<div class='uw-editor-host' data-ref='host'></div>" +
      (showDiagnostics ? "<div class='diagnostics' data-ref='diagnostics'></div>" : "");
    var diagnosticsEl = UW.util.ref(el, "diagnostics");
    var hint = makeHint(ws);
    var self = {};
    var loading = false;   // setValue venu de l'espace : ne pas le renvoyer

    var cm = CodeMirror(UW.util.ref(el, "host"), {
      value: ws.getScript(),
      mode: "workflow-dsl",
      lineNumbers: true,
      indentUnit: 4,
      gutters: ["CodeMirror-lint-markers"],
      // Lint branché sur l'analyse de l'espace (qui suit TOUTES les
      // modifications, y compris celles des autres composants), pas sur
      // une requête propre à l'éditeur.
      lint: {getAnnotations: annotations, lintOnChange: false},
      extraKeys: {"Ctrl-Space": function (instance) {
        instance.showHint({hint: hint, completeSingle: false});
      }},
      readOnly: !!options.readOnly,
    });

    function annotations() {
      // Les erreurs positionnées DANS un script (e.script) sont soulignées
      // par le composant Scripts, pas dans le workflow.
      return ws.getErrors().filter(function (e) { return !e.script; }).map(function (e) {
        var line = Math.max(0, (e.line || 1) - 1);
        var ch = Math.max(0, e.column || 0);
        return {
          from: CodeMirror.Pos(line, ch), to: CodeMirror.Pos(line, ch + 1),
          message: e.message, severity: e.severity || "error",
        };
      });
    }

    cm.on("change", function () {
      if (loading) { return; }
      ws.setScript(cm.getValue(), self);
    });

    cm.on("inputRead", function (instance, change) {
      if (instance.state.completionActive) { return; }
      var token = instance.getTokenAt(instance.getCursor());
      if (token.type === "string" || token.type === "comment") { return; }
      // « . » et « [ » ouvrent aussi la complétion : « @IncomingEvent. » doit
      // proposer les propriétés de l'événement sans attendre une lettre.
      if (/[\w@.\[]/.test(change.text[0])) {
        instance.showHint({hint: hint, completeSingle: false});
      }
    });

    function renderDiagnostics() {
      if (!diagnosticsEl) { return; }
      diagnosticsEl.innerHTML = "";
      ws.getErrors().forEach(function (e) {
        var div = document.createElement("div");
        div.className = "diag";
        if (e.script) {
          // Erreur dans un script : on demande à l'afficher (composant Scripts).
          div.textContent = "script @" + e.script + " ligne " + e.line + ":" +
            e.column + " — " + e.message;
          div.onclick = function () { ws.reveal("scripts", e); };
        } else {
          div.textContent = "ligne " + e.line + ":" + e.column + " — " + e.message;
          div.onclick = function () {
            cm.setCursor({line: Math.max(0, e.line - 1), ch: e.column || 0});
            cm.focus();
          };
        }
        diagnosticsEl.appendChild(div);
      });
    }

    var offs = [
      ws.on("change", function (c) {
        if (c.what !== "script" || c.origin === self) { return; }
        var wasEmpty = !cm.getValue();
        loading = true;
        try { cm.setValue(ws.getScript()); } finally { loading = false; }
        // Premier contenu d'un éditeur vide : rien à annuler (Ctrl+Z ne
        // doit pas ramener au texte vide d'avant le chargement).
        if (wasEmpty) { cm.clearHistory(); }
      }),
      ws.on("analyze", function () { cm.performLint(); renderDiagnostics(); }),
      ws.on("reveal", function (r) {
        if (r.component !== "editor" || !r.detail.line) { return; }
        cm.setCursor({line: Math.max(0, r.detail.line - 1), ch: r.detail.column || 0});
        cm.focus();
      }),
      ws.attachTextEditor({
        // replaceRange garde le curseur et l'historique d'annulation, là où
        // un setValue complet les perdrait.
        insertText: function (index, text) { cm.replaceRange(text, cm.posFromIndex(index)); },
      }),
    ];

    if (ws.getAnalysis().errors.length) { renderDiagnostics(); }

    return Object.assign(self, {
      codemirror: cm,
      // CodeMirror mesure sa largeur au rendu : remesurer quand le conteneur
      // redevient visible ou change de taille.
      activate: function () { cm.refresh(); },
      refresh: function () { cm.refresh(); },
      focus: function () { cm.focus(); },
      destroy: function () { offs.forEach(function (off) { off(); }); },
    });
  }, {label: "Éditeur", description: "Texte du workflow, intellisense et erreurs positionnées"});

  // ------------------------------------------------------------------
  // Composant « status »
  // ------------------------------------------------------------------

  UW.define("status", function (el, options) {
    var ws = options.workspace;
    el.classList.add("status");
    el.textContent = "—";
    var offs = [
      ws.on("analyze", function (data) {
        if (data.ok) {
          el.textContent = data.is_fragment ? "fragment valide" : "script valide";
          el.className = el.className.replace(/\b(ok|ko)\b/g, "").trim() + " ok";
        } else {
          el.textContent = data.errors.length + " erreur(s)";
          el.className = el.className.replace(/\b(ok|ko)\b/g, "").trim() + " ko";
        }
      }),
      ws.on("analyze-error", function () {
        el.textContent = "serveur injoignable";
        el.className = el.className.replace(/\b(ok|ko)\b/g, "").trim() + " ko";
      }),
    ];
    return {destroy: function () { offs.forEach(function (off) { off(); }); }};
  }, {label: "Statut", description: "Résultat de la dernière analyse"});

})();
