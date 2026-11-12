/* Exemples préchargés, et composant « examples » (liste déroulante qui
 * charge un exemple dans l'espace de travail).
 *
 *   UrbanWorkflow.mount("examples", el, {workspace})
 *   UrbanWorkflow.mount("examples", el, {workspace, examples: {mon: {label, script, …}}})
 */
(function () {
"use strict";

var UW = window.UrbanWorkflow;

UW.examples = {
  validation: {
    label: "Circuit de validation",
    script: `NAME ValidationAchat VERSION 1
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat')

DEFINE EVENT  DemandeSoumise     'une demande est déposée'
    AS @schema_DemandeSoumise UNIQUE (ExternalId, Montant);
DEFINE EVENT  PiecesFournies     'le demandeur complète son dossier';
DEFINE EVENT  ValidationAccordee 'un valideur approuve';
DEFINE EVENT  ValidationRefusee  'un valideur refuse';

DEFINE RULE   EstComplet (TEXT champs)         'les champs requis sont présents';
-- Règle implémentée par un script (vue Scripts) : évaluée par le moteur,
-- sans entrée dans le panneau Paramétrage.
DEFINE RULE   MontantInferieur (DECIMAL seuil) 'montant sous le seuil'
    AS @montant_inferieur;

DEFINE ACTION NotifierValideur (TEXT niveau, TEXT dossier)  'demande d''approbation';
DEFINE ACTION NotifierDemandeur (TEXT motif, TEXT dossier)  'information du demandeur';

DEFINE CONST  seuil_auto 500 'approbation automatique sous ce montant';

INITIALIZE WORKFLOW
    ON EVENT DemandeSoumise RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON EVENT DemandeSoumise
        WHEN NOT EstComplet(champs = 'Montant')
            EXECUTE NotifierDemandeur(motif = 'dossier incomplet',
                                      dossier = @Workflow.ExternalId)
            SWITCH Incomplete
        WHEN MontantInferieur(seuil = seuil_auto)
            SWITCH Approuvee
        EXECUTE NotifierValideur(niveau = 'standard',
                                 dossier = @Workflow.ExternalId)
            SWITCH EnValidation
;

DEFINE STATE Incomplete 'en attente de pièces'
    ON EVENT PiecesFournies
        WHEN EstComplet(champs = 'Montant')
            SWITCH EnValidation
;

DEFINE STATE EnValidation 'en attente d''un valideur'
    ON EVENT ValidationAccordee
        SWITCH Approuvee
    ON EVENT ValidationRefusee
        EXECUTE NotifierDemandeur(motif = @IncomingEvent.Motif,
                                  dossier = @Workflow.ExternalId)
        SWITCH Rejetee
    EXPIRE AFTER 3 DAY
        SWITCH Expiree
;

DEFINE STATE Approuvee 'demande approuvée'
    ON ENTER STATE
        STORE (Statut = 'approuvee')
;

DEFINE STATE Rejetee 'demande rejetée'
    ON ENTER STATE
        STORE (Statut = 'rejetee')
;

DEFINE STATE Expiree 'validation expirée sans réponse' ;
`,
    rules: [
      {name: "EstComplet", params: [{name: "champs", type: "TEXT"}], result: true},
    ],
    scripts: [
      {name: "montant_inferieur", source: "-- le montant de la demande est sous le seuil\n@IncomingEvent.Montant < seuil\n"},
    ],
    schemas: [
      {name: "schema_DemandeSoumise",
       yaml: "title: DemandeSoumise\n" +
             "type: object\n" +
             "properties:\n" +
             "  Type: {type: string}\n" +
             "  Montant: {type: number, minimum: 0}\n" +
             "  Canal: {type: string, enum: [web, mail]}\n" +
             "required: [Montant]\n"},
    ],
    events: [
      {Name: "DemandeSoumise", Uuid: "11111111-1111-4111-8111-111111111111",
       ExternalId: "DA-42", Type: "achat", Montant: 120, DedupKey: "cmd-42"},
      {Name: "DemandeSoumise", Uuid: "33333333-3333-4333-8333-333333333333",
       ExternalId: "DA-42", Type: "achat", Montant: 120, DedupKey: "cmd-42"},
      {Name: "ValidationAccordee", Uuid: "22222222-2222-4222-8222-222222222222",
       ExternalId: "DA-42", Type: "achat"},
    ],
  },

  regles: {
    label: "Règles et scripts",
    script: `NAME Reclamations VERSION 1
DESCRIPTION 'réclamations clients — règles implémentées par des scripts'

DEFINE EVENT  ReclamationDeposee 'une réclamation est déposée'
    AS @schema_Reclamation;
DEFINE EVENT  PieceAjoutee 'le client complète son dossier';
DEFINE EVENT  Relance      'le client relance';
DEFINE EVENT  Cloture      'le conseiller clôt le dossier';

-- Chaque règle référence son script (vue Scripts) : le workflow ne porte
-- pas de code. Évaluées par le moteur pendant la simulation.
DEFINE RULE   Urgente (DECIMAL plafond) 'réclamation urgente' AS @urgente;
DEFINE RULE   Complete (INTEGER minimum) 'assez de pièces jointes' AS @complete;
DEFINE RULE   SansMontant () 'montant non renseigné' AS @sans_montant;
DEFINE RULE   CanalNumerique () 'déposée en ligne' AS @canal_numerique;
-- @state dans le script : l'état du bloc qui APPELLE la règle (Incomplete).
DEFINE RULE   Ancienne (INTEGER jours) 'dans l''état depuis assez longtemps'
    AS @anciennete;

DEFINE ACTION Notifier (TEXT motif, TEXT dossier) 'information du client';

DEFINE CONST  plafond_urgence 5000 'au-delà : traitement prioritaire';
DEFINE CONST  pieces_min 2 'pièces jointes exigées';

INITIALIZE WORKFLOW
    ON EVENT ReclamationDeposee RECURSIVE SWITCH Tri

DEFINE STATE Tri 'aiguillage à la création'
    ON EVENT ReclamationDeposee
        WHEN Urgente(plafond = plafond_urgence)
            SWITCH Prioritaire
        WHEN SansMontant() OR NOT Complete(minimum = pieces_min)
            EXECUTE Notifier(motif = 'dossier incomplet',
                             dossier = @Workflow.ExternalId)
            SWITCH Incomplete
        WHEN CanalNumerique()
            SWITCH EnTraitement
        EXECUTE Notifier(motif = 'reçu par courrier',
                         dossier = @Workflow.ExternalId)
            SWITCH EnTraitement
;

DEFINE STATE Incomplete 'en attente de pièces'
    ON EVENT PieceAjoutee
        WHEN Complete(minimum = pieces_min)
            SWITCH EnTraitement
    ON EVENT Relance
        WHEN Ancienne(jours = '3')
            SWITCH Prioritaire
;

DEFINE STATE EnTraitement 'en cours de traitement'
    ON EVENT Cloture
        SWITCH Close
;

DEFINE STATE Prioritaire 'traitement prioritaire'
    ON EVENT Cloture
        SWITCH Close
;

DEFINE STATE Close 'réclamation close' ;
`,
    rules: [],
    scripts: [
      {name: "urgente", source: "-- urgent si le libellé le dit, ou si le montant majoré\n-- de 20 % dépasse le plafond\nCONTAINS(@IncomingEvent.Libelle, 'urgent')\n    OR @IncomingEvent.Montant * 1.2 > plafond\n"},
      {name: "complete", source: "LENGTH(@IncomingEvent.Pieces) >= minimum\n"},
      {name: "sans_montant", source: "@IncomingEvent.Montant IS NULL\n"},
      {name: "canal_numerique", source: "@IncomingEvent.Canal IN ('web', 'mobile')\n"},
      {name: "anciennete", source: "-- @state = l'état du bloc qui appelle la règle\nDAYS_BETWEEN(@state.CreationDate, NOW()) >= jours\n"},
    ],
    schemas: [
      {name: "schema_Reclamation",
       yaml: "title: Reclamation\n" +
             "type: object\n" +
             "properties:\n" +
             "  Libelle: {type: string}\n" +
             "  Montant: {type: number, minimum: 0}\n" +
             "  Canal: {type: string, enum: [web, mobile, courrier]}\n" +
             "  Pieces:\n" +
             "    type: array\n" +
             "    items: {type: string}\n"},
    ],
    events: [
      {Name: "ReclamationDeposee", Uuid: "a1111111-1111-4111-8111-111111111111",
       ExternalId: "R-1", Libelle: "colis urgent non livré", Montant: 80,
       Canal: "web", Pieces: ["photo.jpg"]},
      {Name: "ReclamationDeposee", Uuid: "a2222222-2222-4222-8222-222222222222",
       ExternalId: "R-2", Libelle: "article abîmé", Montant: 300,
       Canal: "mobile", Pieces: ["photo.jpg"]},
      {Name: "Relance", Uuid: "a3333333-3333-4333-8333-333333333333",
       ExternalId: "R-2"},
      {Name: "PieceAjoutee", Uuid: "a4444444-4444-4444-8444-444444444444",
       ExternalId: "R-2", Pieces: ["photo.jpg", "facture.pdf"]},
      {Name: "Cloture", Uuid: "a5555555-5555-4555-8555-555555555555",
       ExternalId: "R-2"},
    ],
  },

  etats: {
    label: "États et switch viable",
    script: `NAME Abonnement VERSION 1
DESCRIPTION 'abonnement — états modélisés, @state et switch viable'

DEFINE EVENT  Souscription 'le client souscrit' AS @schema_Souscription;
DEFINE EVENT  Paiement     'un paiement est reçu';
DEFINE EVENT  Resiliation  'le client résilie';

DEFINE RULE   OffreConnue () 'offre au catalogue' AS @offre_connue;
DEFINE RULE   PaiementAccepte () 'paiement accepté' AS @paiement_accepte;
DEFINE RULE   EngagementTermine (INTEGER mois) 'engagement écoulé'
    AS @engagement_termine;

DEFINE ACTION Notifier (TEXT motif, TEXT reference) 'information du client';

INITIALIZE WORKFLOW
    ON EVENT Souscription RECURSIVE SWITCH Qualification

-- Switch viable : Qualification gère Souscription. Si aucune branche ne
-- passe (offre inconnue), tout se passe comme si le SWITCH d'initialisation
-- n'avait pas été rencontré : pas de workflow (AB-1 dans la simulation).
DEFINE STATE Qualification 'qualification de l''offre'
    ON EVENT Souscription
        WHEN OffreConnue()
            SWITCH AttentePaiement
;

DEFINE STATE AttentePaiement 'en attente du premier paiement'
    ON EVENT Paiement
        WHEN PaiementAccepte()
            SWITCH Actif
;

-- Actif gère aussi Paiement : il lui faut une branche qui passe pour ce
-- même paiement, sinon le switch vers Actif serait ignoré. La branche
-- sans WHEN renouvelle l'état : une nouvelle instance à chaque paiement.
DEFINE STATE Actif 'abonnement actif'
    ON ENTER STATE
        -- @state.Uuid : l'instance qui vient d'être créée par le SWITCH.
        EXECUTE Notifier(motif = 'abonnement actif', reference = @state.Uuid)
    ON EVENT Paiement
        WHEN NOT PaiementAccepte()
            SWITCH Suspendu
        SWITCH Actif
    ON EVENT Resiliation
        WHEN EngagementTermine(mois = '12')
            SWITCH Resilie
        EXECUTE Notifier(motif = 'résiliation à l''échéance de l''engagement',
                         reference = @state.EventId)
            SWITCH Preavis
;

-- Même raison : Suspendu gère Paiement, la branche sans WHEN garantit que
-- le switch Actif → Suspendu (paiement refusé) trouve sa route.
DEFINE STATE Suspendu 'paiement refusé'
    ON EVENT Paiement
        WHEN PaiementAccepte()
            SWITCH Actif
        SWITCH Suspendu
;

DEFINE STATE Preavis  'résiliation programmée' ;
DEFINE STATE Resilie  'abonnement résilié' ;
`,
    rules: [],
    scripts: [
      {name: "offre_connue", source: "@IncomingEvent.Offre IN ('standard', 'premium')\n"},
      {name: "paiement_accepte", source: "@IncomingEvent.Statut = 'accepte'\n"},
      {name: "engagement_termine", source: "-- engagement exprimé en mois, compté en jours\nDAYS_BETWEEN(@state.CreationDate, NOW()) >= mois * 30\n"},
    ],
    schemas: [
      {name: "schema_Souscription",
       yaml: "title: Souscription\n" +
             "type: object\n" +
             "properties:\n" +
             "  Offre: {type: string}\n" +
             "  Email: {type: string}\n" +
             "required: [Offre]\n"},
    ],
    events: [
      {Name: "Souscription", Uuid: "b1111111-1111-4111-8111-111111111111",
       ExternalId: "AB-1", Offre: "gold", Email: "a@exemple.fr"},
      {Name: "Souscription", Uuid: "b2222222-2222-4222-8222-222222222222",
       ExternalId: "AB-2", Offre: "premium", Email: "b@exemple.fr"},
      {Name: "Paiement", Uuid: "b3333333-3333-4333-8333-333333333333",
       ExternalId: "AB-2", Statut: "refuse"},
      {Name: "Paiement", Uuid: "b4444444-4444-4444-8444-444444444444",
       ExternalId: "AB-2", Statut: "accepte"},
      {Name: "Paiement", Uuid: "b5555555-5555-4555-8555-555555555555",
       ExternalId: "AB-2", Statut: "accepte"},
      {Name: "Resiliation", Uuid: "b6666666-6666-4666-8666-666666666666",
       ExternalId: "AB-2"},
    ],
  },

  python: {
    label: "Scripts Python",
    script: `NAME OuvertureCompte VERSION 1
DESCRIPTION 'ouverture de compte — règles en Python et en expression'

DEFINE EVENT  DemandeOuverture      'un client demande l''ouverture'
    AS @schema_DemandeOuverture;
DEFINE EVENT  CoordonneesCorrigees  'le client corrige ses coordonnées'
    AS @schema_DemandeOuverture;
DEFINE EVENT  DepotRecu             'le dépôt initial est arrivé';
DEFINE EVENT  Relance               'relance automatique';

-- Trois règles implémentées en Python : fonctions enregistrées par
-- l'application (ici le serveur du playground, ScriptRegistry.add_function).
-- Les noms des paramètres sont ceux de la fonction : contrôlés au chargement.
DEFINE RULE   IbanValide (TEXT iban)       'clé IBAN correcte'   AS @iban_valide;
DEFINE RULE   EmailValide (TEXT adresse)   'adresse bien formée' AS @email_valide;
DEFINE RULE   DelaiDepasse (TEXT depuis, INTEGER jours)
    'jours ouvrés écoulés' AS @jours_ouvres_depuis;
-- Et une en expression : les deux langages se mélangent librement.
DEFINE RULE   DepotSuffisant (DECIMAL minimum) 'dépôt initial suffisant'
    AS @depot_suffisant;

DEFINE ACTION Notifier (TEXT motif, TEXT dossier) 'information du client';

DEFINE CONST  depot_min 100 'dépôt initial exigé';

INITIALIZE WORKFLOW
    ON EVENT DemandeOuverture RECURSIVE SWITCH Controle

DEFINE STATE Controle 'contrôle de la demande'
    ON EVENT DemandeOuverture
        WHEN NOT IbanValide(iban = @IncomingEvent.Iban)
            EXECUTE Notifier(motif = 'IBAN invalide', dossier = @Workflow.ExternalId)
            SWITCH Rejetee
        WHEN NOT EmailValide(adresse = @IncomingEvent.Email)
            SWITCH AttenteCoordonnees
        WHEN DepotSuffisant(minimum = depot_min)
            SWITCH Ouvert
        SWITCH AttenteDepot
;

DEFINE STATE AttenteCoordonnees 'adresse électronique à corriger'
    ON EVENT CoordonneesCorrigees
        WHEN EmailValide(adresse = @IncomingEvent.Email)
            SWITCH Ouvert
;

DEFINE STATE AttenteDepot 'en attente du dépôt initial'
    ON EVENT DepotRecu
        SWITCH Ouvert
    -- @state.CreationDate : entrée dans AttenteDepot ; la fonction Python
    -- compte les jours ouvrés jusqu'à maintenant.
    ON EVENT Relance
        WHEN DelaiDepasse(depuis = @state.CreationDate, jours = '10')
            EXECUTE Notifier(motif = 'demande expirée', dossier = @Workflow.ExternalId)
            SWITCH Rejetee
;

DEFINE STATE Ouvert 'compte ouvert' ;
DEFINE STATE Rejetee 'demande rejetée' ;
`,
    rules: [],
    scripts: [
      {name: "depot_suffisant", source: "-- un dépôt absent n'est jamais suffisant (NULL >= x → FALSE)\n@IncomingEvent.Montant >= minimum\n"},
    ],
    schemas: [
      {name: "schema_DemandeOuverture",
       yaml: "title: DemandeOuverture\n" +
             "type: object\n" +
             "properties:\n" +
             "  Iban: {type: string}\n" +
             "  Email: {type: string}\n" +
             "  Montant: {type: number, minimum: 0}\n"},
    ],
    events: [
      {Name: "DemandeOuverture", Uuid: "c1111111-1111-4111-8111-111111111111",
       ExternalId: "C-1", Iban: "FR76 3000 6000 0112 3456 7890 188",
       Email: "ana@exemple.fr", Montant: 500},
      {Name: "DemandeOuverture", Uuid: "c2222222-2222-4222-8222-222222222222",
       ExternalId: "C-2", Iban: "FR76 3000 6000 0112 3456 7890 189",
       Email: "jean@exemple", Montant: 500},
      {Name: "CoordonneesCorrigees", Uuid: "c3333333-3333-4333-8333-333333333333",
       ExternalId: "C-2", Email: "jean@exemple.fr"},
      {Name: "DemandeOuverture", Uuid: "c4444444-4444-4444-8444-444444444444",
       ExternalId: "C-3", Iban: "FR7630006000011234567890189",
       Email: "lea@exemple.fr", Montant: 20},
      {Name: "Relance", Uuid: "c5555555-5555-4555-8555-555555555555",
       ExternalId: "C-3"},
      {Name: "DepotRecu", Uuid: "c6666666-6666-4666-8666-666666666666",
       ExternalId: "C-3"},
    ],
  },

  artefacts: {
    label: "Artefacts JSON",
    script: `NAME Commandes VERSION 1
DESCRIPTION 'facturation des commandes — artefacts JSON produits par jslt'

DEFINE EVENT  CommandeValidee 'le client valide sa commande'
    AS @schema_CommandeValidee;
DEFINE EVENT  Livree 'la commande est livrée';

-- Les actions reçoivent des données bien formées : des artefacts JSON,
-- produits par un script jslt (vue Scripts) et validés par un schéma.
DEFINE ACTION AppelerFacturation (TEXT corps, TEXT client) 'POST /factures';
DEFINE ACTION Notifier (TEXT message) 'message au client';

DEFINE ARTIFACT RequeteFacture 'corps de la requête de facturation'
    AS @schema_RequeteFacture USING @requete_facture;
DEFINE ARTIFACT AvisLivraison 'message de livraison (sans schéma)'
    USING @avis_livraison;

DEFINE CONST  devise 'EUR' 'devise de facturation';

INITIALIZE WORKFLOW
    ON EVENT CommandeValidee SWITCH Facturee

DEFINE STATE Facturee 'facture demandée'
    -- @artifact.X : le JSON complet ; @artifact.X.partie : une partie.
    ON ENTER STATE
        EXECUTE AppelerFacturation(corps = @artifact.RequeteFacture,
                                   client = @artifact.RequeteFacture.client.nom)
    ON EVENT Livree
        SWITCH Livree
;

DEFINE STATE Livree 'commande livrée'
    ON ENTER STATE
        EXECUTE Notifier(message = @artifact.AvisLivraison)
;
`,
    rules: [],
    scripts: [
      {name: "requete_facture", language: "jslt", source:
        '{\n' +
        '    "reference": $.Workflow.ExternalId,\n' +
        '    "client": {\n' +
        '        "nom": $.IncomingEvent.Client.Nom,\n' +
        '        "email": $.IncomingEvent.Client.Email\n' +
        '    },\n' +
        '    "lignes": $.IncomingEvent.Lignes,\n' +
        '    "montant": $.IncomingEvent.Montant,\n' +
        '    "devise": $.constants.devise,\n' +
        '    "emise_le": $.now\n' +
        '}\n'},
      {name: "avis_livraison", language: "jslt", source:
        '{\n' +
        '    "commande": $.Workflow.ExternalId,\n' +
        '    "etat": $.state.Name,\n' +
        '    "depuis": $.state.CreationDate,\n' +
        '    "texte": "Votre commande est livrée"\n' +
        '}\n'},
    ],
    schemas: [
      {name: "schema_CommandeValidee",
       yaml: "title: CommandeValidee\n" +
             "type: object\n" +
             "properties:\n" +
             "  Client:\n" +
             "    type: object\n" +
             "    properties:\n" +
             "      Nom: {type: string}\n" +
             "      Email: {type: string}\n" +
             "  Lignes:\n" +
             "    type: array\n" +
             "    items:\n" +
             "      type: object\n" +
             "      properties:\n" +
             "        Article: {type: string}\n" +
             "        Quantite: {type: integer}\n" +
             "  Montant: {type: number}\n"},
      {name: "schema_RequeteFacture",
       yaml: "title: RequeteFacture\n" +
             "type: object\n" +
             "required: [reference, client, lignes, montant, devise]\n" +
             "properties:\n" +
             "  reference: {type: string}\n" +
             "  client:\n" +
             "    type: object\n" +
             "    required: [nom]\n" +
             "    properties:\n" +
             "      nom: {type: string}\n" +
             "      email: {type: [string, 'null']}\n" +
             "  lignes: {type: array, minItems: 1}\n" +
             "  montant: {type: number, exclusiveMinimum: 0}\n" +
             "  devise: {type: string, enum: [EUR]}\n" +
             "  emise_le: {type: string}\n"},
    ],
    events: [
      {Name: "CommandeValidee", Uuid: "e1111111-1111-4111-8111-111111111111",
       ExternalId: "CMD-1", Client: {Nom: "ACME", Email: "achats@acme.fr"},
       Lignes: [{Article: "Câble", Quantite: 3}], Montant: 42.5},
      {Name: "Livree", Uuid: "e2222222-2222-4222-8222-222222222222",
       ExternalId: "CMD-1"},
      {Name: "CommandeValidee", Uuid: "e3333333-3333-4333-8333-333333333333",
       ExternalId: "CMD-2", Client: {Nom: "Durand"}, Lignes: [], Montant: 0},
    ],
  },

  minimal: {
    label: "Script minimal",
    script: `NAME Demo VERSION 1

DEFINE EVENT Ouverture 'ouverture du dossier';
DEFINE EVENT Cloture   'clôture du dossier';

INITIALIZE WORKFLOW
    ON EVENT Ouverture SWITCH Ouvert

DEFINE STATE Ouvert 'dossier ouvert'
    ON EVENT Cloture
        SWITCH Ferme
;
DEFINE STATE Ferme 'dossier fermé' ;
`,
    rules: [],
    events: [
      {Name: "Ouverture", Uuid: "31111111-1111-4111-8111-111111111111", ExternalId: "D-1"},
      {Name: "Cloture",   Uuid: "32222222-2222-4222-8222-222222222222", ExternalId: "D-1"},
    ],
  },

  casse: {
    label: "Script avec erreurs",
    script: `NAME Casse VERSION 1

DEFINE EVENT Ouverture 'ouverture';
DEFINE ACTION Notifier (TEXT cible) 'notification';

INITIALIZE WORKFLOW
    ON EVENT Ouverture WHEN RegleInconnue() SWITCH Ouvert

DEFINE STATE Ouvert 'dossier ouvert'
    ON ENTER STATE
        EXECUTE Notifier(mauvaisArgument = 'x')
    ON EVENT Fermeture
        SWITCH EtatInexistant
;
`,
    rules: [],
    events: [],
  },
};

UW.define("examples", function (el, options) {
  var ws = options.workspace;
  var examples = options.examples || UW.examples;
  var select = document.createElement("select");
  select.title = "Exemples";
  select.innerHTML = "<option value=''>Exemples…</option>" +
    Object.keys(examples).map(function (key) {
      return "<option value='" + UW.util.esc(key) + "'>" +
        UW.util.esc(examples[key].label || key) + "</option>";
    }).join("");
  select.onchange = function () {
    var example = examples[select.value];
    select.value = "";
    if (example) { ws.loadExample(example); }
  };
  el.appendChild(select);
  return {select: select};
}, {label: "Exemples", description: "Charger un exemple dans l'espace de travail"});
})();
