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
    STATE key comment?
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
    | compositekey
    ;

rule_conditions :
      key LEFT_PAREN arguments? RIGHT_PAREN
    | NOT rule_conditions
    | rule_conditions AND rule_conditions
    | rule_conditions OR rule_conditions
    | LEFT_PAREN rule_conditions RIGHT_PAREN
    ;

event_declaration_statement :
    EVENT key comment?
    ;

action_declaration_statement :
    ACTION key LEFT_PAREN parameters? RIGHT_PAREN comment?
    ;

rule_declaration_statement :
    RULE key LEFT_PAREN parameters? RIGHT_PAREN comment?
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



