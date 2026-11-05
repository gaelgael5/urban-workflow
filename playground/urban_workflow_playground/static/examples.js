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
