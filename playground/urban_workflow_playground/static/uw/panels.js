/* Composants de paramétrage et de lecture :
 *
 * - « rules »      — règles métier simulées (les règles de code n'existent
 *                    pas dans le navigateur : nom, paramètres, résultat) ;
 * - « schemas »    — schémas JSON (YAML) des événements, états et artefacts ;
 * - « structure »  — configuration compilée (initialiseurs, états, transitions) ;
 * - « simulation » — événements rejoués sur le vrai moteur en mémoire ;
 * - « help »       — aide-mémoire du langage et des composants.
 */
(function () {
  "use strict";

  var UW = window.UrbanWorkflow;
  var esc = UW.util.esc;
  var ref = UW.util.ref;

  function offAll(offs) { return function () { offs.forEach(function (off) { off(); }); }; }

  // ------------------------------------------------------------------
  // « rules »
  // ------------------------------------------------------------------

  UW.define("rules", function (el, options) {
    var ws = options.workspace;
    el.innerHTML =
      "<p class='hint-text'>Règles métier disponibles pour les conditions " +
      "<code>WHEN</code> : nom, paramètres typés et résultat simulé. Les règles " +
      "qui référencent un script (<code>AS @…</code>) sont évaluées pour de vrai.</p>" +
      "<div data-ref='list'></div>" +
      "<form class='uw-inline-form' data-ref='form'>" +
      "<input data-ref='name' placeholder='NomDeLaRegle' required pattern='[A-Za-z][A-Za-z0-9_]*'>" +
      "<input data-ref='params' placeholder='TEXT champ, DECIMAL seuil'>" +
      "<label class='inline'><input type='checkbox' data-ref='result' checked> vraie</label>" +
      "<button type='submit'>Ajouter</button></form>";
    var listEl = ref(el, "list");

    function render() {
      listEl.innerHTML = "";
      // Règles implémentées par un script (DEFINE RULE … AS @nom) : évaluées
      // par le moteur, rien à simuler ; une entrée homonyme est ignorée.
      // Clic = ouvrir le script.
      var withScript = {};
      (ws.getSymbols().rules || []).forEach(function (rule) {
        if (!rule.script) { return; }
        withScript[rule.name] = true;
        var row = document.createElement("div");
        row.className = "rule-row dsl-rule";
        row.title = "Ouvrir le script @" + rule.script;
        row.innerHTML = "<code>" + esc(rule.name + "(" + (rule.params || []).map(function (p) {
          return p.type + " " + p.name; }).join(", ") + ")") + "</code>" +
          "<small>script @" + esc(rule.script) + "</small>";
        row.onclick = function () { ws.reveal("scripts", {script: rule.script}); };
        listEl.appendChild(row);
      });
      var rules = ws.getRules();
      if (!rules.length) {
        listEl.insertAdjacentHTML("beforeend", "<p class='hint-text'>Aucune règle " +
          "paramétrée. Les conditions WHEN exigeront leur enregistrement.</p>");
      }
      rules.forEach(function (rule) {
        var row = document.createElement("div");
        row.className = "rule-row";
        var signature = rule.name + "(" + (rule.params || []).map(function (p) {
          return p.type + " " + p.name;
        }).join(", ") + ")";
        if (withScript[rule.name]) {
          row.className += " overridden";
          row.title = "Ignorée : cette règle est implémentée par un script (AS @…)";
        }
        row.innerHTML = "<code>" + esc(signature) + "</code>" +
          "<label class='inline'><input type='checkbox' " +
          (rule.result ? "checked" : "") + "> vraie</label>" +
          "<button type='button' class='remove' title='Supprimer'>✕</button>";
        row.querySelector("input").onchange = function (e) {
          ws.setRule(Object.assign({}, rule, {result: e.target.checked}));
        };
        row.querySelector(".remove").onclick = function () { ws.removeRule(rule.name); };
        listEl.appendChild(row);
      });
    }

    ref(el, "form").onsubmit = function (e) {
      e.preventDefault();
      var name = ref(el, "name").value.trim();
      var paramsText = ref(el, "params").value.trim();
      var params = [];
      if (paramsText) {
        paramsText.split(",").forEach(function (part) {
          var m = /^\s*(TEXT|INTEGER|DECIMAL)?\s*([A-Za-z]\w*)\s*$/i.exec(part);
          if (m) { params.push({name: m[2], type: (m[1] || "TEXT").toUpperCase()}); }
        });
      }
      if (!name) { return; }
      ws.setRule({name: name, params: params, result: ref(el, "result").checked});
      e.target.reset();
      ref(el, "result").checked = true;
    };

    render();
    return {destroy: offAll([
      ws.on("change", function (c) { if (c.what === "rules") { render(); } }),
      ws.on("analyze", render),
    ])};
  }, {label: "Règles", description: "Règles métier simulées pour les conditions WHEN"});

  // ------------------------------------------------------------------
  // « schemas »
  // ------------------------------------------------------------------

  UW.define("schemas", function (el, options) {
    var ws = options.workspace;
    el.innerHTML =
      "<p class='hint-text'>JSON Schema écrits en YAML, référencés par " +
      "<code>AS @nom</code> : <code>DEFINE EVENT</code> (payload validé : socle " +
      "commun + schéma), <code>DEFINE STATE</code> (champs métier de l'état) et " +
      "<code>DEFINE ARTIFACT</code> (JSON produit validé).</p>" +
      "<div data-ref='list'></div>" +
      "<form class='uw-schema-form' data-ref='form'>" +
      "<input data-ref='name' placeholder='schema_MonEvenement' required pattern='[A-Za-z][A-Za-z0-9_]*'>" +
      "<textarea data-ref='yaml' spellcheck='false' rows='5' placeholder='type: object\n" +
      "properties:\n  Montant: {type: number, minimum: 0}\nrequired: [Montant]'></textarea>" +
      "<button type='submit'>Ajouter le schéma</button></form>";
    var listEl = ref(el, "list");

    /** Qui référence chaque schéma (événement, état, artefact). */
    function users() {
      var s = ws.getSymbols(), byName = {};
      function add(name, label) { if (name) { (byName[name] = byName[name] || []).push(label); } }
      (s.event_details || []).forEach(function (d) { add(d.schema_ref, "événement " + d.name); });
      (s.state_details || []).forEach(function (d) { add(d.schema_ref, "état " + d.name); });
      (s.artifacts || []).forEach(function (d) { add(d.schema_ref, "artefact " + d.name); });
      return byName;
    }

    function render() {
      listEl.innerHTML = "";
      var schemas = ws.getSchemas();
      if (!schemas.length) {
        listEl.innerHTML = "<p class='hint-text'>Aucun schéma. Les références " +
          "AS @… resteront non résolues (erreur à l'analyse).</p>";
      }
      var used = users();
      schemas.forEach(function (schema) {
        var row = document.createElement("div");
        row.className = "rule-row";
        row.innerHTML = "<code title=\"" + esc(schema.yaml) + "\">@" + esc(schema.name) +
          "</code><small>" + esc((used[schema.name] || ["inutilisé"]).join(", ")) + "</small>" +
          "<button type='button' class='remove' title='Supprimer'>✕</button>";
        row.querySelector(".remove").onclick = function () { ws.removeSchema(schema.name); };
        listEl.appendChild(row);
      });
    }

    ref(el, "form").onsubmit = function (e) {
      e.preventDefault();
      var name = ref(el, "name").value.trim();
      var yaml = ref(el, "yaml").value;
      if (!name || !yaml.trim()) { return; }
      ws.setSchema(name, yaml);
      e.target.reset();
    };

    render();
    return {destroy: offAll([
      ws.on("change", function (c) { if (c.what === "schemas") { render(); } }),
      ws.on("analyze", render),
    ])};
  }, {label: "Schémas", description: "Schémas JSON des événements, états et artefacts"});

  // ------------------------------------------------------------------
  // « structure »
  // ------------------------------------------------------------------

  UW.define("structure", function (el, options) {
    var ws = options.workspace;

    function render() {
      var summary = ws.getAnalysis().summary;
      if (!summary) {
        el.innerHTML = "<p class='hint-text'>Structure affichée quand le script est valide.</p>";
        return;
      }
      var html = "<h3>" + esc(summary.name) + " <small>v" + summary.version +
        " · concurrence " + summary.concurrency + "</small></h3>";
      if (Object.keys(summary.filters || {}).length) {
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
      (summary.initializers || []).forEach(function (init) {
        init.switchs.forEach(function (sw) {
          html += "<div class='node init'>⚡ " + esc(init.event) +
            (sw.when ? " <em>si " + esc(sw.when) + "</em>" : "") +
            " → <b>" + esc(sw.target) + "</b>" +
            (init.recursive ? " <small>(récursif)</small>" : "") + "</div>";
        });
      });
      (summary.states || []).forEach(function (state) {
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

    render();
    return {destroy: ws.on("analyze", render)};
  }, {label: "Structure", description: "Configuration compilée : initialiseurs, états, transitions"});

  // ------------------------------------------------------------------
  // « simulation »
  // ------------------------------------------------------------------

  UW.define("simulation", function (el, options) {
    var ws = options.workspace;
    var self = {};
    el.innerHTML =
      "<p class='hint-text'>Une liste JSON d'événements, rejoués dans l'ordre sur un " +
      "moteur en mémoire.</p>" +
      "<textarea class='uw-events-input' data-ref='events' spellcheck='false'></textarea>" +
      "<button type='button' class='uw-run' data-ref='run'>Rejouer les événements</button>" +
      "<div data-ref='result'></div>";
    var input = ref(el, "events");
    var out = ref(el, "result");

    function showEvents() { input.value = JSON.stringify(ws.getEvents(), null, 2); }

    // Le texte saisi devient les événements de l'espace dès qu'il est un
    // JSON valide : l'aperçu des artefacts s'en sert comme exemple.
    input.oninput = function () {
      try {
        var value = JSON.parse(input.value || "[]");
        if (Array.isArray(value)) { ws.setEvents(value, self); }
      } catch (e) { /* saisie en cours : on attend un JSON complet */ }
    };

    function run() {
      var events;
      try {
        events = JSON.parse(input.value || "[]");
      } catch (e) {
        out.innerHTML = "<div class='diag'>JSON des événements invalide : " + esc(e.message) + "</div>";
        return Promise.resolve(null);
      }
      out.innerHTML = "<p class='hint-text'>Simulation…</p>";
      return ws.simulate(events).then(function (data) {
        render(data);
        return data;
      }, function (e) {
        out.innerHTML = "<div class='diag'>" + esc(String(e)) + "</div>";
        return null;
      });
    }
    ref(el, "run").onclick = run;

    function render(data) {
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
            "événement non déclaré, pas d'initialiseur, switch sans route " +
            "ou doublon).</p>";
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
          (w.states && w.states.length
            ? "<div class='sim-log'>États : " + w.states.map(function (s) {
                return esc(s.name) + " <small>(" + esc(s.uuid.slice(0, 8)) +
                  "…, évt " + esc((s.event_id || "∅").slice(0, 8)) + "…)</small>";
              }).join(" → ") + "</div>"
            : "") +
          "<pre>" + esc(JSON.stringify(w.extended_datas, null, 1)) + "</pre></div>";
      });
      out.innerHTML = html;
    }

    showEvents();
    var off = ws.on("change", function (c) {
      if (c.what === "events" && c.origin !== self) { showEvents(); }
    });
    return Object.assign(self, {run: run, destroy: off});
  }, {label: "Simulation", description: "Rejouer des événements sur le moteur en mémoire"});

  // ------------------------------------------------------------------
  // « help »
  // ------------------------------------------------------------------

  UW.define("help", function (el) {
    el.innerHTML = "<ul class='hint-text'>" +
      "<li><kbd>Ctrl</kbd>+<kbd>Espace</kbd> : complétion (aussi automatique en tapant).</li>" +
      "<li>La complétion est contextuelle : événements après <code>ON EVENT</code>, " +
      "états après <code>SWITCH</code>, règles après <code>WHEN</code>/<code>AND</code>/" +
      "<code>OR</code>/<code>NOT</code>, actions après <code>EXECUTE</code>, chemins après " +
      "<code>@</code>.</li>" +
      "<li>Les erreurs (syntaxe et validation) sont soulignées dans l'éditeur et listées " +
      "sous celui-ci — cliquer pour y aller.</li>" +
      "<li><code>DEFINE EVENT X '…' AS @schema UNIQUE (Prop, …);</code> : le schéma valide " +
      "le payload ; UNIQUE et la propriété <code>DedupKey</code> de l'émetteur (prioritaire) " +
      "bloquent les doublons en simulation. Sans l'un ni l'autre, le moteur dédoublonne " +
      "sur l'<code>Uuid</code> du payload, ou à défaut sur <code>Name</code> + " +
      "<code>EventDate</code> (+ <code>ExternalId</code>).</li>" +
      "<li><code>regle(p = @IncomingEvent.Montant)</code> : chemin dans l'événement entrant " +
      "(socle + payload, <code>@IncomingEvent.Lignes[0].Qte</code>). Un chemin absent du " +
      "schéma est signalé.</li>" +
      "<li><code>@state.…</code> : l'instance de l'état du bloc <code>DEFINE STATE</code> " +
      "courant (<code>Name</code>, <code>Uuid</code>, <code>CreationDate</code>, " +
      "<code>EventId</code>). Une instance est créée à chaque <code>SWITCH</code> ; " +
      "indisponible dans <code>INITIALIZE WORKFLOW</code>.</li>" +
      "<li><code>DEFINE RULE R (DECIMAL seuil) '…' AS @montant_eleve;</code> : la règle est " +
      "implémentée par le script <code>@montant_eleve</code> (composant Scripts, hors du " +
      "workflow). Langage <code>expression</code> : <code>= != &lt; &lt;= &gt; &gt;=</code>, " +
      "<code>+ - * /</code>, <code>IN (…)</code>, <code>IS [NOT] NULL</code>, " +
      "<code>AND/OR/NOT</code>, fonctions <code>NOW()</code>, <code>DAYS_BETWEEN</code>, " +
      "<code>LENGTH</code>, <code>CONTAINS</code>…</li>" +
      "<li><code>DEFINE ARTIFACT X 'l' AS @schema USING @script;</code> puis " +
      "<code>EXECUTE A(corps = @artifact.X)</code> : JSON produit par un script " +
      "<code>jslt</code>, validé par le schéma, remis à l'action.</li>" +
      "<li>Référence : <code>docs/guide-dsl.md</code>, <code>docs/guide-regles.md</code>, " +
      "<code>docs/guide-artefacts.md</code>.</li>" +
      "</ul>";
    return {};
  }, {label: "Aide", description: "Aide-mémoire du langage"});
})();
