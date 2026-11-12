/* urban-workflow — composants d'édition : noyau.
 *
 * Décision utilisateur du 2026-11-08 : l'éditeur n'est pas une page
 * figée mais un jeu de **composants graphiques indépendants** qu'une
 * application cliente monte où elle veut, selon ses besoins (l'éditeur de
 * texte seul, le diagramme seul, les deux côte à côte, des onglets…).
 *
 * Deux notions :
 *
 * - l'**espace de travail** (``UrbanWorkflow.createWorkspace``) porte les
 *   données partagées — le script du workflow, les règles simulées, les
 *   schémas, les scripts, les événements d'exemple — ainsi que la dernière
 *   analyse du serveur. Il parle à l'API, persiste (ou non) ses données et
 *   prévient ses abonnés. Aucun composant n'en est propriétaire : on peut
 *   n'en monter aucun, ou deux éditeurs sur le même espace ;
 * - les **composants** (``UrbanWorkflow.mount(nom, élément, options)``)
 *   s'affichent dans l'élément qu'on leur donne, sans id fixe dans la page,
 *   et ne communiquent que par l'espace de travail.
 *
 * Pas d'étape de construction (fichiers ES5 servis tels quels, comme le
 * reste du playground) ; ``static/urban-workflow.js`` les concatène.
 */
(function () {
  "use strict";

  var UW = window.UrbanWorkflow = window.UrbanWorkflow || {};

  // ------------------------------------------------------------------
  // Utilitaires partagés
  // ------------------------------------------------------------------

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function reEscape(text) { return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  /** Petit constructeur DOM : h("button", {class: "x", onclick: f}, [enfants]). */
  function h(tag, attrs, children) {
    var element = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (key === "text") { element.textContent = value; }
      else if (key === "html") { element.innerHTML = value; }
      else if (key.indexOf("on") === 0) { element[key] = value; }
      else if (key === "checked" || key === "value" || key === "hidden") {
        element[key] = value;
      } else { element.setAttribute(key, value); }
    });
    (children || []).forEach(function (child) {
      element.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return element;
  }

  /** Élément [data-ref=nom] DANS root : plusieurs instances d'un même
   * composant coexistent dans une page, des id fixes se télescoperaient. */
  function ref(root, name) { return root.querySelector("[data-ref='" + name + "']"); }

  var uidSeq = 0;
  function uid(prefix) { return (prefix || "uw") + "-" + (++uidSeq); }

  UW.util = {esc: esc, reEscape: reEscape, h: h, ref: ref, uid: uid};

  // ------------------------------------------------------------------
  // Adresse de l'API
  // ------------------------------------------------------------------
  //
  // Par défaut, déduite de l'URL de ce fichier : les composants chargés
  // depuis <base>/static/… parlent à <base>/api/…, que le playground soit
  // servi à la racine ou monté sous un préfixe (/outils/workflow/), et même
  // quand la page hôte vit sur un autre chemin. Une application qui sert
  // l'API ailleurs passe ``apiBase`` à createWorkspace.

  var scriptSrc = document.currentScript && document.currentScript.src;
  // static/uw/core.js ou static/urban-workflow.js (le paquet concaténé).
  UW.defaultApiBase = scriptSrc
    ? scriptSrc.replace(/[?#].*$/, "").replace(/static\/(?:uw\/)?[^\/]*$/, "") : "";

  // ------------------------------------------------------------------
  // Petit émetteur d'événements
  // ------------------------------------------------------------------

  function emitter() {
    var handlers = {};
    return {
      on: function (name, fn) {
        (handlers[name] = handlers[name] || []).push(fn);
        return function off() {
          handlers[name] = (handlers[name] || []).filter(function (f) { return f !== fn; });
        };
      },
      emit: function (name, detail) {
        (handlers[name] || []).slice().forEach(function (fn) {
          try { fn(detail); } catch (err) {
            // Un abonné défaillant ne doit pas priver les autres de l'événement.
            if (window.console) { console.error("urban-workflow:", name, err); }
          }
        });
      },
    };
  }

  // ------------------------------------------------------------------
  // Persistance des données de l'espace de travail
  // ------------------------------------------------------------------
  //
  // storage : "local" (défaut, localStorage du navigateur), false (rien
  // n'est gardé : l'application fournit les données à chaque montage) ou
  // un objet {load(nom) -> valeur|null, save(nom, valeur)} pour ranger les
  // règles, schémas et scripts là où l'application le décide.

  function makeStore(storage, key) {
    if (storage === false || storage === null) {
      return {load: function () { return null; }, save: function () {}};
    }
    if (storage && typeof storage.load === "function") { return storage; }
    return {
      load: function (name) {
        try { return JSON.parse(localStorage.getItem(key + "-" + name)); }
        catch (e) { return null; }
      },
      save: function (name, value) {
        try { localStorage.setItem(key + "-" + name, JSON.stringify(value)); }
        catch (e) { /* stockage indisponible : on continue sans persistance */ }
      },
    };
  }

  function copy(value) { return JSON.parse(JSON.stringify(value)); }

  // ------------------------------------------------------------------
  // Espace de travail
  // ------------------------------------------------------------------

  var EMPTY_SYMBOLS = {events: [], rules: [], actions: [], constants: [], states: []};

  /**
   * options :
   * - apiBase : préfixe des appels (« https://h/outils/workflow/ ») ;
   * - storage, storageKey : persistance (voir makeStore ; clé par défaut
   *   « uw-playground », celle des versions précédentes du playground) ;
   * - script, rules, schemas, scripts, events : données initiales (une
   *   valeur fournie l'emporte sur celle du stockage) ;
   * - analyzeDelay : délai (ms) entre une modification et l'analyse.
   */
  function createWorkspace(options) {
    options = options || {};
    var bus = emitter();
    var apiBase = options.apiBase != null ? String(options.apiBase) : UW.defaultApiBase;
    if (apiBase && !/\/$/.test(apiBase)) { apiBase += "/"; }
    var store = makeStore(options.storage, options.storageKey || "uw-playground");
    var delay = options.analyzeDelay != null ? options.analyzeDelay : 450;

    function initial(name) {
      if (options[name] !== undefined) { return copy(options[name]); }
      var stored = store.load(name);
      return Array.isArray(stored) ? stored : [];
    }

    var data = {
      script: options.script || "",
      rules: initial("rules"),
      schemas: initial("schemas"),
      scripts: initial("scripts"),
      // Les événements d'exemple ne sont pas persistés (comme avant) :
      // ils accompagnent le script affiché.
      events: options.events ? copy(options.events) : [],
    };
    var analysis = {ok: false, errors: [], symbols: copy(EMPTY_SYMBOLS), summary: null};
    var textEditors = [];
    var timer = null;
    var seq = 0;

    function api(path, body, method) {
      var init = {method: method || (body === undefined ? "GET" : "POST")};
      if (body !== undefined) {
        init.headers = {"Content-Type": "application/json"};
        init.body = JSON.stringify(body);
      }
      return fetch(apiBase + path, init).then(function (r) {
        if (!r.ok && r.status !== 400) { throw new Error("HTTP " + r.status); }
        return r.json();
      });
    }

    function payload() {
      return {script: data.script, rules: data.rules, schemas: data.schemas,
              scripts: data.scripts};
    }

    function changed(what, origin) {
      if (what !== "script" && what !== "events") { store.save(what, data[what]); }
      bus.emit("change", {what: what, origin: origin});
      if (what !== "events") { schedule(); }
    }

    function schedule() {
      clearTimeout(timer);
      timer = setTimeout(function () { ws.analyze(); }, delay);
    }

    function upsert(list, name, fields) {
      var found = list.some(function (item) {
        if (item.name === name) { Object.assign(item, fields); return true; }
        return false;
      });
      if (!found) { list.push(Object.assign({name: name}, fields)); }
    }

    var ws = {
      apiBase: apiBase,
      api: api,
      on: bus.on,
      emit: bus.emit,
      ruleFunctions: UW.RULE_FUNCTIONS,

      // --- script du workflow ---
      getScript: function () { return data.script; },
      /** origin : qui modifie (un composant passe son instance), pour que
       * l'éditeur à l'origine ne se recharge pas lui-même. */
      setScript: function (text, origin) {
        text = text == null ? "" : String(text);
        if (text === data.script) { return; }
        data.script = text;
        changed("script", origin);
      },
      /** Insertion ponctuelle (index = position dans le texte). Si un
       * éditeur de texte est monté, c'est lui qui insère : il garde le
       * curseur et l'historique d'annulation, qu'un remplacement complet
       * perdrait. */
      insertText: function (index, text) {
        if (textEditors.length) { textEditors[0].insertText(index, text); return; }
        ws.setScript(data.script.slice(0, index) + text + data.script.slice(index), "insert");
      },
      attachTextEditor: function (editor) {
        textEditors.push(editor);
        return function () {
          textEditors = textEditors.filter(function (e) { return e !== editor; });
        };
      },

      // --- règles simulées (règles de code absentes du navigateur) ---
      getRules: function () { return data.rules; },
      setRules: function (rules, origin) { data.rules = copy(rules || []); changed("rules", origin); },
      setRule: function (rule, origin) {
        data.rules = data.rules.filter(function (r) { return r.name !== rule.name; });
        data.rules.push(copy(rule));
        changed("rules", origin);
      },
      removeRule: function (name, origin) {
        data.rules = data.rules.filter(function (r) { return r.name !== name; });
        changed("rules", origin);
      },

      // --- schémas (JSON Schema en YAML) ---
      getSchemas: function () { return data.schemas; },
      findSchema: function (name) {
        return data.schemas.filter(function (s) { return s.name === name; })[0] || null;
      },
      setSchemas: function (list, origin) { data.schemas = copy(list || []); changed("schemas", origin); },
      setSchema: function (name, yaml, origin) {
        upsert(data.schemas, name, {yaml: yaml});
        changed("schemas", origin);
      },
      removeSchema: function (name, origin) {
        data.schemas = data.schemas.filter(function (s) { return s.name !== name; });
        changed("schemas", origin);
      },

      // --- scripts (règles AS @nom, artefacts USING @nom) ---
      getScripts: function () { return data.scripts; },
      findScript: function (name) {
        return data.scripts.filter(function (s) { return s.name === name; })[0] || null;
      },
      setScripts: function (list, origin) { data.scripts = copy(list || []); changed("scripts", origin); },
      setScriptSource: function (name, source, language, origin) {
        var existing = ws.findScript(name);
        upsert(data.scripts, name, {
          source: source,
          language: language || (existing && existing.language) || "expression",
        });
        changed("scripts", origin);
      },
      removeScript: function (name, origin) {
        data.scripts = data.scripts.filter(function (s) { return s.name !== name; });
        changed("scripts", origin);
      },

      // --- événements d'exemple (simulation, aperçu des artefacts) ---
      getEvents: function () { return data.events; },
      setEvents: function (events, origin) {
        data.events = Array.isArray(events) ? copy(events) : [];
        changed("events", origin);
      },

      // --- analyse ---
      getAnalysis: function () { return analysis; },
      getSymbols: function () { return analysis.symbols; },
      getErrors: function () { return analysis.errors; },
      /** Analyse immédiate ; seule la réponse la plus récente compte (une
       * réponse lente d'un texte périmé ne doit pas écraser la suivante). */
      analyze: function () {
        clearTimeout(timer);
        var mine = ++seq;
        return api("api/analyze", payload()).then(function (result) {
          if (mine !== seq) { return analysis; }
          analysis = {
            ok: !!result.ok,
            is_fragment: !!result.is_fragment,
            errors: result.errors || [],
            symbols: result.symbols || analysis.symbols,
            summary: result.summary || null,
          };
          bus.emit("analyze", analysis);
          return analysis;
        }, function (err) {
          if (mine === seq) { bus.emit("analyze-error", err); }
          throw err;
        });
      },
      payload: payload,
      simulate: function (events) {
        return api("api/simulate", Object.assign(payload(), {events: events || data.events}));
      },

      // --- exemples ---
      /** Charge un exemple {script, rules, schemas, scripts, events} : les
       * règles sont remplacées, les schémas et scripts fusionnés par nom
       * (ceux de l'utilisateur restent), comme le playground l'a toujours
       * fait. */
      loadExample: function (example) {
        if (!example) { return; }
        if (example.rules && example.rules.length) { data.rules = copy(example.rules); store.save("rules", data.rules); }
        (example.schemas || []).forEach(function (s) { upsert(data.schemas, s.name, {yaml: s.yaml}); });
        store.save("schemas", data.schemas);
        (example.scripts || []).forEach(function (s) {
          upsert(data.scripts, s.name, {language: s.language || "expression", source: s.source});
        });
        store.save("scripts", data.scripts);
        data.events = copy(example.events || []);
        bus.emit("change", {what: "rules"});
        bus.emit("change", {what: "schemas"});
        bus.emit("change", {what: "scripts"});
        bus.emit("change", {what: "events"});
        data.script = "";   // force l'émission même si le texte est identique
        ws.setScript(example.script || "", "example");
      },

      /** Demande d'affichage : « montrez le composant X (et ce détail) ».
       * Les conteneurs (onglets) activent l'onglet qui le porte ; le
       * composant visé réagit au détail (ex. ouvrir un script à une ligne). */
      reveal: function (component, detail) {
        bus.emit("reveal", {component: component, detail: detail || {}});
      },
    };
    return ws;
  }

  UW.createWorkspace = createWorkspace;

  // ------------------------------------------------------------------
  // Registre des composants
  // ------------------------------------------------------------------
  //
  // Un composant = function (el, options) -> instance, où options porte au
  // moins {workspace}. L'instance expose au minimum :
  //   activate()  — appelé quand le composant redevient visible (un
  //                 conteneur l'avait caché) : CodeMirror, X6 remesurent ;
  //   destroy()   — désabonnement et nettoyage.

  var registry = {};

  UW.define = function (name, factory, meta) {
    registry[name] = {factory: factory, meta: meta || {}};
  };

  UW.components = function () {
    return Object.keys(registry).map(function (name) {
      return Object.assign({name: name}, registry[name].meta);
    });
  };

  UW.mount = function (name, el, options) {
    var entry = registry[name];
    if (!entry) { throw new Error("urban-workflow: composant inconnu « " + name + " »"); }
    if (typeof el === "string") { el = document.querySelector(el); }
    if (!el) { throw new Error("urban-workflow: élément introuvable pour « " + name + " »"); }
    options = options || {};
    if (!options.workspace) {
      throw new Error("urban-workflow: le composant « " + name + " » attend {workspace}");
    }
    el.classList.add("uw", "uw-" + name);
    var instance = entry.factory(el, options) || {};
    instance.name = name;
    instance.el = el;
    instance.activate = instance.activate || function () {};
    var destroy = instance.destroy || function () {};
    instance.destroy = function () {
      destroy();
      el.classList.remove("uw", "uw-" + name);
      el.innerHTML = "";
    };
    return instance;
  };

  // ------------------------------------------------------------------
  // Langages : DSL du workflow, expressions des règles, JSLT
  // ------------------------------------------------------------------

  UW.KEYWORDS = [
    "NAME", "VERSION", "CONCURENCY", "DESCRIPTION", "MATCHING", "AS", "UNIQUE",
    "DEFINE", "EVENT", "RULE", "ACTION", "ARTIFACT", "USING", "CONST",
    "INITIALIZE", "WORKFLOW", "ON", "WHEN", "RECURSIVE", "SWITCH",
    "STATE", "ENTER", "EXIT", "AND", "OR", "NOT",
    "EXECUTE", "STORE", "EXPIRE", "AFTER", "WAITING", "BEFORE",
    "MINUTE", "HOUR", "DAY", "TEXT", "INTEGER", "DECIMAL",
    "INCLUDE", "FRAGMENT", "IN", "IS", "NULL", "TRUE", "FALSE",
  ];

  // Miroir de urban_workflow.dsl.expressions.FUNCTIONS, avec les types
  // affichés par la complétion (les fonctions ne lèvent jamais : un argument
  // du mauvais type donne NULL, ou FALSE pour CONTAINS).
  UW.RULE_FUNCTIONS = [
    {name: "NOW", params: [], returns: "DATETIME",
     doc: "date et heure courantes (horloge du moteur)"},
    {name: "LENGTH", params: [["TEXT|LIST|OBJECT", "valeur"]], returns: "INTEGER",
     doc: "longueur d'un texte, d'une liste ou d'un objet"},
    {name: "CONTAINS", params: [["TEXT|LIST|OBJECT", "conteneur"], ["ANY", "element"]],
     returns: "BOOLEAN", doc: "sous-chaîne, élément de liste ou clé d'objet"},
    {name: "DAYS_BETWEEN", params: [["DATETIME", "debut"], ["DATETIME", "fin"]],
     returns: "DECIMAL", doc: "nombre de jours de debut à fin"},
    {name: "HOURS_BETWEEN", params: [["DATETIME", "debut"], ["DATETIME", "fin"]],
     returns: "DECIMAL", doc: "nombre d'heures de debut à fin"},
    {name: "MINUTES_BETWEEN", params: [["DATETIME", "debut"], ["DATETIME", "fin"]],
     returns: "DECIMAL", doc: "nombre de minutes de debut à fin"},
  ];
  UW.RULE_FUNCTIONS.forEach(function (f) {
    f.signature = f.name + "(" + f.params.map(function (p) {
      return p[0] + " " + p[1]; }).join(", ") + ") → " + f.returns;
  });

  if (window.CodeMirror) {
    CodeMirror.defineSimpleMode("workflow-dsl", {
      start: [
        {regex: /--.*/, token: "comment"},
        {regex: /\/\*/, token: "comment", next: "comment"},
        // Chemins @ (@IncomingEvent.Liste[0], @state['p'], @Workflow.X) —
        // avant la règle des chaînes, qui avalerait le ['p'].
        {regex: /@[A-Za-z][\w$#]*(?:\.[A-Za-z][\w$#]*|\[\d+\]|\['(?:[^'\n]|'')*'\])*/, token: "variable-2"},
        {regex: /'(?:[^'\n]|'')*'/, token: "string"},
        {regex: new RegExp("\\b(?:" + UW.KEYWORDS.join("|") + ")\\b"), token: "keyword"},
        {regex: new RegExp("\\b(?:" + UW.RULE_FUNCTIONS.map(function (f) {
          return f.name; }).join("|") + ")(?=\\s*\\()", "i"), token: "builtin"},
        {regex: /\b\d+(?:\.\d+)?\b/, token: "number"},
        {regex: /[A-Za-z][\w$#]*/, token: "variable"},
        {regex: /!=|<>|<=|>=|[<>+*\/-]/, token: "operator"},
        {regex: /[();=,.\[\]]/, token: "punctuation"},
      ],
      comment: [
        {regex: /.*?\*\//, token: "comment", next: "start"},
        {regex: /.*/, token: "comment"},
      ],
    });

    CodeMirror.defineSimpleMode("jslt", {
      start: [
        {regex: /"(?:[^"\\]|\\.)*"/, token: "string"},
        {regex: /\$(?:\.[A-Za-z_][\w]*|\[\d+\])*/, token: "variable-2"},
        {regex: /\b(?:true|false|null|let|def|if|else|for|in)\b/, token: "keyword"},
        {regex: /[A-Za-z_]\w*(?=\s*\()/, token: "builtin"},
        {regex: /-?\d+(?:\.\d+)?/, token: "number"},
        {regex: /==|!=|<=|>=|&&|\|\||[<>+*\/%!-]/, token: "operator"},
        {regex: /[{}\[\]():,.]/, token: "punctuation"},
      ],
    });
  }
})();
