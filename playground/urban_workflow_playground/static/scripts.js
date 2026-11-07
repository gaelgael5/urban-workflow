/* Vue « Scripts » : méthodes des règles référencées par
 * « DEFINE RULE … AS @nom » (décision du 2026-11-07 : pas de code dans le
 * document de workflow).
 *
 * Liste = scripts référencés par le workflow (règles, actions) + scripts
 * écrits mais inutilisés ; détail = qui l'utilise (signatures) et un
 * éditeur CodeMirror du langage « expression », avec complétion
 * (paramètres des règles qui le référencent, constantes, fonctions,
 * chemins @) et erreurs positionnées DANS le script (champ « script » des
 * erreurs de /api/analyze).
 *
 * Source de vérité : les scripts du playground (localStorage, pont
 * window.PlaygroundBridge) et le script du workflow pour les références.
 */
(function () {
  "use strict";

  var bridge = window.PlaygroundBridge;
  var listEl = document.getElementById("sc-list");
  var detailEl = document.getElementById("sc-detail");

  var selected = null;     // nom du script affiché
  var visible = false;
  var lastErrors = [];
  var cm = null;           // éditeur du script affiché
  var cmName = null;       // script chargé dans cm
  var marks = [];
  var saveTimer = null;
  var pendingCursor = null;

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function reEscape(text) { return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function findScript(name) {
    var found = null;
    bridge.getScripts().forEach(function (s) { if (s.name === name) { found = s; } });
    return found;
  }

  function signature(d) {
    return d.name + "(" + (d.params || []).map(function (p) {
      return p.type + " " + p.name;
    }).join(", ") + ")";
  }

  /** [{name, users: [{kind, decl}], written}] — référencés d'abord (ordre
   * des déclarations), puis écrits mais inutilisés. */
  function entries() {
    var symbols = bridge.getSymbols();
    var byName = {}, order = [];
    function entry(name) {
      if (!byName[name]) { byName[name] = {name: name, users: []}; order.push(name); }
      return byName[name];
    }
    (symbols.rules || []).forEach(function (d) {
      if (d.script) { entry(d.script).users.push({kind: "rule", decl: d}); }
    });
    (symbols.actions || []).forEach(function (d) {
      if (d.script) { entry(d.script).users.push({kind: "action", decl: d}); }
    });
    bridge.getScripts().forEach(function (s) { entry(s.name); });
    return order.map(function (name) {
      var e = byName[name];
      e.written = !!findScript(name);
      e.errors = lastErrors.filter(function (err) { return err.script === name; });
      return e;
    });
  }

  function rulesWithoutScript() {
    return (bridge.getSymbols().rules || []).filter(function (d) { return !d.script; });
  }

  /** MontantEleve → montant_eleve (nom de script proposé). */
  function scriptNameFor(ruleName) {
    var base = ruleName.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase();
    var name = base, index = 2;
    while (findScript(name)) { name = base + "_" + index++; }
    return name;
  }

  // ------------------------------------------------------------------
  // Modifications du workflow
  // ------------------------------------------------------------------

  /** Ajoute « AS @script » à DEFINE RULE nom (…) 'libellé'?. */
  function addScriptClause(ruleName, scriptName) {
    var script = bridge.getScript();
    var re = new RegExp("\\bDEFINE\\s+RULE\\s+" + reEscape(ruleName) +
                        "\\s*\\([^)]*\\)(\\s*'(?:[^']|'')*')?", "i");
    var match = re.exec(script);
    if (!match) { return false; }
    bridge.insertText(match.index + match[0].length, " AS @" + scriptName);
    return true;
  }

  function newSource(users) {
    var rule = users.filter(function (u) { return u.kind === "rule"; })[0];
    var head = rule ? "-- " + (rule.decl.comment || rule.decl.name) + "\n" : "";
    var params = rule ? (rule.decl.params || []).map(function (p) { return p.name; }) : [];
    return head + (params.length
      ? "-- paramètres : " + params.join(", ") + "\nTRUE\n"
      : "TRUE\n");
  }

  // ------------------------------------------------------------------
  // Liste
  // ------------------------------------------------------------------

  function renderList(list) {
    listEl.innerHTML = "";
    if (!list.length) {
      listEl.innerHTML = "<p class='hint-text'>Aucun script.</p>";
    }
    list.forEach(function (e) {
      var item = document.createElement("button");
      item.type = "button";
      item.className = "ev-item" + (e.name === selected ? " active" : "");
      var badges = "";
      if (!e.written) { badges += "<span class='ev-badge warn'>à écrire</span>"; }
      if (e.errors.length) { badges += "<span class='ev-badge ko'>erreur</span>"; }
      if (!e.users.length) { badges += "<span class='ev-badge muted'>inutilisé</span>"; }
      e.users.forEach(function (u) {
        badges += "<span class='ev-badge" + (u.kind === "action" ? " muted" : "") + "'>" +
          esc(u.decl.name) + "</span>";
      });
      item.innerHTML = "<span class='ev-name'>@" + esc(e.name) + "</span>" +
        "<span class='ev-badges'>" + badges + "</span>";
      item.onclick = function () { selected = e.name; render(); };
      listEl.appendChild(item);
    });

    var free = rulesWithoutScript();
    if (free.length) {
      var title = document.createElement("p");
      title.className = "hint-text sc-free-title";
      title.textContent = "Règles sans script (fonction de code ou simulée) :";
      listEl.appendChild(title);
      free.forEach(function (d) {
        var row = document.createElement("div");
        row.className = "sc-free";
        row.innerHTML = "<code>" + esc(d.name) + "</code>" +
          "<button type='button' title='Ajouter AS @… à la déclaration et créer le script'>" +
          "écrire en script</button>";
        row.querySelector("button").onclick = function () {
          var name = scriptNameFor(d.name);
          if (!addScriptClause(d.name, name)) { return; }
          bridge.setScriptSource(name, newSource([{kind: "rule", decl: d}]));
          selected = name;
          render();
        };
        listEl.appendChild(row);
      });
    }
  }

  // ------------------------------------------------------------------
  // Détail
  // ------------------------------------------------------------------

  function dropEditor() {
    cm = null; cmName = null; marks = [];
  }

  function render() {
    if (!visible) { return; }
    var list = entries();
    if (!selected || !list.some(function (e) { return e.name === selected; })) {
      selected = list.length ? list[0].name : null;
    }
    renderList(list);
    var e = list.filter(function (x) { return x.name === selected; })[0];
    if (!e) {
      dropEditor();
      detailEl.innerHTML = "<p class='hint-text'>Une règle référence sa méthode par " +
        "<code>DEFINE RULE R (DECIMAL seuil) 'libellé' AS @nom;</code> : le script " +
        "<code>@nom</code> s'écrit ici, hors du document de workflow. « écrire en " +
        "script » (à gauche) le fait pour une règle existante.</p>";
      return;
    }
    renderDetail(e);
  }

  function usersHtml(e) {
    if (!e.users.length) {
      return "<p class='notice'>Aucune déclaration ne référence ce script.</p>";
    }
    return "<p class='notice'>Utilisé par : " + e.users.map(function (u) {
      return "<code>" + esc(signature(u.decl)) + "</code> (" +
        (u.kind === "rule" ? "règle" : "action — exécution des méthodes d'action à venir") + ")";
    }).join(", ") + "</p>";
  }

  function renderDetail(e) {
    var script = findScript(e.name);
    if (cm && cmName === e.name && script) {
      // Même script : on garde l'éditeur (curseur, historique) et on ne
      // met à jour que l'entourage.
      detailEl.querySelector("[data-ref='users']").innerHTML = usersHtml(e);
      showErrors(e.errors);
      return;
    }
    dropEditor();
    detailEl.innerHTML =
      "<div class='ev-head'><h3>@" + esc(e.name) + "</h3>" +
      "<span class='ev-badge'>expression</span></div>" +
      "<div data-ref='users'>" + usersHtml(e) + "</div>" +
      (script
        ? "<div class='sc-editor' data-ref='editor'></div>" +
          "<div class='diagnostics' data-ref='diags'></div>" +
          "<p class='hint-text'>Une expression, sur autant de lignes que voulu " +
          "(commentaires <code>--</code> et <code>/* */</code>). Paramètres des " +
          "règles qui le référencent, constantes, <code>@IncomingEvent.…</code>, " +
          "<code>@state.…</code>, fonctions — <kbd>Ctrl</kbd>+<kbd>Espace</kbd>.</p>" +
          "<button type='button' data-ref='remove'>Supprimer le script</button>"
        : "<p class='notice ko'>Ce script est référencé mais pas encore écrit.</p>" +
          "<button type='button' class='primary' data-ref='create'>Créer le script</button>");

    if (!script) {
      detailEl.querySelector("[data-ref='create']").onclick = function () {
        bridge.setScriptSource(e.name, newSource(e.users));
        render();
      };
      return;
    }
    detailEl.querySelector("[data-ref='remove']").onclick = function () {
      bridge.removeScript(e.name);
      dropEditor();
      render();
    };
    cm = CodeMirror(detailEl.querySelector("[data-ref='editor']"), {
      value: script.source || "",
      mode: "workflow-dsl",
      lineNumbers: true,
      indentUnit: 4,
      extraKeys: {"Ctrl-Space": "autocomplete"},
      hintOptions: {hint: scriptHint, completeSingle: false},
    });
    cmName = e.name;
    cm.on("change", function () {
      clearTimeout(saveTimer);
      var name = cmName, editor = cm;
      saveTimer = setTimeout(function () {
        bridge.setScriptSource(name, editor.getValue());
      }, 450);
    });
    cm.on("inputRead", function (instance, change) {
      if (instance.state.completionActive) { return; }
      var token = instance.getTokenAt(instance.getCursor());
      if (token.type === "string" || token.type === "comment") { return; }
      if (/[\w@.\[]/.test(change.text[0])) {
        instance.showHint({hint: scriptHint, completeSingle: false});
      }
    });
    showErrors(e.errors);
    if (pendingCursor) {
      cm.setCursor(pendingCursor);
      pendingCursor = null;
    }
    setTimeout(function () { if (cm) { cm.refresh(); cm.focus(); } }, 0);
  }

  function showErrors(errors) {
    var diags = detailEl.querySelector("[data-ref='diags']");
    if (!cm || !diags) { return; }
    marks.forEach(function (m) { m.clear(); });
    marks = [];
    diags.innerHTML = "";
    errors.forEach(function (err) {
      var line = Math.max(0, (err.line || 1) - 1);
      var ch = Math.max(0, err.column || 0);
      var token = cm.getTokenAt(CodeMirror.Pos(line, ch + 1));
      var end = token && token.end > ch ? token.end : ch + 1;
      marks.push(cm.markText(CodeMirror.Pos(line, ch), CodeMirror.Pos(line, end), {
        className: "CodeMirror-lint-mark-error", title: err.message,
      }));
      var div = document.createElement("div");
      div.className = "diag";
      div.textContent = "ligne " + err.line + ":" + err.column + " — " + err.message;
      div.onclick = function () { cm.setCursor(CodeMirror.Pos(line, ch)); cm.focus(); };
      diags.appendChild(div);
    });
  }

  // ------------------------------------------------------------------
  // Complétion dans un script
  // ------------------------------------------------------------------

  function currentUsers() {
    var e = entries().filter(function (x) { return x.name === cmName; })[0];
    return e ? e.users : [];
  }

  /** Chemins proposés : un script ne connaît pas le bloc qui l'appellera,
   * on propose donc les propriétés de tous les objets (et le socle). */
  function pathItems(prefix, byName, base) {
    var seen = {}, items = [];
    function add(p, owner) {
      if (seen[p.path]) { return; }
      seen[p.path] = true;
      items.push({text: prefix + p.path,
                  displayText: prefix + p.path + "  ·  " + p.type + "  (" + owner + ")"});
    }
    Object.keys(byName || {}).forEach(function (owner) {
      (byName[owner] || []).forEach(function (p) { add(p, owner); });
    });
    (base || []).forEach(function (p) { add(p, "socle"); });
    return items;
  }

  function scriptHint(instance) {
    var symbols = bridge.getSymbols();
    var cursor = instance.getCursor();
    var token = instance.getTokenAt(cursor);
    if (token.type === "string" || token.type === "comment") { return null; }
    var lineText = instance.getLine(cursor.line).slice(0, cursor.ch);

    var path = /@(IncomingEvent|state)\.[\w.\[\]']*$/i.exec(lineText);
    if (path) {
      var items = path[1].toLowerCase() === "state"
        ? pathItems("@state.", symbols.state_properties, symbols.base_state_paths)
        : pathItems("@IncomingEvent.", symbols.event_properties, symbols.base_paths);
      var typedPath = path[0].toLowerCase();
      return {
        list: items.filter(function (i) { return i.text.toLowerCase().indexOf(typedPath) === 0; }),
        from: CodeMirror.Pos(cursor.line, cursor.ch - path[0].length),
        to: cursor,
      };
    }

    var match = /[@\w.]*$/.exec(lineText);
    var typed = (match ? match[0] : "").toLowerCase();
    var candidates = [], seen = {};
    currentUsers().forEach(function (u) {
      (u.decl.params || []).forEach(function (p) {
        if (seen[p.name]) { return; }
        seen[p.name] = true;
        candidates.push({text: p.name,
                         displayText: p.name + "  ·  paramètre " + p.type + " de " + u.decl.name});
      });
    });
    (symbols.constants || []).forEach(function (c) {
      var name = c.name || c;
      candidates.push({text: name, displayText: name + "  ·  constante"});
    });
    bridge.ruleFunctions.forEach(function (f) {
      candidates.push({text: f.name + "(" + (f.args ? "" : ")"),
                       displayText: f.name + "(" + f.args + ")  ·  fonction"});
    });
    ["@IncomingEvent.", "@state."].forEach(function (p) {
      candidates.push({text: p, displayText: p});
    });
    ["AND ", "OR ", "NOT ", "IN (", "IS NULL", "IS NOT NULL", "TRUE", "FALSE", "NULL"]
      .forEach(function (k) { candidates.push({text: k, displayText: k.trim()}); });
    return {
      list: candidates.filter(function (i) {
        return !typed || i.text.toLowerCase().indexOf(typed) === 0;
      }),
      from: CodeMirror.Pos(cursor.line, cursor.ch - typed.length),
      to: cursor,
    };
  }

  // ------------------------------------------------------------------
  // Branchements
  // ------------------------------------------------------------------

  bridge.onAnalyze(function (data) {
    lastErrors = data.errors || [];
    render();
  });

  document.addEventListener("uw:view", function (event) {
    visible = event.detail === "scripts";
    if (visible) {
      dropEditor();   // conteneur peut-être détaché depuis : on remonte
      render();
    }
  });

  document.addEventListener("uw:open-script", function (event) {
    var detail = event.detail || {};
    selected = detail.script;
    pendingCursor = detail.line
      ? CodeMirror.Pos(Math.max(0, detail.line - 1), detail.column || 0)
      : null;
    dropEditor();
    document.getElementById("view-scripts").click();
  });

  // Poignée de tests UI (non documentée, API non garantie).
  window.PlaygroundScripts = {
    select: function (name) { selected = name; dropEditor(); render(); },
    editor: function () { return cm; },
  };
})();
