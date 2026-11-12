/**
 * workflow engine Parser
 *
 * Copyright (c) 2017-2019 Gael beard <gaelgael5@gmail.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

parser grammar WorkflowParser;

options { 
    // memoize=True;
    tokenVocab=WorkflowLexer; 
    }

script :
    script_fragment | script_full
    EOF
    ;

script_fragment :
    FRAGMENT NAME key 
    (DESCRIPTION comment)?
	(define_referenciel_statement SEMICOLON)+ 
    ;

script_full :
    (INCLUDE CHAR_STRING)*
    NAME key (VERSION versionNumber=number)?
    concurency?
    (DESCRIPTION comment)?
    (MATCHING matchings)? 
	(define_referenciel_statement SEMICOLON)+ 
    initializing?
	(define_state_statement SEMICOLON)*
    ;

concurency :
    (CONCURENCY concurencyNumber=number)
    ;

define_referenciel_statement :
	DEFINE
    (  
        event_declaration_statement
      | rule_declaration_statement
      | action_declaration_statement
      | artifact_declaration_statement
      | constant_declaration
    )    
    ;

define_state_statement : 
    DEFINE state
    ;

constant_declaration :
    CONST key value comment?
    ;

value :
    string | number | delay | REGULAR_ID
    ;

state :
    // (AS ...) : extension urban-workflow -- schema (YAML) des champs metier
    // de l'etat, meme registre que les schemas d'evenements.
    STATE key comment? (AS schemaRef=compositekey)?
    execute*
    on_event_statement*
    ;

initializing : 
    INITIALIZE WORKFLOW initializing_item+
    ;

initializing_item :
    ON EVENT key (WHEN rule_conditions)? RECURSIVE? SWITCH key
    ;

on_event_statement :
    (ON EVENT key | EXPIRE AFTER delay) switch_state+
    ;    

switch_state :
    (WHEN rule_conditions)?
    (
          execute2* SWITCH key
        | execute2+
    )
    ;

execute :
    ON (ENTER STATE | EXIT STATE | ENTER AND EXIT STATE) 
    execute2
    ;

execute2 :
    (WHEN rule_conditions)? 
    (WAITING delay BEFORE)? 
    execute3+
    ;

execute3 :
      (EXECUTE | key) action+
    | STORE matchings+
    ;

matchings : 
    LEFT_PAREN matching+ RIGHT_PAREN
    ;

matching :
    key EQUAL string
    ;

action : 
    key LEFT_PAREN arguments? RIGHT_PAREN
    ;
    
arguments : 
    argument (COMMA argument)*
    ;

argument :
    key EQUAL argumentValue
    ;

argumentValue :
      string 
    | contextPath
    | compositekey
    ;

// Extension urban-workflow : chemin @Racine suivi de segments. Les racines
// @IncomingEvent (evenement entrant : socle + donnees metier) et @state
// (instance de l'etat courant) designent des documents JSON et acceptent
// en plus les index de liste [n] et les cles ['prop'] ; les autres racines
// (@Workflow, @Event) restent des references a proprietes simples.
// Place AVANT compositekey : sur un chemin a points seuls, ambigu entre les
// deux, ANTLR retient la premiere alternative -- tout chemin @ passe ici.
// Sous-ensemble volontaire : pas de filtres ni de jokers (une regle recoit
// UNE valeur).
contextPath :
    AROBASE key jsonPathSegment*
    ;

jsonPathSegment :
      DOT key
    | LEFT_BRACKET NUMBER RIGHT_BRACKET
    | LEFT_BRACKET CHAR_STRING RIGHT_BRACKET
    ;

rule_conditions :
      key LEFT_PAREN arguments? RIGHT_PAREN
    | NOT rule_conditions
    | rule_conditions AND rule_conditions
    | rule_conditions OR rule_conditions
    | LEFT_PAREN rule_conditions RIGHT_PAREN
    ;

event_declaration_statement :
    // (AS ...) et (UNIQUE ...) : extensions urban-workflow.
    // AS reference un JSON Schema (YAML) enregistre dans le SchemaRegistry
    // a l'initialisation du moteur ; UNIQUE liste les proprietes du payload
    // dont le hash sert d'anti-doublon (le champ DedupKey fourni par
    // l'emetteur reste prioritaire quand il est present).
    EVENT key comment? (AS schemaRef=compositekey)? (UNIQUE unique_keys)?
    ;

unique_keys :
    LEFT_PAREN key (COMMA key)* RIGHT_PAREN
    ;

action_declaration_statement :
    // (AS ...) : extension urban-workflow -- reference de la methode de
    // l'action dans le ScriptRegistry (verifiee au chargement ; son
    // execution est a cadrer).
    ACTION key LEFT_PAREN parameters? RIGHT_PAREN comment? (AS scriptRef=compositekey)?
    ;

artifact_declaration_statement :
    // Extension urban-workflow (decision utilisateur du 2026-11-08) : un
    // artefact est un document JSON NOMME, produit par un script (jslt) du
    // ScriptRegistry (USING) et valide par un JSON Schema facultatif du
    // SchemaRegistry (AS, comme EVENT et STATE). Sans parametres : le script
    // lit le contexte ; consomme par le chemin @artifact.Nom dans les
    // arguments d'action (le JSON n'est qu'un moyen de fournir une donnee
    // bien formee a autre chose, ex. le corps d'un appel HTTP).
    ARTIFACT key comment? (AS schemaRef=compositekey)? USING scriptRef=compositekey
    ;

rule_declaration_statement :
    // (AS ...) : extension urban-workflow -- la regle est implementee par un
    // script du ScriptRegistry, charge a l'initialisation du moteur comme les
    // schemas : le document de workflow ne porte pas de code (decision
    // utilisateur du 2026-11-07). Sans AS, la regle reste une fonction
    // enregistree cote code (FunctionRegistry), comme dans le source.
    RULE key LEFT_PAREN parameters? RIGHT_PAREN comment? (AS scriptRef=compositekey)?
    ;

// Extension urban-workflow : point d'entree d'un script du langage
// d'expressions (fichier separe du workflow, une seule expression ; le ';'
// final est tolere).
rule_script :
    expression SEMICOLON? EOF
    ;

// Extension urban-workflow : langage d'expressions des regles. Dans une
// regle recursive a gauche, ANTLR donne la priorite aux alternatives les
// plus HAUTES : moins unaire, puis * /, + -, comparaisons / IN / IS NULL,
// NOT, AND, OR -- l'ordre usuel (NOT a = b se lit NOT (a = b)).
expression :
      MINUS expression                                                  #negateExpression
    | expression op=(STAR | SLASH) expression                           #multiplyExpression
    | expression op=(PLUS | MINUS) expression                           #addExpression
    | expression op=(EQUAL | NOT_EQUAL | LESS | LESS_EQUAL | GREATER | GREATER_EQUAL) expression
                                                                        #compareExpression
    | expression NOT? IN LEFT_PAREN expression (COMMA expression)* RIGHT_PAREN
                                                                        #inExpression
    | expression IS NOT? NULL                                           #nullExpression
    | NOT expression                                                    #notExpression
    | expression AND expression                                         #andExpression
    | expression OR expression                                          #orExpression
    | primaryExpression                                                 #primary
    ;

primaryExpression :
      numeric                                                           #numericLiteral
    | number                                                            #integerLiteral
    | string                                                            #stringLiteral
    | (TRUE | FALSE)                                                    #booleanLiteral
    | NULL                                                              #nullLiteral
    | contextPath                                                       #pathValue
    | key LEFT_PAREN (expression (COMMA expression)*)? RIGHT_PAREN      #functionCall
    | key                                                               #identifier
    | LEFT_PAREN expression RIGHT_PAREN                                 #parenthesized
    ;

parameters : 
    parameter (COMMA parameter)*
    ;

parameter :
    type key
    ;

type : 
    TEXT | INTEGER | DECIMAL
    ;

key : REGULAR_ID;

compositekey : 
    AROBASE? key (DOT key)*
    ;

comment : CHAR_STRING;

number : NUMBER;

numeric :
    number DOT number
    ;

string :
	CHAR_STRING
    ;

delay :
    number (MINUTE | HOUR | DAY)
    ;



