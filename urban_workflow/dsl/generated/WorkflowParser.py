# Generated from WorkflowParser.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,55,421,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,33,
        7,33,2,34,7,34,2,35,7,35,2,36,7,36,1,0,1,0,1,0,1,0,3,0,79,8,0,1,
        1,1,1,1,1,1,1,1,1,3,1,86,8,1,1,1,1,1,1,1,4,1,91,8,1,11,1,12,1,92,
        1,2,1,2,5,2,97,8,2,10,2,12,2,100,9,2,1,2,1,2,1,2,1,2,3,2,106,8,2,
        1,2,3,2,109,8,2,1,2,1,2,3,2,113,8,2,1,2,1,2,3,2,117,8,2,1,2,1,2,
        1,2,4,2,122,8,2,11,2,12,2,123,1,2,3,2,127,8,2,1,2,1,2,1,2,5,2,132,
        8,2,10,2,12,2,135,9,2,1,3,1,3,1,3,1,4,1,4,1,4,1,4,1,4,3,4,145,8,
        4,1,5,1,5,1,5,1,6,1,6,1,6,1,6,3,6,154,8,6,1,7,1,7,1,7,1,7,3,7,160,
        8,7,1,8,1,8,1,8,3,8,165,8,8,1,8,5,8,168,8,8,10,8,12,8,171,9,8,1,
        8,5,8,174,8,8,10,8,12,8,177,9,8,1,9,1,9,1,9,4,9,182,8,9,11,9,12,
        9,183,1,10,1,10,1,10,1,10,1,10,3,10,191,8,10,1,10,3,10,194,8,10,
        1,10,1,10,1,10,1,11,1,11,1,11,1,11,1,11,1,11,3,11,205,8,11,1,11,
        4,11,208,8,11,11,11,12,11,209,1,12,1,12,3,12,214,8,12,1,12,5,12,
        217,8,12,10,12,12,12,220,9,12,1,12,1,12,1,12,4,12,225,8,12,11,12,
        12,12,226,3,12,229,8,12,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,3,13,240,8,13,1,13,1,13,1,14,1,14,3,14,246,8,14,1,14,1,14,1,
        14,1,14,3,14,252,8,14,1,14,4,14,255,8,14,11,14,12,14,256,1,15,1,
        15,3,15,261,8,15,1,15,4,15,264,8,15,11,15,12,15,265,1,15,1,15,4,
        15,270,8,15,11,15,12,15,271,3,15,274,8,15,1,16,1,16,4,16,278,8,16,
        11,16,12,16,279,1,16,1,16,1,17,1,17,1,17,1,17,1,18,1,18,1,18,3,18,
        291,8,18,1,18,1,18,1,19,1,19,1,19,5,19,298,8,19,10,19,12,19,301,
        9,19,1,20,1,20,1,20,1,20,1,21,1,21,3,21,309,8,21,1,22,1,22,1,22,
        1,22,3,22,315,8,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,3,22,
        325,8,22,1,22,1,22,1,22,1,22,1,22,1,22,5,22,333,8,22,10,22,12,22,
        336,9,22,1,23,1,23,1,23,3,23,341,8,23,1,23,1,23,3,23,345,8,23,1,
        23,1,23,3,23,349,8,23,1,24,1,24,1,24,1,24,5,24,355,8,24,10,24,12,
        24,358,9,24,1,24,1,24,1,25,1,25,1,25,1,25,3,25,366,8,25,1,25,1,25,
        3,25,370,8,25,1,26,1,26,1,26,1,26,3,26,376,8,26,1,26,1,26,3,26,380,
        8,26,1,27,1,27,1,27,5,27,385,8,27,10,27,12,27,388,9,27,1,28,1,28,
        1,28,1,29,1,29,1,30,1,30,1,31,3,31,398,8,31,1,31,1,31,1,31,5,31,
        403,8,31,10,31,12,31,406,9,31,1,32,1,32,1,33,1,33,1,34,1,34,1,34,
        1,34,1,35,1,35,1,36,1,36,1,36,1,36,0,1,44,37,0,2,4,6,8,10,12,14,
        16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,
        60,62,64,66,68,70,72,0,2,3,0,11,11,22,22,35,35,3,0,9,9,19,19,24,
        24,442,0,78,1,0,0,0,2,80,1,0,0,0,4,98,1,0,0,0,6,136,1,0,0,0,8,139,
        1,0,0,0,10,146,1,0,0,0,12,149,1,0,0,0,14,159,1,0,0,0,16,161,1,0,
        0,0,18,178,1,0,0,0,20,185,1,0,0,0,22,204,1,0,0,0,24,213,1,0,0,0,
        26,230,1,0,0,0,28,245,1,0,0,0,30,273,1,0,0,0,32,275,1,0,0,0,34,283,
        1,0,0,0,36,287,1,0,0,0,38,294,1,0,0,0,40,302,1,0,0,0,42,308,1,0,
        0,0,44,324,1,0,0,0,46,337,1,0,0,0,48,350,1,0,0,0,50,361,1,0,0,0,
        52,371,1,0,0,0,54,381,1,0,0,0,56,389,1,0,0,0,58,392,1,0,0,0,60,394,
        1,0,0,0,62,397,1,0,0,0,64,407,1,0,0,0,66,409,1,0,0,0,68,411,1,0,
        0,0,70,415,1,0,0,0,72,417,1,0,0,0,74,79,3,2,1,0,75,76,3,4,2,0,76,
        77,5,0,0,1,77,79,1,0,0,0,78,74,1,0,0,0,78,75,1,0,0,0,79,1,1,0,0,
        0,80,81,5,18,0,0,81,82,5,25,0,0,82,85,3,60,30,0,83,84,5,8,0,0,84,
        86,3,64,32,0,85,83,1,0,0,0,85,86,1,0,0,0,86,90,1,0,0,0,87,88,3,8,
        4,0,88,89,5,46,0,0,89,91,1,0,0,0,90,87,1,0,0,0,91,92,1,0,0,0,92,
        90,1,0,0,0,92,93,1,0,0,0,93,3,1,0,0,0,94,95,5,20,0,0,95,97,5,43,
        0,0,96,94,1,0,0,0,97,100,1,0,0,0,98,96,1,0,0,0,98,99,1,0,0,0,99,
        101,1,0,0,0,100,98,1,0,0,0,101,102,5,25,0,0,102,105,3,60,30,0,103,
        104,5,38,0,0,104,106,3,66,33,0,105,103,1,0,0,0,105,106,1,0,0,0,106,
        108,1,0,0,0,107,109,3,6,3,0,108,107,1,0,0,0,108,109,1,0,0,0,109,
        112,1,0,0,0,110,111,5,8,0,0,111,113,3,64,32,0,112,110,1,0,0,0,112,
        113,1,0,0,0,113,116,1,0,0,0,114,115,5,23,0,0,115,117,3,32,16,0,116,
        114,1,0,0,0,116,117,1,0,0,0,117,121,1,0,0,0,118,119,3,8,4,0,119,
        120,5,46,0,0,120,122,1,0,0,0,121,118,1,0,0,0,122,123,1,0,0,0,123,
        121,1,0,0,0,123,124,1,0,0,0,124,126,1,0,0,0,125,127,3,18,9,0,126,
        125,1,0,0,0,126,127,1,0,0,0,127,133,1,0,0,0,128,129,3,10,5,0,129,
        130,5,46,0,0,130,132,1,0,0,0,131,128,1,0,0,0,132,135,1,0,0,0,133,
        131,1,0,0,0,133,134,1,0,0,0,134,5,1,0,0,0,135,133,1,0,0,0,136,137,
        5,7,0,0,137,138,3,66,33,0,138,7,1,0,0,0,139,144,5,10,0,0,140,145,
        3,46,23,0,141,145,3,52,26,0,142,145,3,50,25,0,143,145,3,12,6,0,144,
        140,1,0,0,0,144,141,1,0,0,0,144,142,1,0,0,0,144,143,1,0,0,0,145,
        9,1,0,0,0,146,147,5,10,0,0,147,148,3,16,8,0,148,11,1,0,0,0,149,150,
        5,6,0,0,150,151,3,60,30,0,151,153,3,14,7,0,152,154,3,64,32,0,153,
        152,1,0,0,0,153,154,1,0,0,0,154,13,1,0,0,0,155,160,3,70,35,0,156,
        160,3,66,33,0,157,160,3,72,36,0,158,160,5,55,0,0,159,155,1,0,0,0,
        159,156,1,0,0,0,159,157,1,0,0,0,159,158,1,0,0,0,160,15,1,0,0,0,161,
        162,5,33,0,0,162,164,3,60,30,0,163,165,3,64,32,0,164,163,1,0,0,0,
        164,165,1,0,0,0,165,169,1,0,0,0,166,168,3,26,13,0,167,166,1,0,0,
        0,168,171,1,0,0,0,169,167,1,0,0,0,169,170,1,0,0,0,170,175,1,0,0,
        0,171,169,1,0,0,0,172,174,3,22,11,0,173,172,1,0,0,0,174,177,1,0,
        0,0,175,173,1,0,0,0,175,176,1,0,0,0,176,17,1,0,0,0,177,175,1,0,0,
        0,178,179,5,21,0,0,179,181,5,42,0,0,180,182,3,20,10,0,181,180,1,
        0,0,0,182,183,1,0,0,0,183,181,1,0,0,0,183,184,1,0,0,0,184,19,1,0,
        0,0,185,186,5,27,0,0,186,187,5,12,0,0,187,190,3,60,30,0,188,189,
        5,41,0,0,189,191,3,44,22,0,190,188,1,0,0,0,190,191,1,0,0,0,191,193,
        1,0,0,0,192,194,5,31,0,0,193,192,1,0,0,0,193,194,1,0,0,0,194,195,
        1,0,0,0,195,196,5,32,0,0,196,197,3,60,30,0,197,21,1,0,0,0,198,199,
        5,27,0,0,199,200,5,12,0,0,200,205,3,60,30,0,201,202,5,17,0,0,202,
        203,5,2,0,0,203,205,3,72,36,0,204,198,1,0,0,0,204,201,1,0,0,0,205,
        207,1,0,0,0,206,208,3,24,12,0,207,206,1,0,0,0,208,209,1,0,0,0,209,
        207,1,0,0,0,209,210,1,0,0,0,210,23,1,0,0,0,211,212,5,41,0,0,212,
        214,3,44,22,0,213,211,1,0,0,0,213,214,1,0,0,0,214,228,1,0,0,0,215,
        217,3,28,14,0,216,215,1,0,0,0,217,220,1,0,0,0,218,216,1,0,0,0,218,
        219,1,0,0,0,219,221,1,0,0,0,220,218,1,0,0,0,221,222,5,32,0,0,222,
        229,3,60,30,0,223,225,3,28,14,0,224,223,1,0,0,0,225,226,1,0,0,0,
        226,224,1,0,0,0,226,227,1,0,0,0,227,229,1,0,0,0,228,218,1,0,0,0,
        228,224,1,0,0,0,229,25,1,0,0,0,230,239,5,27,0,0,231,232,5,14,0,0,
        232,240,5,33,0,0,233,234,5,16,0,0,234,240,5,33,0,0,235,236,5,14,
        0,0,236,237,5,3,0,0,237,238,5,16,0,0,238,240,5,33,0,0,239,231,1,
        0,0,0,239,233,1,0,0,0,239,235,1,0,0,0,240,241,1,0,0,0,241,242,3,
        28,14,0,242,27,1,0,0,0,243,244,5,41,0,0,244,246,3,44,22,0,245,243,
        1,0,0,0,245,246,1,0,0,0,246,251,1,0,0,0,247,248,5,39,0,0,248,249,
        3,72,36,0,249,250,5,5,0,0,250,252,1,0,0,0,251,247,1,0,0,0,251,252,
        1,0,0,0,252,254,1,0,0,0,253,255,3,30,15,0,254,253,1,0,0,0,255,256,
        1,0,0,0,256,254,1,0,0,0,256,257,1,0,0,0,257,29,1,0,0,0,258,261,5,
        13,0,0,259,261,3,60,30,0,260,258,1,0,0,0,260,259,1,0,0,0,261,263,
        1,0,0,0,262,264,3,36,18,0,263,262,1,0,0,0,264,265,1,0,0,0,265,263,
        1,0,0,0,265,266,1,0,0,0,266,274,1,0,0,0,267,269,5,34,0,0,268,270,
        3,32,16,0,269,268,1,0,0,0,270,271,1,0,0,0,271,269,1,0,0,0,271,272,
        1,0,0,0,272,274,1,0,0,0,273,260,1,0,0,0,273,267,1,0,0,0,274,31,1,
        0,0,0,275,277,5,44,0,0,276,278,3,34,17,0,277,276,1,0,0,0,278,279,
        1,0,0,0,279,277,1,0,0,0,279,280,1,0,0,0,280,281,1,0,0,0,281,282,
        5,45,0,0,282,33,1,0,0,0,283,284,3,60,30,0,284,285,5,15,0,0,285,286,
        3,70,35,0,286,35,1,0,0,0,287,288,3,60,30,0,288,290,5,44,0,0,289,
        291,3,38,19,0,290,289,1,0,0,0,290,291,1,0,0,0,291,292,1,0,0,0,292,
        293,5,45,0,0,293,37,1,0,0,0,294,299,3,40,20,0,295,296,5,48,0,0,296,
        298,3,40,20,0,297,295,1,0,0,0,298,301,1,0,0,0,299,297,1,0,0,0,299,
        300,1,0,0,0,300,39,1,0,0,0,301,299,1,0,0,0,302,303,3,60,30,0,303,
        304,5,15,0,0,304,305,3,42,21,0,305,41,1,0,0,0,306,309,3,70,35,0,
        307,309,3,62,31,0,308,306,1,0,0,0,308,307,1,0,0,0,309,43,1,0,0,0,
        310,311,6,22,-1,0,311,312,3,60,30,0,312,314,5,44,0,0,313,315,3,38,
        19,0,314,313,1,0,0,0,314,315,1,0,0,0,315,316,1,0,0,0,316,317,5,45,
        0,0,317,325,1,0,0,0,318,319,5,26,0,0,319,325,3,44,22,4,320,321,5,
        44,0,0,321,322,3,44,22,0,322,323,5,45,0,0,323,325,1,0,0,0,324,310,
        1,0,0,0,324,318,1,0,0,0,324,320,1,0,0,0,325,334,1,0,0,0,326,327,
        10,3,0,0,327,328,5,3,0,0,328,333,3,44,22,4,329,330,10,2,0,0,330,
        331,5,28,0,0,331,333,3,44,22,3,332,326,1,0,0,0,332,329,1,0,0,0,333,
        336,1,0,0,0,334,332,1,0,0,0,334,335,1,0,0,0,335,45,1,0,0,0,336,334,
        1,0,0,0,337,338,5,12,0,0,338,340,3,60,30,0,339,341,3,64,32,0,340,
        339,1,0,0,0,340,341,1,0,0,0,341,344,1,0,0,0,342,343,5,4,0,0,343,
        345,3,62,31,0,344,342,1,0,0,0,344,345,1,0,0,0,345,348,1,0,0,0,346,
        347,5,37,0,0,347,349,3,48,24,0,348,346,1,0,0,0,348,349,1,0,0,0,349,
        47,1,0,0,0,350,351,5,44,0,0,351,356,3,60,30,0,352,353,5,48,0,0,353,
        355,3,60,30,0,354,352,1,0,0,0,355,358,1,0,0,0,356,354,1,0,0,0,356,
        357,1,0,0,0,357,359,1,0,0,0,358,356,1,0,0,0,359,360,5,45,0,0,360,
        49,1,0,0,0,361,362,5,1,0,0,362,363,3,60,30,0,363,365,5,44,0,0,364,
        366,3,54,27,0,365,364,1,0,0,0,365,366,1,0,0,0,366,367,1,0,0,0,367,
        369,5,45,0,0,368,370,3,64,32,0,369,368,1,0,0,0,369,370,1,0,0,0,370,
        51,1,0,0,0,371,372,5,30,0,0,372,373,3,60,30,0,373,375,5,44,0,0,374,
        376,3,54,27,0,375,374,1,0,0,0,375,376,1,0,0,0,376,377,1,0,0,0,377,
        379,5,45,0,0,378,380,3,64,32,0,379,378,1,0,0,0,379,380,1,0,0,0,380,
        53,1,0,0,0,381,386,3,56,28,0,382,383,5,48,0,0,383,385,3,56,28,0,
        384,382,1,0,0,0,385,388,1,0,0,0,386,384,1,0,0,0,386,387,1,0,0,0,
        387,55,1,0,0,0,388,386,1,0,0,0,389,390,3,58,29,0,390,391,3,60,30,
        0,391,57,1,0,0,0,392,393,7,0,0,0,393,59,1,0,0,0,394,395,5,55,0,0,
        395,61,1,0,0,0,396,398,5,50,0,0,397,396,1,0,0,0,397,398,1,0,0,0,
        398,399,1,0,0,0,399,404,3,60,30,0,400,401,5,49,0,0,401,403,3,60,
        30,0,402,400,1,0,0,0,403,406,1,0,0,0,404,402,1,0,0,0,404,405,1,0,
        0,0,405,63,1,0,0,0,406,404,1,0,0,0,407,408,5,43,0,0,408,65,1,0,0,
        0,409,410,5,52,0,0,410,67,1,0,0,0,411,412,3,66,33,0,412,413,5,49,
        0,0,413,414,3,66,33,0,414,69,1,0,0,0,415,416,5,43,0,0,416,71,1,0,
        0,0,417,418,3,66,33,0,418,419,7,1,0,0,419,73,1,0,0,0,53,78,85,92,
        98,105,108,112,116,123,126,133,144,153,159,164,169,175,183,190,193,
        204,209,213,218,226,228,239,245,251,256,260,265,271,273,279,290,
        299,308,314,324,332,334,340,344,348,356,365,369,375,379,386,397,
        404
    ]

class WorkflowParser ( Parser ):

    grammarFileName = "WorkflowParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'ACTION'", "'AFTER'", "'AND'", "'AS'", 
                     "'BEFORE'", "'CONST'", "'CONCURENCY'", "'DESCRIPTION'", 
                     "'DAY'", "'DEFINE'", "'DECIMAL'", "'EVENT'", "'EXECUTE'", 
                     "'ENTER'", "'='", "'EXIT'", "'EXPIRE'", "'FRAGMENT'", 
                     "'HOUR'", "'INCLUDE'", "'INITIALIZE'", "'INTEGER'", 
                     "'MATCHING'", "'MINUTE'", "'NAME'", "'NOT'", "'ON'", 
                     "'OR'", "'PARAMETER'", "'RULE'", "'RECURSIVE'", "'SWITCH'", 
                     "'STATE'", "'STORE'", "'TEXT'", "'TIME'", "'UNIQUE'", 
                     "'VERSION'", "'WAITING'", "'WITH'", "'WHEN'", "'WORKFLOW'", 
                     "<INVALID>", "'('", "')'", "';'", "':'", "','", "'.'", 
                     "'@'" ]

    symbolicNames = [ "<INVALID>", "ACTION", "AFTER", "AND", "AS", "BEFORE", 
                      "CONST", "CONCURENCY", "DESCRIPTION", "DAY", "DEFINE", 
                      "DECIMAL", "EVENT", "EXECUTE", "ENTER", "EQUAL", "EXIT", 
                      "EXPIRE", "FRAGMENT", "HOUR", "INCLUDE", "INITIALIZE", 
                      "INTEGER", "MATCHING", "MINUTE", "NAME", "NOT", "ON", 
                      "OR", "PARAMETER", "RULE", "RECURSIVE", "SWITCH", 
                      "STATE", "STORE", "TEXT", "TIME", "UNIQUE", "VERSION", 
                      "WAITING", "WITH", "WHEN", "WORKFLOW", "CHAR_STRING", 
                      "LEFT_PAREN", "RIGHT_PAREN", "SEMICOLON", "COLON", 
                      "COMMA", "DOT", "AROBASE", "SPACES", "NUMBER", "SINGLE_LINE_COMMENT", 
                      "MULTI_LINE_COMMENT", "REGULAR_ID" ]

    RULE_script = 0
    RULE_script_fragment = 1
    RULE_script_full = 2
    RULE_concurency = 3
    RULE_define_referenciel_statement = 4
    RULE_define_state_statement = 5
    RULE_constant_declaration = 6
    RULE_value = 7
    RULE_state = 8
    RULE_initializing = 9
    RULE_initializing_item = 10
    RULE_on_event_statement = 11
    RULE_switch_state = 12
    RULE_execute = 13
    RULE_execute2 = 14
    RULE_execute3 = 15
    RULE_matchings = 16
    RULE_matching = 17
    RULE_action = 18
    RULE_arguments = 19
    RULE_argument = 20
    RULE_argumentValue = 21
    RULE_rule_conditions = 22
    RULE_event_declaration_statement = 23
    RULE_unique_keys = 24
    RULE_action_declaration_statement = 25
    RULE_rule_declaration_statement = 26
    RULE_parameters = 27
    RULE_parameter = 28
    RULE_type = 29
    RULE_key = 30
    RULE_compositekey = 31
    RULE_comment = 32
    RULE_number = 33
    RULE_numeric = 34
    RULE_string = 35
    RULE_delay = 36

    ruleNames =  [ "script", "script_fragment", "script_full", "concurency", 
                   "define_referenciel_statement", "define_state_statement", 
                   "constant_declaration", "value", "state", "initializing", 
                   "initializing_item", "on_event_statement", "switch_state", 
                   "execute", "execute2", "execute3", "matchings", "matching", 
                   "action", "arguments", "argument", "argumentValue", "rule_conditions", 
                   "event_declaration_statement", "unique_keys", "action_declaration_statement", 
                   "rule_declaration_statement", "parameters", "parameter", 
                   "type", "key", "compositekey", "comment", "number", "numeric", 
                   "string", "delay" ]

    EOF = Token.EOF
    ACTION=1
    AFTER=2
    AND=3
    AS=4
    BEFORE=5
    CONST=6
    CONCURENCY=7
    DESCRIPTION=8
    DAY=9
    DEFINE=10
    DECIMAL=11
    EVENT=12
    EXECUTE=13
    ENTER=14
    EQUAL=15
    EXIT=16
    EXPIRE=17
    FRAGMENT=18
    HOUR=19
    INCLUDE=20
    INITIALIZE=21
    INTEGER=22
    MATCHING=23
    MINUTE=24
    NAME=25
    NOT=26
    ON=27
    OR=28
    PARAMETER=29
    RULE=30
    RECURSIVE=31
    SWITCH=32
    STATE=33
    STORE=34
    TEXT=35
    TIME=36
    UNIQUE=37
    VERSION=38
    WAITING=39
    WITH=40
    WHEN=41
    WORKFLOW=42
    CHAR_STRING=43
    LEFT_PAREN=44
    RIGHT_PAREN=45
    SEMICOLON=46
    COLON=47
    COMMA=48
    DOT=49
    AROBASE=50
    SPACES=51
    NUMBER=52
    SINGLE_LINE_COMMENT=53
    MULTI_LINE_COMMENT=54
    REGULAR_ID=55

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ScriptContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def script_fragment(self):
            return self.getTypedRuleContext(WorkflowParser.Script_fragmentContext,0)


        def script_full(self):
            return self.getTypedRuleContext(WorkflowParser.Script_fullContext,0)


        def EOF(self):
            return self.getToken(WorkflowParser.EOF, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_script

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScript" ):
                return visitor.visitScript(self)
            else:
                return visitor.visitChildren(self)




    def script(self):

        localctx = WorkflowParser.ScriptContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_script)
        try:
            self.state = 78
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [18]:
                self.enterOuterAlt(localctx, 1)
                self.state = 74
                self.script_fragment()
                pass
            elif token in [20, 25]:
                self.enterOuterAlt(localctx, 2)
                self.state = 75
                self.script_full()
                self.state = 76
                self.match(WorkflowParser.EOF)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Script_fragmentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FRAGMENT(self):
            return self.getToken(WorkflowParser.FRAGMENT, 0)

        def NAME(self):
            return self.getToken(WorkflowParser.NAME, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def DESCRIPTION(self):
            return self.getToken(WorkflowParser.DESCRIPTION, 0)

        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def define_referenciel_statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Define_referenciel_statementContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.Define_referenciel_statementContext,i)


        def SEMICOLON(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.SEMICOLON)
            else:
                return self.getToken(WorkflowParser.SEMICOLON, i)

        def getRuleIndex(self):
            return WorkflowParser.RULE_script_fragment

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScript_fragment" ):
                return visitor.visitScript_fragment(self)
            else:
                return visitor.visitChildren(self)




    def script_fragment(self):

        localctx = WorkflowParser.Script_fragmentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_script_fragment)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 80
            self.match(WorkflowParser.FRAGMENT)
            self.state = 81
            self.match(WorkflowParser.NAME)
            self.state = 82
            self.key()
            self.state = 85
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 83
                self.match(WorkflowParser.DESCRIPTION)
                self.state = 84
                self.comment()


            self.state = 90 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 87
                self.define_referenciel_statement()
                self.state = 88
                self.match(WorkflowParser.SEMICOLON)
                self.state = 92 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==10):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Script_fullContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.versionNumber = None # NumberContext

        def NAME(self):
            return self.getToken(WorkflowParser.NAME, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def INCLUDE(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.INCLUDE)
            else:
                return self.getToken(WorkflowParser.INCLUDE, i)

        def CHAR_STRING(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.CHAR_STRING)
            else:
                return self.getToken(WorkflowParser.CHAR_STRING, i)

        def VERSION(self):
            return self.getToken(WorkflowParser.VERSION, 0)

        def concurency(self):
            return self.getTypedRuleContext(WorkflowParser.ConcurencyContext,0)


        def DESCRIPTION(self):
            return self.getToken(WorkflowParser.DESCRIPTION, 0)

        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def MATCHING(self):
            return self.getToken(WorkflowParser.MATCHING, 0)

        def matchings(self):
            return self.getTypedRuleContext(WorkflowParser.MatchingsContext,0)


        def define_referenciel_statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Define_referenciel_statementContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.Define_referenciel_statementContext,i)


        def SEMICOLON(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.SEMICOLON)
            else:
                return self.getToken(WorkflowParser.SEMICOLON, i)

        def initializing(self):
            return self.getTypedRuleContext(WorkflowParser.InitializingContext,0)


        def define_state_statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Define_state_statementContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.Define_state_statementContext,i)


        def number(self):
            return self.getTypedRuleContext(WorkflowParser.NumberContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_script_full

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScript_full" ):
                return visitor.visitScript_full(self)
            else:
                return visitor.visitChildren(self)




    def script_full(self):

        localctx = WorkflowParser.Script_fullContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_script_full)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 98
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==20:
                self.state = 94
                self.match(WorkflowParser.INCLUDE)
                self.state = 95
                self.match(WorkflowParser.CHAR_STRING)
                self.state = 100
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 101
            self.match(WorkflowParser.NAME)
            self.state = 102
            self.key()
            self.state = 105
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==38:
                self.state = 103
                self.match(WorkflowParser.VERSION)
                self.state = 104
                localctx.versionNumber = self.number()


            self.state = 108
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7:
                self.state = 107
                self.concurency()


            self.state = 112
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 110
                self.match(WorkflowParser.DESCRIPTION)
                self.state = 111
                self.comment()


            self.state = 116
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==23:
                self.state = 114
                self.match(WorkflowParser.MATCHING)
                self.state = 115
                self.matchings()


            self.state = 121 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 118
                    self.define_referenciel_statement()
                    self.state = 119
                    self.match(WorkflowParser.SEMICOLON)

                else:
                    raise NoViableAltException(self)
                self.state = 123 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

            self.state = 126
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 125
                self.initializing()


            self.state = 133
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==10:
                self.state = 128
                self.define_state_statement()
                self.state = 129
                self.match(WorkflowParser.SEMICOLON)
                self.state = 135
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConcurencyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.concurencyNumber = None # NumberContext

        def CONCURENCY(self):
            return self.getToken(WorkflowParser.CONCURENCY, 0)

        def number(self):
            return self.getTypedRuleContext(WorkflowParser.NumberContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_concurency

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConcurency" ):
                return visitor.visitConcurency(self)
            else:
                return visitor.visitChildren(self)




    def concurency(self):

        localctx = WorkflowParser.ConcurencyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_concurency)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 136
            self.match(WorkflowParser.CONCURENCY)
            self.state = 137
            localctx.concurencyNumber = self.number()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Define_referenciel_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DEFINE(self):
            return self.getToken(WorkflowParser.DEFINE, 0)

        def event_declaration_statement(self):
            return self.getTypedRuleContext(WorkflowParser.Event_declaration_statementContext,0)


        def rule_declaration_statement(self):
            return self.getTypedRuleContext(WorkflowParser.Rule_declaration_statementContext,0)


        def action_declaration_statement(self):
            return self.getTypedRuleContext(WorkflowParser.Action_declaration_statementContext,0)


        def constant_declaration(self):
            return self.getTypedRuleContext(WorkflowParser.Constant_declarationContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_define_referenciel_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDefine_referenciel_statement" ):
                return visitor.visitDefine_referenciel_statement(self)
            else:
                return visitor.visitChildren(self)




    def define_referenciel_statement(self):

        localctx = WorkflowParser.Define_referenciel_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_define_referenciel_statement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 139
            self.match(WorkflowParser.DEFINE)
            self.state = 144
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [12]:
                self.state = 140
                self.event_declaration_statement()
                pass
            elif token in [30]:
                self.state = 141
                self.rule_declaration_statement()
                pass
            elif token in [1]:
                self.state = 142
                self.action_declaration_statement()
                pass
            elif token in [6]:
                self.state = 143
                self.constant_declaration()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Define_state_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DEFINE(self):
            return self.getToken(WorkflowParser.DEFINE, 0)

        def state_(self):
            return self.getTypedRuleContext(WorkflowParser.StateContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_define_state_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDefine_state_statement" ):
                return visitor.visitDefine_state_statement(self)
            else:
                return visitor.visitChildren(self)




    def define_state_statement(self):

        localctx = WorkflowParser.Define_state_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_define_state_statement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 146
            self.match(WorkflowParser.DEFINE)
            self.state = 147
            self.state_()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Constant_declarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CONST(self):
            return self.getToken(WorkflowParser.CONST, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def value(self):
            return self.getTypedRuleContext(WorkflowParser.ValueContext,0)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_constant_declaration

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstant_declaration" ):
                return visitor.visitConstant_declaration(self)
            else:
                return visitor.visitChildren(self)




    def constant_declaration(self):

        localctx = WorkflowParser.Constant_declarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_constant_declaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 149
            self.match(WorkflowParser.CONST)
            self.state = 150
            self.key()
            self.state = 151
            self.value()
            self.state = 153
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 152
                self.comment()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def string(self):
            return self.getTypedRuleContext(WorkflowParser.StringContext,0)


        def number(self):
            return self.getTypedRuleContext(WorkflowParser.NumberContext,0)


        def delay(self):
            return self.getTypedRuleContext(WorkflowParser.DelayContext,0)


        def REGULAR_ID(self):
            return self.getToken(WorkflowParser.REGULAR_ID, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_value

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitValue" ):
                return visitor.visitValue(self)
            else:
                return visitor.visitChildren(self)




    def value(self):

        localctx = WorkflowParser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_value)
        try:
            self.state = 159
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,13,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 155
                self.string()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 156
                self.number()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 157
                self.delay()
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 158
                self.match(WorkflowParser.REGULAR_ID)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StateContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STATE(self):
            return self.getToken(WorkflowParser.STATE, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def execute(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExecuteContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExecuteContext,i)


        def on_event_statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.On_event_statementContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.On_event_statementContext,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_state

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitState" ):
                return visitor.visitState(self)
            else:
                return visitor.visitChildren(self)




    def state_(self):

        localctx = WorkflowParser.StateContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_state)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 161
            self.match(WorkflowParser.STATE)
            self.state = 162
            self.key()
            self.state = 164
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 163
                self.comment()


            self.state = 169
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,15,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 166
                    self.execute() 
                self.state = 171
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,15,self._ctx)

            self.state = 175
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==17 or _la==27:
                self.state = 172
                self.on_event_statement()
                self.state = 177
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InitializingContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INITIALIZE(self):
            return self.getToken(WorkflowParser.INITIALIZE, 0)

        def WORKFLOW(self):
            return self.getToken(WorkflowParser.WORKFLOW, 0)

        def initializing_item(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Initializing_itemContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.Initializing_itemContext,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_initializing

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInitializing" ):
                return visitor.visitInitializing(self)
            else:
                return visitor.visitChildren(self)




    def initializing(self):

        localctx = WorkflowParser.InitializingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_initializing)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 178
            self.match(WorkflowParser.INITIALIZE)
            self.state = 179
            self.match(WorkflowParser.WORKFLOW)
            self.state = 181 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 180
                self.initializing_item()
                self.state = 183 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==27):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Initializing_itemContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ON(self):
            return self.getToken(WorkflowParser.ON, 0)

        def EVENT(self):
            return self.getToken(WorkflowParser.EVENT, 0)

        def key(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.KeyContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.KeyContext,i)


        def SWITCH(self):
            return self.getToken(WorkflowParser.SWITCH, 0)

        def WHEN(self):
            return self.getToken(WorkflowParser.WHEN, 0)

        def rule_conditions(self):
            return self.getTypedRuleContext(WorkflowParser.Rule_conditionsContext,0)


        def RECURSIVE(self):
            return self.getToken(WorkflowParser.RECURSIVE, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_initializing_item

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInitializing_item" ):
                return visitor.visitInitializing_item(self)
            else:
                return visitor.visitChildren(self)




    def initializing_item(self):

        localctx = WorkflowParser.Initializing_itemContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_initializing_item)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 185
            self.match(WorkflowParser.ON)
            self.state = 186
            self.match(WorkflowParser.EVENT)
            self.state = 187
            self.key()
            self.state = 190
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==41:
                self.state = 188
                self.match(WorkflowParser.WHEN)
                self.state = 189
                self.rule_conditions(0)


            self.state = 193
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==31:
                self.state = 192
                self.match(WorkflowParser.RECURSIVE)


            self.state = 195
            self.match(WorkflowParser.SWITCH)
            self.state = 196
            self.key()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class On_event_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ON(self):
            return self.getToken(WorkflowParser.ON, 0)

        def EVENT(self):
            return self.getToken(WorkflowParser.EVENT, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def EXPIRE(self):
            return self.getToken(WorkflowParser.EXPIRE, 0)

        def AFTER(self):
            return self.getToken(WorkflowParser.AFTER, 0)

        def delay(self):
            return self.getTypedRuleContext(WorkflowParser.DelayContext,0)


        def switch_state(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Switch_stateContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.Switch_stateContext,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_on_event_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOn_event_statement" ):
                return visitor.visitOn_event_statement(self)
            else:
                return visitor.visitChildren(self)




    def on_event_statement(self):

        localctx = WorkflowParser.On_event_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_on_event_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 204
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [27]:
                self.state = 198
                self.match(WorkflowParser.ON)
                self.state = 199
                self.match(WorkflowParser.EVENT)
                self.state = 200
                self.key()
                pass
            elif token in [17]:
                self.state = 201
                self.match(WorkflowParser.EXPIRE)
                self.state = 202
                self.match(WorkflowParser.AFTER)
                self.state = 203
                self.delay()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 207 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 206
                self.switch_state()
                self.state = 209 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & 36031567272878080) != 0)):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Switch_stateContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SWITCH(self):
            return self.getToken(WorkflowParser.SWITCH, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def WHEN(self):
            return self.getToken(WorkflowParser.WHEN, 0)

        def rule_conditions(self):
            return self.getTypedRuleContext(WorkflowParser.Rule_conditionsContext,0)


        def execute2(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Execute2Context)
            else:
                return self.getTypedRuleContext(WorkflowParser.Execute2Context,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_switch_state

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSwitch_state" ):
                return visitor.visitSwitch_state(self)
            else:
                return visitor.visitChildren(self)




    def switch_state(self):

        localctx = WorkflowParser.Switch_stateContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_switch_state)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 213
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,22,self._ctx)
            if la_ == 1:
                self.state = 211
                self.match(WorkflowParser.WHEN)
                self.state = 212
                self.rule_conditions(0)


            self.state = 228
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,25,self._ctx)
            if la_ == 1:
                self.state = 218
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while (((_la) & ~0x3f) == 0 and ((1 << _la) & 36031562977910784) != 0):
                    self.state = 215
                    self.execute2()
                    self.state = 220
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 221
                self.match(WorkflowParser.SWITCH)
                self.state = 222
                self.key()
                pass

            elif la_ == 2:
                self.state = 224 
                self._errHandler.sync(self)
                _alt = 1
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt == 1:
                        self.state = 223
                        self.execute2()

                    else:
                        raise NoViableAltException(self)
                    self.state = 226 
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,24,self._ctx)

                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExecuteContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ON(self):
            return self.getToken(WorkflowParser.ON, 0)

        def execute2(self):
            return self.getTypedRuleContext(WorkflowParser.Execute2Context,0)


        def ENTER(self):
            return self.getToken(WorkflowParser.ENTER, 0)

        def STATE(self):
            return self.getToken(WorkflowParser.STATE, 0)

        def EXIT(self):
            return self.getToken(WorkflowParser.EXIT, 0)

        def AND(self):
            return self.getToken(WorkflowParser.AND, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_execute

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExecute" ):
                return visitor.visitExecute(self)
            else:
                return visitor.visitChildren(self)




    def execute(self):

        localctx = WorkflowParser.ExecuteContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_execute)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 230
            self.match(WorkflowParser.ON)
            self.state = 239
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,26,self._ctx)
            if la_ == 1:
                self.state = 231
                self.match(WorkflowParser.ENTER)
                self.state = 232
                self.match(WorkflowParser.STATE)
                pass

            elif la_ == 2:
                self.state = 233
                self.match(WorkflowParser.EXIT)
                self.state = 234
                self.match(WorkflowParser.STATE)
                pass

            elif la_ == 3:
                self.state = 235
                self.match(WorkflowParser.ENTER)
                self.state = 236
                self.match(WorkflowParser.AND)
                self.state = 237
                self.match(WorkflowParser.EXIT)
                self.state = 238
                self.match(WorkflowParser.STATE)
                pass


            self.state = 241
            self.execute2()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Execute2Context(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHEN(self):
            return self.getToken(WorkflowParser.WHEN, 0)

        def rule_conditions(self):
            return self.getTypedRuleContext(WorkflowParser.Rule_conditionsContext,0)


        def WAITING(self):
            return self.getToken(WorkflowParser.WAITING, 0)

        def delay(self):
            return self.getTypedRuleContext(WorkflowParser.DelayContext,0)


        def BEFORE(self):
            return self.getToken(WorkflowParser.BEFORE, 0)

        def execute3(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Execute3Context)
            else:
                return self.getTypedRuleContext(WorkflowParser.Execute3Context,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_execute2

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExecute2" ):
                return visitor.visitExecute2(self)
            else:
                return visitor.visitChildren(self)




    def execute2(self):

        localctx = WorkflowParser.Execute2Context(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_execute2)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 245
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==41:
                self.state = 243
                self.match(WorkflowParser.WHEN)
                self.state = 244
                self.rule_conditions(0)


            self.state = 251
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==39:
                self.state = 247
                self.match(WorkflowParser.WAITING)
                self.state = 248
                self.delay()
                self.state = 249
                self.match(WorkflowParser.BEFORE)


            self.state = 254 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 253
                    self.execute3()

                else:
                    raise NoViableAltException(self)
                self.state = 256 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,29,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Execute3Context(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EXECUTE(self):
            return self.getToken(WorkflowParser.EXECUTE, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def action(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ActionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ActionContext,i)


        def STORE(self):
            return self.getToken(WorkflowParser.STORE, 0)

        def matchings(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.MatchingsContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.MatchingsContext,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_execute3

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExecute3" ):
                return visitor.visitExecute3(self)
            else:
                return visitor.visitChildren(self)




    def execute3(self):

        localctx = WorkflowParser.Execute3Context(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_execute3)
        self._la = 0 # Token type
        try:
            self.state = 273
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [13, 55]:
                self.enterOuterAlt(localctx, 1)
                self.state = 260
                self._errHandler.sync(self)
                token = self._input.LA(1)
                if token in [13]:
                    self.state = 258
                    self.match(WorkflowParser.EXECUTE)
                    pass
                elif token in [55]:
                    self.state = 259
                    self.key()
                    pass
                else:
                    raise NoViableAltException(self)

                self.state = 263 
                self._errHandler.sync(self)
                _alt = 1
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt == 1:
                        self.state = 262
                        self.action()

                    else:
                        raise NoViableAltException(self)
                    self.state = 265 
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,31,self._ctx)

                pass
            elif token in [34]:
                self.enterOuterAlt(localctx, 2)
                self.state = 267
                self.match(WorkflowParser.STORE)
                self.state = 269 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 268
                    self.matchings()
                    self.state = 271 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==44):
                        break

                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MatchingsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)

        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def matching(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.MatchingContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.MatchingContext,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_matchings

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMatchings" ):
                return visitor.visitMatchings(self)
            else:
                return visitor.visitChildren(self)




    def matchings(self):

        localctx = WorkflowParser.MatchingsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_matchings)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 275
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 277 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 276
                self.matching()
                self.state = 279 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==55):
                    break

            self.state = 281
            self.match(WorkflowParser.RIGHT_PAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MatchingContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def EQUAL(self):
            return self.getToken(WorkflowParser.EQUAL, 0)

        def string(self):
            return self.getTypedRuleContext(WorkflowParser.StringContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_matching

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMatching" ):
                return visitor.visitMatching(self)
            else:
                return visitor.visitChildren(self)




    def matching(self):

        localctx = WorkflowParser.MatchingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_matching)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 283
            self.key()
            self.state = 284
            self.match(WorkflowParser.EQUAL)
            self.state = 285
            self.string()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ActionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)

        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def arguments(self):
            return self.getTypedRuleContext(WorkflowParser.ArgumentsContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_action

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAction" ):
                return visitor.visitAction(self)
            else:
                return visitor.visitChildren(self)




    def action(self):

        localctx = WorkflowParser.ActionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_action)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 287
            self.key()
            self.state = 288
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 290
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==55:
                self.state = 289
                self.arguments()


            self.state = 292
            self.match(WorkflowParser.RIGHT_PAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def argument(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ArgumentContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ArgumentContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.COMMA)
            else:
                return self.getToken(WorkflowParser.COMMA, i)

        def getRuleIndex(self):
            return WorkflowParser.RULE_arguments

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArguments" ):
                return visitor.visitArguments(self)
            else:
                return visitor.visitChildren(self)




    def arguments(self):

        localctx = WorkflowParser.ArgumentsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_arguments)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 294
            self.argument()
            self.state = 299
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==48:
                self.state = 295
                self.match(WorkflowParser.COMMA)
                self.state = 296
                self.argument()
                self.state = 301
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def EQUAL(self):
            return self.getToken(WorkflowParser.EQUAL, 0)

        def argumentValue(self):
            return self.getTypedRuleContext(WorkflowParser.ArgumentValueContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_argument

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArgument" ):
                return visitor.visitArgument(self)
            else:
                return visitor.visitChildren(self)




    def argument(self):

        localctx = WorkflowParser.ArgumentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_argument)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 302
            self.key()
            self.state = 303
            self.match(WorkflowParser.EQUAL)
            self.state = 304
            self.argumentValue()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def string(self):
            return self.getTypedRuleContext(WorkflowParser.StringContext,0)


        def compositekey(self):
            return self.getTypedRuleContext(WorkflowParser.CompositekeyContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_argumentValue

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArgumentValue" ):
                return visitor.visitArgumentValue(self)
            else:
                return visitor.visitChildren(self)




    def argumentValue(self):

        localctx = WorkflowParser.ArgumentValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_argumentValue)
        try:
            self.state = 308
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [43]:
                self.enterOuterAlt(localctx, 1)
                self.state = 306
                self.string()
                pass
            elif token in [50, 55]:
                self.enterOuterAlt(localctx, 2)
                self.state = 307
                self.compositekey()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Rule_conditionsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)

        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def arguments(self):
            return self.getTypedRuleContext(WorkflowParser.ArgumentsContext,0)


        def NOT(self):
            return self.getToken(WorkflowParser.NOT, 0)

        def rule_conditions(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.Rule_conditionsContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.Rule_conditionsContext,i)


        def AND(self):
            return self.getToken(WorkflowParser.AND, 0)

        def OR(self):
            return self.getToken(WorkflowParser.OR, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_rule_conditions

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule_conditions" ):
                return visitor.visitRule_conditions(self)
            else:
                return visitor.visitChildren(self)



    def rule_conditions(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = WorkflowParser.Rule_conditionsContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 44
        self.enterRecursionRule(localctx, 44, self.RULE_rule_conditions, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 324
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [55]:
                self.state = 311
                self.key()
                self.state = 312
                self.match(WorkflowParser.LEFT_PAREN)
                self.state = 314
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==55:
                    self.state = 313
                    self.arguments()


                self.state = 316
                self.match(WorkflowParser.RIGHT_PAREN)
                pass
            elif token in [26]:
                self.state = 318
                self.match(WorkflowParser.NOT)
                self.state = 319
                self.rule_conditions(4)
                pass
            elif token in [44]:
                self.state = 320
                self.match(WorkflowParser.LEFT_PAREN)
                self.state = 321
                self.rule_conditions(0)
                self.state = 322
                self.match(WorkflowParser.RIGHT_PAREN)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 334
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,41,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 332
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,40,self._ctx)
                    if la_ == 1:
                        localctx = WorkflowParser.Rule_conditionsContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_rule_conditions)
                        self.state = 326
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 327
                        self.match(WorkflowParser.AND)
                        self.state = 328
                        self.rule_conditions(4)
                        pass

                    elif la_ == 2:
                        localctx = WorkflowParser.Rule_conditionsContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_rule_conditions)
                        self.state = 329
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 330
                        self.match(WorkflowParser.OR)
                        self.state = 331
                        self.rule_conditions(3)
                        pass

             
                self.state = 336
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,41,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class Event_declaration_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.schemaRef = None # CompositekeyContext

        def EVENT(self):
            return self.getToken(WorkflowParser.EVENT, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def AS(self):
            return self.getToken(WorkflowParser.AS, 0)

        def UNIQUE(self):
            return self.getToken(WorkflowParser.UNIQUE, 0)

        def unique_keys(self):
            return self.getTypedRuleContext(WorkflowParser.Unique_keysContext,0)


        def compositekey(self):
            return self.getTypedRuleContext(WorkflowParser.CompositekeyContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_event_declaration_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEvent_declaration_statement" ):
                return visitor.visitEvent_declaration_statement(self)
            else:
                return visitor.visitChildren(self)




    def event_declaration_statement(self):

        localctx = WorkflowParser.Event_declaration_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_event_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 337
            self.match(WorkflowParser.EVENT)
            self.state = 338
            self.key()
            self.state = 340
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 339
                self.comment()


            self.state = 344
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==4:
                self.state = 342
                self.match(WorkflowParser.AS)
                self.state = 343
                localctx.schemaRef = self.compositekey()


            self.state = 348
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==37:
                self.state = 346
                self.match(WorkflowParser.UNIQUE)
                self.state = 347
                self.unique_keys()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Unique_keysContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)

        def key(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.KeyContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.KeyContext,i)


        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.COMMA)
            else:
                return self.getToken(WorkflowParser.COMMA, i)

        def getRuleIndex(self):
            return WorkflowParser.RULE_unique_keys

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnique_keys" ):
                return visitor.visitUnique_keys(self)
            else:
                return visitor.visitChildren(self)




    def unique_keys(self):

        localctx = WorkflowParser.Unique_keysContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_unique_keys)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 350
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 351
            self.key()
            self.state = 356
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==48:
                self.state = 352
                self.match(WorkflowParser.COMMA)
                self.state = 353
                self.key()
                self.state = 358
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 359
            self.match(WorkflowParser.RIGHT_PAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Action_declaration_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ACTION(self):
            return self.getToken(WorkflowParser.ACTION, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)

        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def parameters(self):
            return self.getTypedRuleContext(WorkflowParser.ParametersContext,0)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_action_declaration_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAction_declaration_statement" ):
                return visitor.visitAction_declaration_statement(self)
            else:
                return visitor.visitChildren(self)




    def action_declaration_statement(self):

        localctx = WorkflowParser.Action_declaration_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_action_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 361
            self.match(WorkflowParser.ACTION)
            self.state = 362
            self.key()
            self.state = 363
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 365
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 34363934720) != 0):
                self.state = 364
                self.parameters()


            self.state = 367
            self.match(WorkflowParser.RIGHT_PAREN)
            self.state = 369
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 368
                self.comment()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Rule_declaration_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RULE(self):
            return self.getToken(WorkflowParser.RULE, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)

        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def parameters(self):
            return self.getTypedRuleContext(WorkflowParser.ParametersContext,0)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_rule_declaration_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule_declaration_statement" ):
                return visitor.visitRule_declaration_statement(self)
            else:
                return visitor.visitChildren(self)




    def rule_declaration_statement(self):

        localctx = WorkflowParser.Rule_declaration_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_rule_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 371
            self.match(WorkflowParser.RULE)
            self.state = 372
            self.key()
            self.state = 373
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 375
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 34363934720) != 0):
                self.state = 374
                self.parameters()


            self.state = 377
            self.match(WorkflowParser.RIGHT_PAREN)
            self.state = 379
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 378
                self.comment()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParametersContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def parameter(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ParameterContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ParameterContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.COMMA)
            else:
                return self.getToken(WorkflowParser.COMMA, i)

        def getRuleIndex(self):
            return WorkflowParser.RULE_parameters

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParameters" ):
                return visitor.visitParameters(self)
            else:
                return visitor.visitChildren(self)




    def parameters(self):

        localctx = WorkflowParser.ParametersContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_parameters)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 381
            self.parameter()
            self.state = 386
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==48:
                self.state = 382
                self.match(WorkflowParser.COMMA)
                self.state = 383
                self.parameter()
                self.state = 388
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParameterContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def type_(self):
            return self.getTypedRuleContext(WorkflowParser.TypeContext,0)


        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_parameter

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParameter" ):
                return visitor.visitParameter(self)
            else:
                return visitor.visitChildren(self)




    def parameter(self):

        localctx = WorkflowParser.ParameterContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_parameter)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 389
            self.type_()
            self.state = 390
            self.key()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TEXT(self):
            return self.getToken(WorkflowParser.TEXT, 0)

        def INTEGER(self):
            return self.getToken(WorkflowParser.INTEGER, 0)

        def DECIMAL(self):
            return self.getToken(WorkflowParser.DECIMAL, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_type

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitType" ):
                return visitor.visitType(self)
            else:
                return visitor.visitChildren(self)




    def type_(self):

        localctx = WorkflowParser.TypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_type)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 392
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 34363934720) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class KeyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def REGULAR_ID(self):
            return self.getToken(WorkflowParser.REGULAR_ID, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_key

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitKey" ):
                return visitor.visitKey(self)
            else:
                return visitor.visitChildren(self)




    def key(self):

        localctx = WorkflowParser.KeyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_key)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 394
            self.match(WorkflowParser.REGULAR_ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CompositekeyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def key(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.KeyContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.KeyContext,i)


        def AROBASE(self):
            return self.getToken(WorkflowParser.AROBASE, 0)

        def DOT(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.DOT)
            else:
                return self.getToken(WorkflowParser.DOT, i)

        def getRuleIndex(self):
            return WorkflowParser.RULE_compositekey

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompositekey" ):
                return visitor.visitCompositekey(self)
            else:
                return visitor.visitChildren(self)




    def compositekey(self):

        localctx = WorkflowParser.CompositekeyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 62, self.RULE_compositekey)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 397
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 396
                self.match(WorkflowParser.AROBASE)


            self.state = 399
            self.key()
            self.state = 404
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==49:
                self.state = 400
                self.match(WorkflowParser.DOT)
                self.state = 401
                self.key()
                self.state = 406
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CommentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CHAR_STRING(self):
            return self.getToken(WorkflowParser.CHAR_STRING, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_comment

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComment" ):
                return visitor.visitComment(self)
            else:
                return visitor.visitChildren(self)




    def comment(self):

        localctx = WorkflowParser.CommentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_comment)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 407
            self.match(WorkflowParser.CHAR_STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(WorkflowParser.NUMBER, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_number

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumber" ):
                return visitor.visitNumber(self)
            else:
                return visitor.visitChildren(self)




    def number(self):

        localctx = WorkflowParser.NumberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 66, self.RULE_number)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 409
            self.match(WorkflowParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumericContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def number(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.NumberContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.NumberContext,i)


        def DOT(self):
            return self.getToken(WorkflowParser.DOT, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_numeric

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumeric" ):
                return visitor.visitNumeric(self)
            else:
                return visitor.visitChildren(self)




    def numeric(self):

        localctx = WorkflowParser.NumericContext(self, self._ctx, self.state)
        self.enterRule(localctx, 68, self.RULE_numeric)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 411
            self.number()
            self.state = 412
            self.match(WorkflowParser.DOT)
            self.state = 413
            self.number()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StringContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CHAR_STRING(self):
            return self.getToken(WorkflowParser.CHAR_STRING, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_string

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitString" ):
                return visitor.visitString(self)
            else:
                return visitor.visitChildren(self)




    def string(self):

        localctx = WorkflowParser.StringContext(self, self._ctx, self.state)
        self.enterRule(localctx, 70, self.RULE_string)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 415
            self.match(WorkflowParser.CHAR_STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DelayContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def number(self):
            return self.getTypedRuleContext(WorkflowParser.NumberContext,0)


        def MINUTE(self):
            return self.getToken(WorkflowParser.MINUTE, 0)

        def HOUR(self):
            return self.getToken(WorkflowParser.HOUR, 0)

        def DAY(self):
            return self.getToken(WorkflowParser.DAY, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_delay

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDelay" ):
                return visitor.visitDelay(self)
            else:
                return visitor.visitChildren(self)




    def delay(self):

        localctx = WorkflowParser.DelayContext(self, self._ctx, self.state)
        self.enterRule(localctx, 72, self.RULE_delay)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 417
            self.number()
            self.state = 418
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 17302016) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[22] = self.rule_conditions_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def rule_conditions_sempred(self, localctx:Rule_conditionsContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 3)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 2)
         




