#!/usr/bin/env bash
# Déploie le playground urban-workflow (IHM de test) sur une machine de test,
# depuis la branche dev.
#
# Usage (depuis le clone du dépôt sur la machine) :
#   ./dev-deploy.sh                       # déploiement normal
#   ./dev-deploy.sh --no-detach           # CI / débogage : sans le filet anti-raccrochage
#   ./dev-deploy.sh --exposer-seulement   # stack déjà en place : santé + déclaration seules
#   ./dev-deploy.sh --bootstrap-deploy-key [--force]
#                                         # dépôt devenu privé : clé de déploiement
#
# Première installation sur une machine :
#   git clone -b dev https://github.com/gaelgael5/urban-workflow.git ~/urban-workflow
#   cd ~/urban-workflow && ./dev-deploy.sh
# Port déjà pris sur une VM partagée : PLAYGROUND_PORT=8797 ./dev-deploy.sh
# (persisté dans .env au premier passage, relu ensuite).
#
# Déclaration à l'annuaire du portail (après la santé) : active seulement si
# PORTAL_TOKEN est dans l'environnement — code TOTP « <login>:<code> » obtenu
# par l'outil MCP `totp_code`, valable 30 s, jamais écrit dans .env ni dans le
# journal. Il expire bien avant la fin d'un build : on enchaîne en pratique
# ./dev-deploy.sh, puis un code frais et ./dev-deploy.sh --exposer-seulement.
#
# Prérequis : git, docker (+ plugin compose v2), curl, et l'accès réseau au
# dépôt GitHub — le script se met à jour depuis origin/dev avant tout ; il
# n'existe pas de mode « déployer ce qui est déjà là ».
#
# Pas de base de données dans cette stack (moteur en mémoire) : aucune
# migration à jouer, donc pas d'étape de schéma.
set -euo pipefail

BRANCH="dev"
SERVICE="playground"
STEPS=9
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$REPO_DIR/deploy-logs"
PRUNE_STAMP="$LOG_DIR/.last-prune"
DEPLOY_KEY="$HOME/.ssh/urban_workflow_deploy"
cd "$REPO_DIR"

DETACH=1
EXPOSE_ONLY=0
BOOTSTRAP_KEY=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --no-detach) DETACH=0 ;;
    --exposer-seulement) EXPOSE_ONLY=1 ;;
    --bootstrap-deploy-key) BOOTSTRAP_KEY=1 ;;
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,28p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done
[[ "$FORCE" == 0 || "$BOOTSTRAP_KEY" == 1 ]] \
  || { echo "--force ne s'utilise qu'avec --bootstrap-deploy-key" >&2; exit 2; }

# --- 0. Survivre à la perte de la session -----------------------------------
# Le script arrête la stack : si le terminal tombe (mobile, session web) entre
# l'arrêt et la relance, SIGHUP le tuerait et laisserait la stack à terre. On
# ignore donc HUP et on journalise tout dans un fichier, avec `tee -p` qui
# continue d'écrire le fichier même quand le terminal a disparu.
mkdir -p "$LOG_DIR"
if [[ "$DETACH" == 1 && -z "${DEV_DEPLOY_LOGGING:-}" ]]; then
  export DEV_DEPLOY_LOGGING=1
  export DEV_DEPLOY_LOG="$LOG_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"
  trap '' HUP PIPE
  exec > >(tee -a -p "$DEV_DEPLOY_LOG") 2>&1
  echo "Journal du déploiement : $DEV_DEPLOY_LOG"
fi

step() { echo; echo "=== [$1/$STEPS] $2"; }
die()  { echo "ERREUR : $*" >&2; exit 1; }

# --- Mode bootstrap : clé de déploiement (dépôt privé) -----------------------
# Aujourd'hui le dépôt est public et se clone en HTTPS anonyme. S'il passe en
# privé, la récupération échouera soudain sur une authentification : ce mode
# génère une clé SUR l'hôte (la clé privée ne transite par aucun canal ni
# copier-coller), bascule origin en SSH, affiche la clé publique EN DERNIER et
# attend qu'elle soit enregistrée en lecture seule dans les Deploy keys.
# Idempotent : relancé, il réaffiche la clé existante ; --force régénère.
if [[ "$BOOTSTRAP_KEY" == 1 ]]; then
  command -v ssh-keygen >/dev/null || die "ssh-keygen introuvable — sudo apt-get install -y openssh-client"
  mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
  if [[ "$FORCE" == 1 ]]; then rm -f "$DEPLOY_KEY" "$DEPLOY_KEY.pub"; fi
  if [[ ! -f "$DEPLOY_KEY" ]]; then
    ssh-keygen -q -t ed25519 -N "" -C "urban-workflow-deploy@$(hostname)" -f "$DEPLOY_KEY"
  fi
  # Alias SSH dédié plutôt que Host github.com : on ne détourne pas les clones
  # des autres projets de la machine vers cette clé.
  if ! grep -q "^Host github-urban-workflow$" "$HOME/.ssh/config" 2>/dev/null; then
    cat >> "$HOME/.ssh/config" <<EOF

Host github-urban-workflow
    HostName github.com
    User git
    IdentityFile $DEPLOY_KEY
    IdentitiesOnly yes
EOF
    chmod 600 "$HOME/.ssh/config"
  fi
  git remote set-url origin git@github-urban-workflow:gaelgael5/urban-workflow.git
  echo
  echo "Enregistre cette clé publique dans GitHub > gaelgael5/urban-workflow >"
  echo "Settings > Deploy keys (lecture seule, « Allow write access » décoché) :"
  echo
  cat "$DEPLOY_KEY.pub"
  echo
  if [[ -t 0 ]]; then
    read -r -p "Entrée une fois la clé enregistrée pour poursuivre le déploiement… "
  else
    echo "Pas de terminal interactif : relance ./dev-deploy.sh une fois la clé enregistrée."
    exit 0
  fi
fi

# --- 1. Prérequis --------------------------------------------------------------
step 1 "Prérequis"
command -v git  >/dev/null || die "git introuvable — sudo apt-get install -y git"
command -v curl >/dev/null || die "curl introuvable — sudo apt-get install -y curl"
command -v docker >/dev/null || die "docker introuvable — https://docs.docker.com/engine/install/"
docker compose version >/dev/null 2>&1 \
  || die "plugin docker compose v2 introuvable — sudo apt-get install -y docker-compose-plugin"
docker info >/dev/null 2>&1 \
  || die "le démon docker ne répond pas, ou droits insuffisants — sudo usermod -aG docker \$USER (puis reconnexion)"
echo "OK : compose $(docker compose version --short) / $(git --version)"

# --- 2. Mise à jour depuis le dépôt, puis ré-exécution ---------------------------
# Sans ré-exécution, on déploierait le code neuf avec un script, un compose et un
# Dockerfile périmés. DEV_DEPLOY_REEXEC évite de boucler.
step 2 "Mise à jour depuis origin/$BRANCH"
if [[ -z "${DEV_DEPLOY_REEXEC:-}" ]]; then
  [[ -z "$(git status --porcelain --untracked-files=no)" ]] \
    || die "modifications locales sur la machine (git status) : aucune retouche à la main n'est admise, tout passe par le dépôt"
  before="$(git rev-parse HEAD)"
  git fetch --prune origin "$BRANCH" \
    || die "récupération impossible depuis origin — dépôt devenu privé ? ./dev-deploy.sh --bootstrap-deploy-key"
  git checkout -q "$BRANCH"
  git merge --ff-only -q "origin/$BRANCH" \
    || die "la branche locale a divergé d'origin/$BRANCH — reclone la branche $BRANCH"
  after="$(git rev-parse HEAD)"
  if [[ "$before" != "$after" ]]; then
    echo "Mis à jour ${before:0:7} -> ${after:0:7} : relance avec la version récupérée"
    export DEV_DEPLOY_REEXEC=1
    # Le mode bootstrap est déjà joué : on ne le repasse pas à la version fraîche.
    reexec_args=()
    for a in "$@"; do
      [[ "$a" == --bootstrap-deploy-key || "$a" == --force ]] || reexec_args+=("$a")
    done
    exec "$REPO_DIR/dev-deploy.sh" "${reexec_args[@]}"
  fi
fi
echo "Déploiement de $(git log -1 --format='%h %s')"

# --- 3. Configuration : compléter .env sans écraser l'existant --------------------
step 3 "Configuration (.env)"
touch .env
env_get() { grep "^$1=" .env | tail -1 | cut -d= -f2-; }
# Une valeur absente de .env est prise dans l'environnement si elle y est
# (premier déploiement sur une VM partagée), sinon le défaut ; elle est alors
# persistée, et les passages suivants la relisent sans la régénérer.
env_default() { grep -q "^$1=" .env || echo "$1=${!1:-$2}" >> .env; }
# Isolation sur VM partagée : nom de stack et port paramétrés, jamais en dur.
env_default COMPOSE_PROJECT_NAME urban-workflow
env_default PLAYGROUND_PORT 8777
# Cible de la déclaration à l'annuaire (le jeton, lui, n'est jamais ici).
env_default EXPOSE_PORTAL_URL https://dev.yoops.org
env_default EXPOSE_WORKSPACE urban-workflow
PORT="$(env_get PLAYGROUND_PORT)"
STACK="$(env_get COMPOSE_PROJECT_NAME)"
export COMPOSE_PROJECT_NAME="$STACK"
echo "Stack : $STACK — port publié : $PORT"

if [[ "$EXPOSE_ONLY" == 1 ]]; then
  echo "--exposer-seulement : étapes 4 à 6 sautées (stack supposée en place)"
else

# --- 4. Construction --------------------------------------------------------------
# Construire ici, depuis la copie fraîche du dépôt, est la vraie validation de
# l'image (un fichier non versionné manquerait ici, pas en local) : jamais
# d'image réutilisée d'ailleurs.
step 4 "Construction de l'image"
docker compose build --pull

# --- 5. Arrêt (orphelins compris) puis contrôle du port ---------------------------
# Le port se sonde APRÈS l'arrêt : avant, on prendrait notre propre conteneur
# pour un conflit.
step 5 "Arrêt de la stack et contrôle du port"
docker compose down --remove-orphans
if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then
  die "le port $PORT est occupé par un autre service après l'arrêt de la stack — change PLAYGROUND_PORT dans .env (diagnostic : sudo ss -ltnp 'sport = :$PORT')"
fi
echo "Port $PORT libre"

# --- 6. Lancement, attente d'un conteneur réellement en marche --------------------
step 6 "Lancement"
docker compose up -d
state=""
for _ in $(seq 1 30); do
  state="$(docker compose ps --format '{{.State}}' "$SERVICE" 2>/dev/null || true)"
  [[ "$state" == "running" ]] && break
  sleep 2
done
[[ "$state" == "running" ]] \
  || die "le conteneur $SERVICE n'est pas en marche (état : ${state:-absent}) — docker compose logs $SERVICE"
echo "Conteneur $SERVICE en marche"
fi

# --- 7. Contrôle de santé, plafonné, sur le port réellement publié ----------------
# On vérifie le CONTENU de la réponse (et pas seulement un 200) : un autre
# service sur ce port répondrait aussi.
step 7 "Contrôle de santé (http://127.0.0.1:$PORT/healthz)"
ok=0
for _ in $(seq 1 45); do
  if curl -fs --max-time 2 "http://127.0.0.1:$PORT/healthz" | grep -q '"ok"'; then ok=1; break; fi
  sleep 2
done
[[ "$ok" == 1 ]] || die "pas de réponse saine en 90 s — docker compose logs --tail=100 $SERVICE"
echo "Service sain : http://$(hostname -f 2>/dev/null || hostname):$PORT/"

# --- 8. Déclaration à l'annuaire du portail (best-effort) ---------------------------
# Après la santé : on ne publie pas une stack qui ne répond pas. Nom du service =
# nom de la stack. Voie --me : enregistrée sous le workspace de l'appelant
# authentifié par son TOTP.
step 8 "Déclaration à l'annuaire"
if [[ -n "${PORTAL_TOKEN:-}" ]]; then
  # Le portail n'accepte qu'une IP du mesh (100.64.0.0/10) ou d'une machine
  # qu'il connaît — l'IP LAN est refusée (422) : on préfère l'adresse mesh.
  ips="$(hostname -I 2>/dev/null)"
  TARGET_HOST="$(tr ' ' '\n' <<<"$ips" | grep -E '^100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.' | head -1 || true)"
  [[ -n "$TARGET_HOST" ]] || TARGET_HOST="$(awk '{print $1}' <<<"$ips")"
  bash "$REPO_DIR/scripts/declarer-exposition.sh" --me \
    --portal "$(env_get EXPOSE_PORTAL_URL)" \
    --workspace "$(env_get EXPOSE_WORKSPACE)" \
    --service "$STACK" \
    --target-host "$TARGET_HOST" \
    --target-port "$PORT" \
    --host "$(hostname)"
else
  echo "PORTAL_TOKEN absent : pas de déclaration (relancer avec un code TOTP et --exposer-seulement)"
fi

# --- 9. Purge disque hebdomadaire (ne fait jamais échouer le déploiement) ---------
# Chaque build laisse des couches détaggées que rien ne récupère. Portée limitée
# au cache de build et aux images détaggées ; jamais les volumes ni les images de
# base. Témoin horodaté : au plus une fois par semaine (purger à chaque passage
# coûte des minutes, et une purge coûteuse finit par être désactivée).
step 9 "Purge disque (hebdomadaire)"
if [[ "$EXPOSE_ONLY" == 1 ]]; then
  echo "--exposer-seulement : pas de purge"
elif [[ ! -f "$PRUNE_STAMP" ]] || [[ -n "$(find "$PRUNE_STAMP" -mtime +6 2>/dev/null)" ]]; then
  {
    echo "Avant : $(df -h / | awk 'NR==2{print $4}') libres"
    docker builder prune -f --filter until=168h
    docker image prune -f
    echo "Après : $(df -h / | awk 'NR==2{print $4}') libres"
    touch "$PRUNE_STAMP"
  } || echo "AVERTISSEMENT : purge en échec (déploiement non affecté)"
else
  echo "Dernière purge il y a moins d'une semaine : rien à faire"
fi

echo
echo "Déploiement terminé."
