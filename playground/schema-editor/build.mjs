// Construit static/vendor/schema-editor.{js,css} pour le playground.
//
// Le résultat est COMMITÉ (comme CodeMirror et X6) : la distribution PyPI
// urban-workflow-playground et l'image Docker n'ont ainsi besoin ni de Node
// ni du réseau npm. Relancer après toute mise à jour des dépendances :
//   cd playground/schema-editor && npm ci && npm run build
import { build } from "esbuild";

const out = new URL("../urban_workflow_playground/static/vendor/", import.meta.url);

await build({
  entryPoints: [new URL("./src/main.jsx", import.meta.url).pathname],
  bundle: true,
  format: "iife",
  minify: true,
  target: ["es2020"],
  // React en mode production : sans ce define, le bundle embarque les
  // vérifications de développement (x3 en taille, avertissements console).
  define: { "process.env.NODE_ENV": '"production"' },
  jsx: "automatic",
  // Sortie ASCII : même précaution que pour x6.min.js (des caractères non
  // ASCII bruts dans un .js vendorisé ont déjà cassé l'analyse côté client).
  charset: "ascii",
  legalComments: "eof",
  outfile: new URL("schema-editor.js", out).pathname,
  logLevel: "info",
});
