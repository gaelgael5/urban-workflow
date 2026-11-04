# Ressources de test attribuées

Mémoire des ressources mises à disposition de ce workspace (`urban-workflow`) :
on ajoute à chaque attribution, on retire quand la ressource est reprise. Les
règles d'usage sont dans le standard des machines de test, pas ici.

## Machines de test

| Alias SSH | Nom d'hôte réel | Adresses | Usage | Depuis |
|---|---|---|---|---|
| `test1` | `host-test-37` | LAN 192.168.10.243 · mesh 100.74.9.236 | Playground urban-workflow : clone `~/urban-workflow` (branche `dev`), `./dev-deploy.sh`, port 8777 | 2026-11-04 |

Notes sur `test1` :

- Machine **partagée** avec d'autres stacks (miles, tutor, photoreader,
  urban-json sur 8095…) : ports 8080-8082, 8090, 8095, 8100, 8030, 3000 pris.
  8777 (port natif du playground) était libre au premier déploiement.
- **Alias recyclé** : les notes du workspace urban-json donnaient `test1` =
  `host-test-36` (2026-10-22). Toujours vérifier `hostname` avant d'agir.
- git 2.39.5 (bookworm) : HTTP/1.1 forcé vers github.com au niveau système
  (`/etc/git/http2-github.inc`), le clone HTTPS anonyme du dépôt public marche.
- Services standard : `browserless-chromium` (port 3000), collecteurs
  `devpod-alloy-agent` / `devpod-alloy-metrics`.
- Accès par rebond `devflow-jump` (bloc `test1` de `~/.ssh/config`).
