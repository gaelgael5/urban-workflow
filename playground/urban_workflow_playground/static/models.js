/* Vues « Événements » et « États » : listent les objets du script et
 * éditent leur structure avec l'éditeur visuel de schémas du portail Miles
 * (window.UWSchemaEditor, bundle vendor/schema-editor.js).
 *
 * Un objet = son socle commun (BASE_EVENT_SCHEMA / BASE_STATE_SCHEMA, servi
 * par le serveur, NON modifiable) + son schéma métier optionnel
 * (DEFINE EVENT|STATE … AS @schema, YAML du panneau Paramétrage). Le fork
 * de l'éditeur ne verrouille pas un champ isolé : le socle est donc une
 * seconde instance en lecture seule, au-dessus de l'instance éditable.
 *
 * Un seul composant, deux paramétrages (OBJECT_KINDS) : les deux vues
 * doivent se comporter à l'identique, une copie divergerait.
 *
 * Source de vérité inchangée : le script (déclarations) et les schémas du
 * panneau (YAML). Ces vues ne font que les modifier par le pont
 * window.PlaygroundBridge ; elles se redessinent à chaque analyse.
 */
(function () {
  "use strict";

  var bridge = window.PlaygroundBridge;
  var Editor = window.UWSchemaEditor;

  var OBJECT_KINDS = {
    events: {
      keyword: "EVENT",
      details: "event_details",
      fallbackNames: "events",
      baseUrl: "/api/base-event-schema",
      listId: "ev-list",
      detailId: "ev-detail",
      empty: "Aucun événement dans le script.",
      baseTitle: "socle commun à tout événement — non modifiables",
      canDeclare: true,
      showUnique: true,
      exportName: "PlaygroundEvents",
    },
    states: {
      keyword: "STATE",
      details: "state_details",
      fallbackNames: "states",
      baseUrl: "/api/base-state-schema",
      listId: "st-list",
      detailId: "st-detail",
      empty: "Aucun état dans le script.",
      baseTitle: "socle de toute instance d'état (posé au SWITCH) — non modifiables",
      canDeclare: false,
      showUnique: false,
      exportName: "PlaygroundStates",
    },
  };

  if (!Editor) {
    // Bundle absent (installation incomplète) : on le dit plutôt que de
    // laisser des vues vides.
    Object.keys(OBJECT_KINDS).forEach(function (view) {
      document.getElementById(OBJECT_KINDS[view].detailId).innerHTML =
        "<p class='notice ko'>Éditeur de schémas indisponible " +
        "(static/vendor/schema-editor.js).</p>";
    });
    return;
  }

  Object.keys(OBJECT_KINDS).forEach(function (view) {
    createModelView(view, OBJECT_KINDS[view]);
  });

  function createModelView(viewName, kind) {
  var listEl = document.getElementById(kind.listId);
  var detailEl = document.getElementById(kind.detailId);
  // Éléments du détail repérés par data-ref DANS cette vue : les deux vues
  // coexistent dans la page, des id fixes se télescoperaient.
  function ref(name) { return detailEl.querySelector("[data-ref='" + name + "']"); }

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
    if (symbols[kind.details] && symbols[kind.details].length) {
      return symbols[kind.details].map(function (d) {
        // Un état est toujours déclaré (DEFINE STATE) ; seuls les
        // événements peuvent n'être qu'utilisés.
        return d.declared === undefined ? Object.assign({declared: true}, d) : d;
      });
    }
    // Script qui ne compile pas : repli sur les noms trouvés par regex, sans
    // détail (la liste reste utilisable, l'édition attend un script valide).
    return (symbols[kind.fallbackNames] || [])
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

  /** Ajoute « AS @schema » à la déclaration de l'objet. */
  function addSchemaClause(eventName, schemaName) {
    var script = bridge.getScript();
    // DEFINE EVENT|STATE nom 'libellé'? — AS se place juste après
    // (grammaire : key comment? (AS …)? …).
    var re = new RegExp("\\bDEFINE\\s+" + kind.keyword + "\\s+" + reEscape(eventName) +
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
      listEl.innerHTML = "<p class='hint-text'>" + kind.empty + "</p>";
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
      if (kind.showUnique && ev.unique && ev.unique.length) {
        badges += "<span class='ev-badge'>UNIQUE</span>";
      }
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
        "en éditer la structure.</p>";
    } else if (kind.canDeclare && !ev.declared) {
      html += "<p class='notice'>Événement utilisé mais pas déclaré par " +
        "<code>DEFINE EVENT</code>. <button type='button' data-ref='declare'>" +
        "Déclarer dans le script</button></p>";
    }

    html += "<h4 class='section-title'>Champs de base " +
      "<small>" + kind.baseTitle + "</small></h4>" +
      "<div data-ref='base' class='ev-editor locked'></div>";

    html += "<h4 class='section-title'>Champs métier";
    if (ev.schema_ref) { html += " <small>@" + esc(ev.schema_ref) + "</small>"; }
    html += "</h4>";
    if (!ev.schema_ref) {
      html += "<p class='hint-text'>Aucun schéma métier : seul le socle est " +
        "validé.</p>" + (ev.declared && !ev.partial
          ? "<button type='button' data-ref='create' class='primary'>Créer le schéma " +
            "métier</button>" : "");
    } else if (!setting) {
      html += "<p class='notice'>Le script référence <code>@" + esc(ev.schema_ref) +
        "</code> mais ce schéma n'existe pas encore. <button type='button' " +
        "data-ref='create-missing'>Créer @" + esc(ev.schema_ref) + "</button></p>";
    } else {
      html += "<div data-ref='clash' class='notice ko' hidden></div>" +
        "<div data-ref='business' class='ev-editor'></div>" +
        "<details class='ev-yaml'><summary>YAML du schéma</summary>" +
        "<textarea data-ref='yaml' spellcheck='false'></textarea>" +
        "<p data-ref='yaml-error' class='notice ko' hidden></p></details>";
    }
    detailEl.innerHTML = html;

    var declareBtn = ref("declare");
    if (declareBtn) { declareBtn.onclick = function () { declareEvent(ev.name); }; }

    var createBtn = ref("create");
    if (createBtn) {
      createBtn.onclick = function () {
        var name = schemaNameFor(ev.name);
        if (!findSchema(name)) {
          bridge.setSchema(name, "type: object\nproperties: {}\n");
        }
        if (!addSchemaClause(ev.name, name)) {
          createBtn.insertAdjacentHTML("afterend",
            "<p class='notice ko'>Déclaration introuvable dans le script.</p>");
        }
      };
    }
    var createMissing = ref("create-missing");
    if (createMissing) {
      createMissing.onclick = function () {
        bridge.setSchema(ev.schema_ref, "type: object\nproperties: {}\n");
      };
    }

    if (baseSchema) {
      mountEditor(ref("base"), {value: baseSchema, readOnly: true});
    }
    if (setting) { mountBusiness(ev, setting); }
  }

  function mountBusiness(ev, setting) {
    var yamlEl = ref("yaml");
    var yamlError = ref("yaml-error");
    var clashEl = ref("clash");
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
          "objet de ce type — à retirer du schéma métier (refusé à l'analyse)."
        : "";
    }
    showClash(value);

    var instance = mountEditor(ref("business"), {
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

  /** Nom proposé : schema_<Nom> ; si un événement l'emploie déjà (un état
   * et un événement de même nom), suffixe _state pour ne pas partager
   * par mégarde le schéma d'un autre type d'objet. */
  function schemaNameFor(name) {
    var candidate = "schema_" + name;
    if (kind.keyword !== "STATE") { return candidate; }
    var usedByEvent = (bridge.getSymbols().event_details || []).some(function (e) {
      return e.schema_ref === candidate;
    });
    return usedByEvent ? candidate + "_state" : candidate;
  }

  function render() {
    if (!visible) { return; }
    renderList();
    renderDetail();
  }

  // ------------------------------------------------------------------
  // Branchements
  // ------------------------------------------------------------------

  fetch(kind.baseUrl)
    .then(function (r) { return r.json(); })
    .then(function (schema) { baseSchema = schema; shownKey = ""; render(); })
    .catch(function () { /* le socle manquera ; le reste de la vue fonctionne */ });

  bridge.onAnalyze(function () { render(); });

  document.addEventListener("uw:view", function (e) {
    visible = e.detail === viewName;
    if (visible) { shownKey = ""; render(); }
  });

  window[kind.exportName] = {
    select: function (name) { selected = name; shownKey = ""; render(); },
  };
  }
})();
