/* Vue « Événements » : liste les événements du script et édite leur
 * structure avec l'éditeur visuel de schémas du portail Miles
 * (window.UWSchemaEditor, bundle vendor/schema-editor.js).
 *
 * Un événement = le socle commun (BASE_EVENT_SCHEMA, servi par
 * /api/base-event-schema, NON modifiable) + son schéma métier optionnel
 * (DEFINE EVENT … AS @schema, YAML du panneau Paramétrage). Le fork de
 * l'éditeur ne verrouille pas un champ isolé : le socle est donc une
 * seconde instance en lecture seule, au-dessus de l'instance éditable.
 *
 * Source de vérité inchangée : le script (déclarations) et les schémas du
 * panneau (YAML). Cette vue ne fait que les modifier par le pont
 * window.PlaygroundBridge ; elle se redessine à chaque analyse.
 */
(function () {
  "use strict";

  var bridge = window.PlaygroundBridge;
  var Editor = window.UWSchemaEditor;
  var listEl = document.getElementById("ev-list");
  var detailEl = document.getElementById("ev-detail");

  var baseSchema = null;      // socle, chargé une fois
  var selected = null;        // nom de l'événement affiché
  var shownKey = "";          // ce qui est affiché (évite de remonter les éditeurs)
  var mounted = [];           // instances React à démonter au changement
  var visible = false;

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function reEscape(text) { return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function events() {
    var symbols = bridge.getSymbols();
    if (symbols.event_details && symbols.event_details.length) {
      return symbols.event_details;
    }
    // Script qui ne compile pas : repli sur les noms trouvés par regex, sans
    // détail (la liste reste utilisable, l'édition attend un script valide).
    return (symbols.events || [])
      .filter(function (name) { return name.charAt(0) !== "$" && name.indexOf("__") !== 0; })
      .map(function (name) {
        return {name: name, label: "", schema_ref: "", unique: [], declared: true, partial: true};
      });
  }

  function findSchema(name) {
    var found = null;
    bridge.getSchemas().forEach(function (s) { if (s.name === name) { found = s; } });
    return found;
  }

  // ------------------------------------------------------------------
  // Modifications du script (insertions ponctuelles, annulables)
  // ------------------------------------------------------------------

  /** Ajoute « AS @schema » à la déclaration de l'événement. */
  function addSchemaClause(eventName, schemaName) {
    var script = bridge.getScript();
    // DEFINE EVENT nom 'libellé'? — AS se place juste après (grammaire :
    // key comment? (AS …)? (UNIQUE …)?).
    var re = new RegExp("\\bDEFINE\\s+EVENT\\s+" + reEscape(eventName) +
                        "\\b(\\s*'(?:[^']|'')*')?", "i");
    var match = re.exec(script);
    if (!match) { return false; }
    bridge.insertText(match.index + match[0].length, " AS @" + schemaName);
    return true;
  }

  /** Déclare un événement utilisé mais absent des DEFINE EVENT. */
  function declareEvent(eventName) {
    var script = bridge.getScript();
    var line = "DEFINE EVENT " + eventName + " '" + eventName + "';\n";
    // Après la dernière déclaration d'événement si elle existe, sinon avant
    // la première déclaration/section du script.
    var last = null, re = /\bDEFINE\s+EVENT\b[^;]*;[^\n]*\n?/gi, m;
    while ((m = re.exec(script)) !== null) { last = m; }
    if (last) {
      bridge.insertText(last.index + last[0].length, line);
      return;
    }
    var first = /^[ \t]*(DEFINE|INITIALIZE)\b/im.exec(script);
    bridge.insertText(first ? first.index : script.length, line);
  }

  // ------------------------------------------------------------------
  // Liste
  // ------------------------------------------------------------------

  function renderList() {
    var list = events();
    if (!list.length) {
      listEl.innerHTML = "<p class='hint-text'>Aucun événement dans le script.</p>";
      return;
    }
    if (!selected || !list.some(function (e) { return e.name === selected; })) {
      selected = list[0].name;
    }
    listEl.innerHTML = "";
    list.forEach(function (ev) {
      var item = document.createElement("button");
      item.type = "button";
      item.className = "ev-item" + (ev.name === selected ? " active" : "");
      var badges = "";
      if (!ev.declared) { badges += "<span class='ev-badge warn'>non déclaré</span>"; }
      badges += ev.schema_ref
        ? "<span class='ev-badge'>@" + esc(ev.schema_ref) + "</span>"
        : "<span class='ev-badge muted'>socle seul</span>";
      if (ev.unique && ev.unique.length) { badges += "<span class='ev-badge'>UNIQUE</span>"; }
      item.innerHTML = "<span class='ev-name'>" + esc(ev.name) + "</span>" +
        (ev.label ? "<span class='ev-label'>" + esc(ev.label) + "</span>" : "") +
        "<span class='ev-badges'>" + badges + "</span>";
      item.onclick = function () { selected = ev.name; render(); };
      listEl.appendChild(item);
    });
  }

  // ------------------------------------------------------------------
  // Détail
  // ------------------------------------------------------------------

  function unmountAll() {
    mounted.forEach(function (m) { m.unmount(); });
    mounted = [];
  }

  function mountEditor(container, props) {
    var instance = Editor.mount(container, props);
    mounted.push(instance);
    return instance;
  }

  function reservedClash(schema) {
    if (!baseSchema || !schema || !schema.properties) { return []; }
    return Object.keys(schema.properties).filter(function (p) {
      return Object.prototype.hasOwnProperty.call(baseSchema.properties, p);
    });
  }

  function renderDetail() {
    var ev = null;
    events().forEach(function (e) { if (e.name === selected) { ev = e; } });
    var setting = ev && ev.schema_ref ? findSchema(ev.schema_ref) : null;
    // On ne remonte les éditeurs que si ce qui est montré change de nature :
    // une saisie dans l'éditeur déclenche une analyse, qui ne doit pas
    // détruire l'éditeur sous les doigts de l'utilisateur.
    var key = ev ? [ev.name, ev.label, ev.schema_ref, ev.declared, ev.partial,
                    !!setting, !!baseSchema].join("|") : "";
    if (key === shownKey) { return; }
    shownKey = key;
    unmountAll();
    if (!ev) { detailEl.innerHTML = ""; return; }

    var html = "<header class='ev-head'><h3>" + esc(ev.name) + "</h3>" +
      (ev.label ? "<span class='hint-text'>" + esc(ev.label) + "</span>" : "") +
      (ev.unique && ev.unique.length
        ? "<span class='ev-badge'>UNIQUE (" + ev.unique.map(esc).join(", ") + ")</span>" : "") +
      "</header>";

    if (ev.partial) {
      html += "<p class='notice'>Le script ne compile pas : corrigez-le pour " +
        "éditer la structure de cet événement.</p>";
    } else if (!ev.declared) {
      html += "<p class='notice'>Événement utilisé mais pas déclaré par " +
        "<code>DEFINE EVENT</code>. <button type='button' id='ev-declare'>" +
        "Déclarer dans le script</button></p>";
    }

    html += "<h4 class='section-title'>Champs de base " +
      "<small>socle commun à tout événement — non modifiables</small></h4>" +
      "<div id='ev-base' class='ev-editor locked'></div>";

    html += "<h4 class='section-title'>Champs métier";
    if (ev.schema_ref) { html += " <small>@" + esc(ev.schema_ref) + "</small>"; }
    html += "</h4>";
    if (!ev.schema_ref) {
      html += "<p class='hint-text'>Aucun schéma métier : seul le socle est " +
        "validé.</p>" + (ev.declared && !ev.partial
          ? "<button type='button' id='ev-create' class='primary'>Créer le schéma " +
            "métier</button>" : "");
    } else if (!setting) {
      html += "<p class='notice'>Le script référence <code>@" + esc(ev.schema_ref) +
        "</code> mais ce schéma n'existe pas encore. <button type='button' " +
        "id='ev-create-missing'>Créer @" + esc(ev.schema_ref) + "</button></p>";
    } else {
      html += "<div id='ev-clash' class='notice ko' hidden></div>" +
        "<div id='ev-business' class='ev-editor'></div>" +
        "<details class='ev-yaml'><summary>YAML du schéma</summary>" +
        "<textarea id='ev-yaml' spellcheck='false'></textarea>" +
        "<p id='ev-yaml-error' class='notice ko' hidden></p></details>";
    }
    detailEl.innerHTML = html;

    var declareBtn = document.getElementById("ev-declare");
    if (declareBtn) { declareBtn.onclick = function () { declareEvent(ev.name); }; }

    var createBtn = document.getElementById("ev-create");
    if (createBtn) {
      createBtn.onclick = function () {
        var name = "schema_" + ev.name;
        if (!findSchema(name)) {
          bridge.setSchema(name, "type: object\nproperties: {}\n");
        }
        if (!addSchemaClause(ev.name, name)) {
          createBtn.insertAdjacentHTML("afterend",
            "<p class='notice ko'>Déclaration introuvable dans le script.</p>");
        }
      };
    }
    var createMissing = document.getElementById("ev-create-missing");
    if (createMissing) {
      createMissing.onclick = function () {
        bridge.setSchema(ev.schema_ref, "type: object\nproperties: {}\n");
      };
    }

    if (baseSchema) {
      mountEditor(document.getElementById("ev-base"), {value: baseSchema, readOnly: true});
    }
    if (setting) { mountBusiness(ev, setting); }
  }

  function mountBusiness(ev, setting) {
    var yamlEl = document.getElementById("ev-yaml");
    var yamlError = document.getElementById("ev-yaml-error");
    var clashEl = document.getElementById("ev-clash");
    var parsed = Editor.parseYaml(setting.yaml);
    var value = parsed.value || {type: "object", properties: {}};
    yamlEl.value = setting.yaml;
    if (parsed.error) {
      yamlError.hidden = false;
      yamlError.textContent = "YAML illisible : " + parsed.error;
    }

    function showClash(schema) {
      var clash = reservedClash(schema);
      clashEl.hidden = !clash.length;
      clashEl.textContent = clash.length
        ? clash.join(", ") + " : champ(s) du socle, déjà présent(s) sur tout " +
          "événement — à retirer du schéma métier (refusé à l'analyse)."
        : "";
    }
    showClash(value);

    var instance = mountEditor(document.getElementById("ev-business"), {
      value: value,
      onChange: function (schema) {
        var text = Editor.stringifyYaml(schema);
        instance.update({value: schema});
        yamlEl.value = text;
        yamlError.hidden = true;
        showClash(schema);
        bridge.setSchema(setting.name, text);
      },
    });

    yamlEl.oninput = function () {
      var next = Editor.parseYaml(yamlEl.value);
      if (next.error) {
        yamlError.hidden = false;
        yamlError.textContent = "YAML illisible : " + next.error;
        return;
      }
      yamlError.hidden = true;
      instance.update({value: next.value});
      showClash(next.value);
      bridge.setSchema(setting.name, yamlEl.value);
    };
  }

  function render() {
    if (!visible) { return; }
    renderList();
    renderDetail();
  }

  // ------------------------------------------------------------------
  // Branchements
  // ------------------------------------------------------------------

  if (!Editor) {
    // Bundle absent (installation incomplète) : on le dit plutôt que de
    // laisser une vue vide.
    detailEl.innerHTML = "<p class='notice ko'>Éditeur de schémas indisponible " +
      "(static/vendor/schema-editor.js).</p>";
    return;
  }

  fetch("/api/base-event-schema")
    .then(function (r) { return r.json(); })
    .then(function (schema) { baseSchema = schema; shownKey = ""; render(); })
    .catch(function () { /* le socle manquera ; le reste de la vue fonctionne */ });

  bridge.onAnalyze(function () { render(); });

  document.addEventListener("uw:view", function (e) {
    visible = e.detail === "events";
    if (visible) { shownKey = ""; render(); }
  });

  window.PlaygroundEvents = {
    select: function (name) { selected = name; shownKey = ""; render(); },
  };
})();
