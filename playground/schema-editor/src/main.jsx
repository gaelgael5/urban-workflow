// Point d'entrée du bundle : expose window.UWSchemaEditor au playground, qui
// est en JavaScript sans étape de build (CodeMirror et X6 y sont vendorisés de
// la même façon). Le composant est celui du portail Miles
// (portail/frontend/src/dataModels/SchemaEditor.tsx) : SchemaFieldsEditor de
// jsonjoy-builder, même fork vendu, même locale fr.
import { createElement as h } from "react";
import { createRoot } from "react-dom/client";
import { SchemaFieldsEditor, fr } from "jsonjoy-builder";
import { YAMLParseError, parse, stringify } from "yaml";
import "jsonjoy-builder/styles.css";

/**
 * Monte un éditeur contrôlé dans `el` : l'appelant garde le schéma, reçoit
 * chaque modification par onChange et repousse la valeur par update().
 * Une instance readOnly sert à montrer le socle commun des événements :
 * le fork ne sait pas verrouiller un champ isolé, d'où deux instances.
 */
function mount(el, props) {
  const root = createRoot(el);
  let current = { ...props };
  const render = () =>
    root.render(
      h(SchemaFieldsEditor, {
        value: current.value,
        onChange: current.onChange,
        readOnly: Boolean(current.readOnly),
        // Pas de focus automatique : le montage suit un clic dans la liste
        // des événements, voler le focus casserait la navigation clavier.
        autoFocus: false,
        locale: fr,
        messages: current.messages,
      }),
    );
  render();
  return {
    update(next) {
      current = { ...current, ...next };
      render();
    },
    unmount() {
      root.unmount();
    },
  };
}

/** Le YAML lu en objet, ou { error } avec ligne/colonne (même message que Miles). */
function parseYaml(text) {
  try {
    const value = parse(text, { uniqueKeys: true });
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      return { error: "le document n'est pas un objet" };
    }
    return { value };
  } catch (error) {
    if (error instanceof YAMLParseError) {
      const at = error.linePos?.[0];
      const where = at ? ` (ligne ${at.line}, colonne ${at.col})` : "";
      return { error: `${error.message.split("\n")[0] ?? ""}${where}` };
    }
    throw error;
  }
}

function stringifyYaml(value) {
  return stringify(value, { lineWidth: 0 });
}

window.UWSchemaEditor = { mount, parseYaml, stringifyYaml };
