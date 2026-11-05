// Exemples préchargés du playground.
window.PLAYGROUND_EXAMPLES = {
  validation: {
    script: `NAME ValidationAchat VERSION 1
DESCRIPTION 'circuit de validation des demandes d''achat'
MATCHING (Type = 'achat')

DEFINE EVENT  DemandeSoumise     'une demande est déposée'
    AS @schema_DemandeSoumise UNIQUE (ExternalId, Montant);
DEFINE EVENT  PiecesFournies     'le demandeur complète son dossier';
DEFINE EVENT  ValidationAccordee 'un valideur approuve';
DEFINE EVENT  ValidationRefusee  'un valideur refuse';

DEFINE RULE   EstComplet (TEXT champs)         'les champs requis sont présents';
-- Règle écrite dans le script (AS …) : évaluée par le moteur, sans
-- entrée dans le panneau Paramétrage.
DEFINE RULE   MontantInferieur (DECIMAL seuil) 'montant sous le seuil'
    AS @IncomingEvent.Montant < seuil;

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
    script: `NAME Reclamations VERSION 1
DESCRIPTION 'réclamations clients — règles écrites dans le script'

DEFINE EVENT  ReclamationDeposee 'une réclamation est déposée'
    AS @schema_Reclamation;
DEFINE EVENT  PieceAjoutee 'le client complète son dossier';
DEFINE EVENT  Relance      'le client relance';
DEFINE EVENT  Cloture      'le conseiller clôt le dossier';

-- Règles écrites dans le script (AS …) : évaluées par le moteur pendant
-- la simulation, sans entrée dans le panneau Paramétrage.
DEFINE RULE   Urgente (DECIMAL plafond) 'réclamation urgente'
    AS CONTAINS(@IncomingEvent.Libelle, 'urgent')
       OR @IncomingEvent.Montant * 1.2 > plafond;
DEFINE RULE   Complete (INTEGER minimum) 'assez de pièces jointes'
    AS LENGTH(@IncomingEvent.Pieces) >= minimum;
DEFINE RULE   SansMontant () 'montant non renseigné'
    AS @IncomingEvent.Montant IS NULL;
DEFINE RULE   CanalNumerique () 'déposée en ligne'
    AS @IncomingEvent.Canal IN ('web', 'mobile');
-- @state : l'état du bloc qui APPELLE la règle (ici Incomplete).
DEFINE RULE   Ancienne (INTEGER jours) 'dans l''état depuis assez longtemps'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= jours;

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
    script: `NAME Abonnement VERSION 1
DESCRIPTION 'abonnement — états modélisés, @state et switch viable'

DEFINE EVENT  Souscription 'le client souscrit' AS @schema_Souscription;
DEFINE EVENT  Paiement     'un paiement est reçu';
DEFINE EVENT  Resiliation  'le client résilie';

DEFINE RULE   OffreConnue () 'offre au catalogue'
    AS @IncomingEvent.Offre IN ('standard', 'premium');
DEFINE RULE   PaiementAccepte () 'paiement accepté'
    AS @IncomingEvent.Statut = 'accepte';
DEFINE RULE   EngagementTermine (INTEGER mois) 'engagement écoulé'
    AS DAYS_BETWEEN(@state.CreationDate, NOW()) >= mois * 30;

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

  minimal: {
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
