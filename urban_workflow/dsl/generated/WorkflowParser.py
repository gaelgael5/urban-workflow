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
        4,1,73,561,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,33,
        7,33,2,34,7,34,2,35,7,35,2,36,7,36,2,37,7,37,2,38,7,38,2,39,7,39,
        2,40,7,40,2,41,7,41,2,42,7,42,1,0,1,0,1,0,1,0,3,0,91,8,0,1,1,1,1,
        1,1,1,1,1,1,3,1,98,8,1,1,1,1,1,1,1,4,1,103,8,1,11,1,12,1,104,1,2,
        1,2,5,2,109,8,2,10,2,12,2,112,9,2,1,2,1,2,1,2,1,2,3,2,118,8,2,1,
        2,3,2,121,8,2,1,2,1,2,3,2,125,8,2,1,2,1,2,3,2,129,8,2,1,2,1,2,1,
        2,5,2,134,8,2,10,2,12,2,137,9,2,1,2,3,2,140,8,2,1,2,1,2,1,2,5,2,
        145,8,2,10,2,12,2,148,9,2,1,3,1,3,1,3,1,4,1,4,1,4,1,4,1,4,1,4,3,
        4,159,8,4,1,5,1,5,1,5,1,6,1,6,1,6,1,6,3,6,168,8,6,1,7,1,7,1,7,1,
        7,3,7,174,8,7,1,8,1,8,1,8,3,8,179,8,8,1,8,1,8,3,8,183,8,8,1,8,5,
        8,186,8,8,10,8,12,8,189,9,8,1,8,5,8,192,8,8,10,8,12,8,195,9,8,1,
        9,1,9,1,9,4,9,200,8,9,11,9,12,9,201,1,10,1,10,1,10,1,10,1,10,3,10,
        209,8,10,1,10,3,10,212,8,10,1,10,1,10,1,10,1,11,1,11,1,11,1,11,1,
        11,1,11,3,11,223,8,11,1,11,4,11,226,8,11,11,11,12,11,227,1,12,1,
        12,3,12,232,8,12,1,12,5,12,235,8,12,10,12,12,12,238,9,12,1,12,1,
        12,1,12,4,12,243,8,12,11,12,12,12,244,3,12,247,8,12,1,13,1,13,1,
        13,1,13,1,13,1,13,1,13,1,13,1,13,3,13,258,8,13,1,13,1,13,1,14,1,
        14,3,14,264,8,14,1,14,1,14,1,14,1,14,3,14,270,8,14,1,14,4,14,273,
        8,14,11,14,12,14,274,1,15,1,15,3,15,279,8,15,1,15,4,15,282,8,15,
        11,15,12,15,283,1,15,1,15,4,15,288,8,15,11,15,12,15,289,3,15,292,
        8,15,1,16,1,16,4,16,296,8,16,11,16,12,16,297,1,16,1,16,1,17,1,17,
        1,17,1,17,1,18,1,18,1,18,3,18,309,8,18,1,18,1,18,1,19,1,19,1,19,
        5,19,316,8,19,10,19,12,19,319,9,19,1,20,1,20,1,20,1,20,1,21,1,21,
        1,21,3,21,328,8,21,1,22,1,22,1,22,5,22,333,8,22,10,22,12,22,336,
        9,22,1,23,1,23,1,23,1,23,1,23,1,23,1,23,1,23,3,23,346,8,23,1,24,
        1,24,1,24,1,24,3,24,352,8,24,1,24,1,24,1,24,1,24,1,24,1,24,1,24,
        1,24,3,24,362,8,24,1,24,1,24,1,24,1,24,1,24,1,24,5,24,370,8,24,10,
        24,12,24,373,9,24,1,25,1,25,1,25,3,25,378,8,25,1,25,1,25,3,25,382,
        8,25,1,25,1,25,3,25,386,8,25,1,26,1,26,1,26,1,26,5,26,392,8,26,10,
        26,12,26,395,9,26,1,26,1,26,1,27,1,27,1,27,1,27,3,27,403,8,27,1,
        27,1,27,3,27,407,8,27,1,27,1,27,3,27,411,8,27,1,28,1,28,1,28,3,28,
        416,8,28,1,28,1,28,3,28,420,8,28,1,28,1,28,1,28,1,29,1,29,1,29,1,
        29,3,29,429,8,29,1,29,1,29,3,29,433,8,29,1,29,1,29,3,29,437,8,29,
        1,30,1,30,3,30,441,8,30,1,30,1,30,1,31,1,31,1,31,1,31,1,31,1,31,
        3,31,451,8,31,1,31,1,31,1,31,1,31,1,31,1,31,1,31,1,31,1,31,1,31,
        1,31,1,31,1,31,1,31,1,31,1,31,1,31,3,31,470,8,31,1,31,1,31,1,31,
        1,31,1,31,5,31,477,8,31,10,31,12,31,480,9,31,1,31,1,31,1,31,1,31,
        1,31,3,31,487,8,31,1,31,5,31,490,8,31,10,31,12,31,493,9,31,1,32,
        1,32,1,32,1,32,1,32,1,32,1,32,1,32,1,32,1,32,1,32,5,32,506,8,32,
        10,32,12,32,509,9,32,3,32,511,8,32,1,32,1,32,1,32,1,32,1,32,1,32,
        1,32,3,32,520,8,32,1,33,1,33,1,33,5,33,525,8,33,10,33,12,33,528,
        9,33,1,34,1,34,1,34,1,35,1,35,1,36,1,36,1,37,3,37,538,8,37,1,37,
        1,37,1,37,5,37,543,8,37,10,37,12,37,546,9,37,1,38,1,38,1,39,1,39,
        1,40,1,40,1,40,1,40,1,41,1,41,1,42,1,42,1,42,1,42,0,2,48,62,43,0,
        2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,
        48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,80,82,84,0,6,1,0,
        67,68,1,0,65,66,2,0,16,16,60,64,2,0,19,19,42,42,3,0,12,12,25,25,
        40,40,3,0,10,10,21,21,28,28,609,0,90,1,0,0,0,2,92,1,0,0,0,4,110,
        1,0,0,0,6,149,1,0,0,0,8,152,1,0,0,0,10,160,1,0,0,0,12,163,1,0,0,
        0,14,173,1,0,0,0,16,175,1,0,0,0,18,196,1,0,0,0,20,203,1,0,0,0,22,
        222,1,0,0,0,24,231,1,0,0,0,26,248,1,0,0,0,28,263,1,0,0,0,30,291,
        1,0,0,0,32,293,1,0,0,0,34,301,1,0,0,0,36,305,1,0,0,0,38,312,1,0,
        0,0,40,320,1,0,0,0,42,327,1,0,0,0,44,329,1,0,0,0,46,345,1,0,0,0,
        48,361,1,0,0,0,50,374,1,0,0,0,52,387,1,0,0,0,54,398,1,0,0,0,56,412,
        1,0,0,0,58,424,1,0,0,0,60,438,1,0,0,0,62,450,1,0,0,0,64,519,1,0,
        0,0,66,521,1,0,0,0,68,529,1,0,0,0,70,532,1,0,0,0,72,534,1,0,0,0,
        74,537,1,0,0,0,76,547,1,0,0,0,78,549,1,0,0,0,80,551,1,0,0,0,82,555,
        1,0,0,0,84,557,1,0,0,0,86,91,3,2,1,0,87,88,3,4,2,0,88,89,5,0,0,1,
        89,91,1,0,0,0,90,86,1,0,0,0,90,87,1,0,0,0,91,1,1,0,0,0,92,93,5,20,
        0,0,93,94,5,29,0,0,94,97,3,72,36,0,95,96,5,9,0,0,96,98,3,76,38,0,
        97,95,1,0,0,0,97,98,1,0,0,0,98,102,1,0,0,0,99,100,3,8,4,0,100,101,
        5,53,0,0,101,103,1,0,0,0,102,99,1,0,0,0,103,104,1,0,0,0,104,102,
        1,0,0,0,104,105,1,0,0,0,105,3,1,0,0,0,106,107,5,23,0,0,107,109,5,
        50,0,0,108,106,1,0,0,0,109,112,1,0,0,0,110,108,1,0,0,0,110,111,1,
        0,0,0,111,113,1,0,0,0,112,110,1,0,0,0,113,114,5,29,0,0,114,117,3,
        72,36,0,115,116,5,45,0,0,116,118,3,78,39,0,117,115,1,0,0,0,117,118,
        1,0,0,0,118,120,1,0,0,0,119,121,3,6,3,0,120,119,1,0,0,0,120,121,
        1,0,0,0,121,124,1,0,0,0,122,123,5,9,0,0,123,125,3,76,38,0,124,122,
        1,0,0,0,124,125,1,0,0,0,125,128,1,0,0,0,126,127,5,27,0,0,127,129,
        3,32,16,0,128,126,1,0,0,0,128,129,1,0,0,0,129,135,1,0,0,0,130,131,
        3,8,4,0,131,132,5,53,0,0,132,134,1,0,0,0,133,130,1,0,0,0,134,137,
        1,0,0,0,135,133,1,0,0,0,135,136,1,0,0,0,136,139,1,0,0,0,137,135,
        1,0,0,0,138,140,3,18,9,0,139,138,1,0,0,0,139,140,1,0,0,0,140,146,
        1,0,0,0,141,142,3,10,5,0,142,143,5,53,0,0,143,145,1,0,0,0,144,141,
        1,0,0,0,145,148,1,0,0,0,146,144,1,0,0,0,146,147,1,0,0,0,147,5,1,
        0,0,0,148,146,1,0,0,0,149,150,5,8,0,0,150,151,3,78,39,0,151,7,1,
        0,0,0,152,158,5,11,0,0,153,159,3,50,25,0,154,159,3,58,29,0,155,159,
        3,54,27,0,156,159,3,56,28,0,157,159,3,12,6,0,158,153,1,0,0,0,158,
        154,1,0,0,0,158,155,1,0,0,0,158,156,1,0,0,0,158,157,1,0,0,0,159,
        9,1,0,0,0,160,161,5,11,0,0,161,162,3,16,8,0,162,11,1,0,0,0,163,164,
        5,7,0,0,164,165,3,72,36,0,165,167,3,14,7,0,166,168,3,76,38,0,167,
        166,1,0,0,0,167,168,1,0,0,0,168,13,1,0,0,0,169,174,3,82,41,0,170,
        174,3,78,39,0,171,174,3,84,42,0,172,174,5,73,0,0,173,169,1,0,0,0,
        173,170,1,0,0,0,173,171,1,0,0,0,173,172,1,0,0,0,174,15,1,0,0,0,175,
        176,5,38,0,0,176,178,3,72,36,0,177,179,3,76,38,0,178,177,1,0,0,0,
        178,179,1,0,0,0,179,182,1,0,0,0,180,181,5,5,0,0,181,183,3,74,37,
        0,182,180,1,0,0,0,182,183,1,0,0,0,183,187,1,0,0,0,184,186,3,26,13,
        0,185,184,1,0,0,0,186,189,1,0,0,0,187,185,1,0,0,0,187,188,1,0,0,
        0,188,193,1,0,0,0,189,187,1,0,0,0,190,192,3,22,11,0,191,190,1,0,
        0,0,192,195,1,0,0,0,193,191,1,0,0,0,193,194,1,0,0,0,194,17,1,0,0,
        0,195,193,1,0,0,0,196,197,5,24,0,0,197,199,5,49,0,0,198,200,3,20,
        10,0,199,198,1,0,0,0,200,201,1,0,0,0,201,199,1,0,0,0,201,202,1,0,
        0,0,202,19,1,0,0,0,203,204,5,32,0,0,204,205,5,13,0,0,205,208,3,72,
        36,0,206,207,5,48,0,0,207,209,3,48,24,0,208,206,1,0,0,0,208,209,
        1,0,0,0,209,211,1,0,0,0,210,212,5,36,0,0,211,210,1,0,0,0,211,212,
        1,0,0,0,212,213,1,0,0,0,213,214,5,37,0,0,214,215,3,72,36,0,215,21,
        1,0,0,0,216,217,5,32,0,0,217,218,5,13,0,0,218,223,3,72,36,0,219,
        220,5,18,0,0,220,221,5,2,0,0,221,223,3,84,42,0,222,216,1,0,0,0,222,
        219,1,0,0,0,223,225,1,0,0,0,224,226,3,24,12,0,225,224,1,0,0,0,226,
        227,1,0,0,0,227,225,1,0,0,0,227,228,1,0,0,0,228,23,1,0,0,0,229,230,
        5,48,0,0,230,232,3,48,24,0,231,229,1,0,0,0,231,232,1,0,0,0,232,246,
        1,0,0,0,233,235,3,28,14,0,234,233,1,0,0,0,235,238,1,0,0,0,236,234,
        1,0,0,0,236,237,1,0,0,0,237,239,1,0,0,0,238,236,1,0,0,0,239,240,
        5,37,0,0,240,247,3,72,36,0,241,243,3,28,14,0,242,241,1,0,0,0,243,
        244,1,0,0,0,244,242,1,0,0,0,244,245,1,0,0,0,245,247,1,0,0,0,246,
        236,1,0,0,0,246,242,1,0,0,0,247,25,1,0,0,0,248,257,5,32,0,0,249,
        250,5,15,0,0,250,258,5,38,0,0,251,252,5,17,0,0,252,258,5,38,0,0,
        253,254,5,15,0,0,254,255,5,3,0,0,255,256,5,17,0,0,256,258,5,38,0,
        0,257,249,1,0,0,0,257,251,1,0,0,0,257,253,1,0,0,0,258,259,1,0,0,
        0,259,260,3,28,14,0,260,27,1,0,0,0,261,262,5,48,0,0,262,264,3,48,
        24,0,263,261,1,0,0,0,263,264,1,0,0,0,264,269,1,0,0,0,265,266,5,46,
        0,0,266,267,3,84,42,0,267,268,5,6,0,0,268,270,1,0,0,0,269,265,1,
        0,0,0,269,270,1,0,0,0,270,272,1,0,0,0,271,273,3,30,15,0,272,271,
        1,0,0,0,273,274,1,0,0,0,274,272,1,0,0,0,274,275,1,0,0,0,275,29,1,
        0,0,0,276,279,5,14,0,0,277,279,3,72,36,0,278,276,1,0,0,0,278,277,
        1,0,0,0,279,281,1,0,0,0,280,282,3,36,18,0,281,280,1,0,0,0,282,283,
        1,0,0,0,283,281,1,0,0,0,283,284,1,0,0,0,284,292,1,0,0,0,285,287,
        5,39,0,0,286,288,3,32,16,0,287,286,1,0,0,0,288,289,1,0,0,0,289,287,
        1,0,0,0,289,290,1,0,0,0,290,292,1,0,0,0,291,278,1,0,0,0,291,285,
        1,0,0,0,292,31,1,0,0,0,293,295,5,51,0,0,294,296,3,34,17,0,295,294,
        1,0,0,0,296,297,1,0,0,0,297,295,1,0,0,0,297,298,1,0,0,0,298,299,
        1,0,0,0,299,300,5,52,0,0,300,33,1,0,0,0,301,302,3,72,36,0,302,303,
        5,16,0,0,303,304,3,82,41,0,304,35,1,0,0,0,305,306,3,72,36,0,306,
        308,5,51,0,0,307,309,3,38,19,0,308,307,1,0,0,0,308,309,1,0,0,0,309,
        310,1,0,0,0,310,311,5,52,0,0,311,37,1,0,0,0,312,317,3,40,20,0,313,
        314,5,55,0,0,314,316,3,40,20,0,315,313,1,0,0,0,316,319,1,0,0,0,317,
        315,1,0,0,0,317,318,1,0,0,0,318,39,1,0,0,0,319,317,1,0,0,0,320,321,
        3,72,36,0,321,322,5,16,0,0,322,323,3,42,21,0,323,41,1,0,0,0,324,
        328,3,82,41,0,325,328,3,44,22,0,326,328,3,74,37,0,327,324,1,0,0,
        0,327,325,1,0,0,0,327,326,1,0,0,0,328,43,1,0,0,0,329,330,5,57,0,
        0,330,334,3,72,36,0,331,333,3,46,23,0,332,331,1,0,0,0,333,336,1,
        0,0,0,334,332,1,0,0,0,334,335,1,0,0,0,335,45,1,0,0,0,336,334,1,0,
        0,0,337,338,5,56,0,0,338,346,3,72,36,0,339,340,5,58,0,0,340,341,
        5,70,0,0,341,346,5,59,0,0,342,343,5,58,0,0,343,344,5,50,0,0,344,
        346,5,59,0,0,345,337,1,0,0,0,345,339,1,0,0,0,345,342,1,0,0,0,346,
        47,1,0,0,0,347,348,6,24,-1,0,348,349,3,72,36,0,349,351,5,51,0,0,
        350,352,3,38,19,0,351,350,1,0,0,0,351,352,1,0,0,0,352,353,1,0,0,
        0,353,354,5,52,0,0,354,362,1,0,0,0,355,356,5,30,0,0,356,362,3,48,
        24,4,357,358,5,51,0,0,358,359,3,48,24,0,359,360,5,52,0,0,360,362,
        1,0,0,0,361,347,1,0,0,0,361,355,1,0,0,0,361,357,1,0,0,0,362,371,
        1,0,0,0,363,364,10,3,0,0,364,365,5,3,0,0,365,370,3,48,24,4,366,367,
        10,2,0,0,367,368,5,33,0,0,368,370,3,48,24,3,369,363,1,0,0,0,369,
        366,1,0,0,0,370,373,1,0,0,0,371,369,1,0,0,0,371,372,1,0,0,0,372,
        49,1,0,0,0,373,371,1,0,0,0,374,375,5,13,0,0,375,377,3,72,36,0,376,
        378,3,76,38,0,377,376,1,0,0,0,377,378,1,0,0,0,378,381,1,0,0,0,379,
        380,5,5,0,0,380,382,3,74,37,0,381,379,1,0,0,0,381,382,1,0,0,0,382,
        385,1,0,0,0,383,384,5,43,0,0,384,386,3,52,26,0,385,383,1,0,0,0,385,
        386,1,0,0,0,386,51,1,0,0,0,387,388,5,51,0,0,388,393,3,72,36,0,389,
        390,5,55,0,0,390,392,3,72,36,0,391,389,1,0,0,0,392,395,1,0,0,0,393,
        391,1,0,0,0,393,394,1,0,0,0,394,396,1,0,0,0,395,393,1,0,0,0,396,
        397,5,52,0,0,397,53,1,0,0,0,398,399,5,1,0,0,399,400,3,72,36,0,400,
        402,5,51,0,0,401,403,3,66,33,0,402,401,1,0,0,0,402,403,1,0,0,0,403,
        404,1,0,0,0,404,406,5,52,0,0,405,407,3,76,38,0,406,405,1,0,0,0,406,
        407,1,0,0,0,407,410,1,0,0,0,408,409,5,5,0,0,409,411,3,74,37,0,410,
        408,1,0,0,0,410,411,1,0,0,0,411,55,1,0,0,0,412,413,5,4,0,0,413,415,
        3,72,36,0,414,416,3,76,38,0,415,414,1,0,0,0,415,416,1,0,0,0,416,
        419,1,0,0,0,417,418,5,5,0,0,418,420,3,74,37,0,419,417,1,0,0,0,419,
        420,1,0,0,0,420,421,1,0,0,0,421,422,5,44,0,0,422,423,3,74,37,0,423,
        57,1,0,0,0,424,425,5,35,0,0,425,426,3,72,36,0,426,428,5,51,0,0,427,
        429,3,66,33,0,428,427,1,0,0,0,428,429,1,0,0,0,429,430,1,0,0,0,430,
        432,5,52,0,0,431,433,3,76,38,0,432,431,1,0,0,0,432,433,1,0,0,0,433,
        436,1,0,0,0,434,435,5,5,0,0,435,437,3,74,37,0,436,434,1,0,0,0,436,
        437,1,0,0,0,437,59,1,0,0,0,438,440,3,62,31,0,439,441,5,53,0,0,440,
        439,1,0,0,0,440,441,1,0,0,0,441,442,1,0,0,0,442,443,5,0,0,1,443,
        61,1,0,0,0,444,445,6,31,-1,0,445,446,5,66,0,0,446,451,3,62,31,10,
        447,448,5,30,0,0,448,451,3,62,31,4,449,451,3,64,32,0,450,444,1,0,
        0,0,450,447,1,0,0,0,450,449,1,0,0,0,451,491,1,0,0,0,452,453,10,9,
        0,0,453,454,7,0,0,0,454,490,3,62,31,10,455,456,10,8,0,0,456,457,
        7,1,0,0,457,490,3,62,31,9,458,459,10,7,0,0,459,460,7,2,0,0,460,490,
        3,62,31,8,461,462,10,3,0,0,462,463,5,3,0,0,463,490,3,62,31,4,464,
        465,10,2,0,0,465,466,5,33,0,0,466,490,3,62,31,3,467,469,10,6,0,0,
        468,470,5,30,0,0,469,468,1,0,0,0,469,470,1,0,0,0,470,471,1,0,0,0,
        471,472,5,22,0,0,472,473,5,51,0,0,473,478,3,62,31,0,474,475,5,55,
        0,0,475,477,3,62,31,0,476,474,1,0,0,0,477,480,1,0,0,0,478,476,1,
        0,0,0,478,479,1,0,0,0,479,481,1,0,0,0,480,478,1,0,0,0,481,482,5,
        52,0,0,482,490,1,0,0,0,483,484,10,5,0,0,484,486,5,26,0,0,485,487,
        5,30,0,0,486,485,1,0,0,0,486,487,1,0,0,0,487,488,1,0,0,0,488,490,
        5,31,0,0,489,452,1,0,0,0,489,455,1,0,0,0,489,458,1,0,0,0,489,461,
        1,0,0,0,489,464,1,0,0,0,489,467,1,0,0,0,489,483,1,0,0,0,490,493,
        1,0,0,0,491,489,1,0,0,0,491,492,1,0,0,0,492,63,1,0,0,0,493,491,1,
        0,0,0,494,520,3,80,40,0,495,520,3,78,39,0,496,520,3,82,41,0,497,
        520,7,3,0,0,498,520,5,31,0,0,499,520,3,44,22,0,500,501,3,72,36,0,
        501,510,5,51,0,0,502,507,3,62,31,0,503,504,5,55,0,0,504,506,3,62,
        31,0,505,503,1,0,0,0,506,509,1,0,0,0,507,505,1,0,0,0,507,508,1,0,
        0,0,508,511,1,0,0,0,509,507,1,0,0,0,510,502,1,0,0,0,510,511,1,0,
        0,0,511,512,1,0,0,0,512,513,5,52,0,0,513,520,1,0,0,0,514,520,3,72,
        36,0,515,516,5,51,0,0,516,517,3,62,31,0,517,518,5,52,0,0,518,520,
        1,0,0,0,519,494,1,0,0,0,519,495,1,0,0,0,519,496,1,0,0,0,519,497,
        1,0,0,0,519,498,1,0,0,0,519,499,1,0,0,0,519,500,1,0,0,0,519,514,
        1,0,0,0,519,515,1,0,0,0,520,65,1,0,0,0,521,526,3,68,34,0,522,523,
        5,55,0,0,523,525,3,68,34,0,524,522,1,0,0,0,525,528,1,0,0,0,526,524,
        1,0,0,0,526,527,1,0,0,0,527,67,1,0,0,0,528,526,1,0,0,0,529,530,3,
        70,35,0,530,531,3,72,36,0,531,69,1,0,0,0,532,533,7,4,0,0,533,71,
        1,0,0,0,534,535,5,73,0,0,535,73,1,0,0,0,536,538,5,57,0,0,537,536,
        1,0,0,0,537,538,1,0,0,0,538,539,1,0,0,0,539,544,3,72,36,0,540,541,
        5,56,0,0,541,543,3,72,36,0,542,540,1,0,0,0,543,546,1,0,0,0,544,542,
        1,0,0,0,544,545,1,0,0,0,545,75,1,0,0,0,546,544,1,0,0,0,547,548,5,
        50,0,0,548,77,1,0,0,0,549,550,5,70,0,0,550,79,1,0,0,0,551,552,3,
        78,39,0,552,553,5,56,0,0,553,554,3,78,39,0,554,81,1,0,0,0,555,556,
        5,50,0,0,556,83,1,0,0,0,557,558,3,78,39,0,558,559,7,5,0,0,559,85,
        1,0,0,0,70,90,97,104,110,117,120,124,128,135,139,146,158,167,173,
        178,182,187,193,201,208,211,222,227,231,236,244,246,257,263,269,
        274,278,283,289,291,297,308,317,327,334,345,351,361,369,371,377,
        381,385,393,402,406,410,415,419,428,432,436,440,450,469,478,486,
        489,491,507,510,519,526,537,544
    ]

class WorkflowParser ( Parser ):

    grammarFileName = "WorkflowParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'ACTION'", "'AFTER'", "'AND'", "'ARTIFACT'", 
                     "'AS'", "'BEFORE'", "'CONST'", "'CONCURENCY'", "'DESCRIPTION'", 
                     "'DAY'", "'DEFINE'", "'DECIMAL'", "'EVENT'", "'EXECUTE'", 
                     "'ENTER'", "'='", "'EXIT'", "'EXPIRE'", "'FALSE'", 
                     "'FRAGMENT'", "'HOUR'", "'IN'", "'INCLUDE'", "'INITIALIZE'", 
                     "'INTEGER'", "'IS'", "'MATCHING'", "'MINUTE'", "'NAME'", 
                     "'NOT'", "'NULL'", "'ON'", "'OR'", "'PARAMETER'", "'RULE'", 
                     "'RECURSIVE'", "'SWITCH'", "'STATE'", "'STORE'", "'TEXT'", 
                     "'TIME'", "'TRUE'", "'UNIQUE'", "'USING'", "'VERSION'", 
                     "'WAITING'", "'WITH'", "'WHEN'", "'WORKFLOW'", "<INVALID>", 
                     "'('", "')'", "';'", "':'", "','", "'.'", "'@'", "'['", 
                     "']'", "<INVALID>", "'<='", "'>='", "'<'", "'>'", "'+'", 
                     "'-'", "'*'", "'/'" ]

    symbolicNames = [ "<INVALID>", "ACTION", "AFTER", "AND", "ARTIFACT", 
                      "AS", "BEFORE", "CONST", "CONCURENCY", "DESCRIPTION", 
                      "DAY", "DEFINE", "DECIMAL", "EVENT", "EXECUTE", "ENTER", 
                      "EQUAL", "EXIT", "EXPIRE", "FALSE", "FRAGMENT", "HOUR", 
                      "IN", "INCLUDE", "INITIALIZE", "INTEGER", "IS", "MATCHING", 
                      "MINUTE", "NAME", "NOT", "NULL", "ON", "OR", "PARAMETER", 
                      "RULE", "RECURSIVE", "SWITCH", "STATE", "STORE", "TEXT", 
                      "TIME", "TRUE", "UNIQUE", "USING", "VERSION", "WAITING", 
                      "WITH", "WHEN", "WORKFLOW", "CHAR_STRING", "LEFT_PAREN", 
                      "RIGHT_PAREN", "SEMICOLON", "COLON", "COMMA", "DOT", 
                      "AROBASE", "LEFT_BRACKET", "RIGHT_BRACKET", "NOT_EQUAL", 
                      "LESS_EQUAL", "GREATER_EQUAL", "LESS", "GREATER", 
                      "PLUS", "MINUS", "STAR", "SLASH", "SPACES", "NUMBER", 
                      "SINGLE_LINE_COMMENT", "MULTI_LINE_COMMENT", "REGULAR_ID" ]

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
    RULE_contextPath = 22
    RULE_jsonPathSegment = 23
    RULE_rule_conditions = 24
    RULE_event_declaration_statement = 25
    RULE_unique_keys = 26
    RULE_action_declaration_statement = 27
    RULE_artifact_declaration_statement = 28
    RULE_rule_declaration_statement = 29
    RULE_rule_script = 30
    RULE_expression = 31
    RULE_primaryExpression = 32
    RULE_parameters = 33
    RULE_parameter = 34
    RULE_type = 35
    RULE_key = 36
    RULE_compositekey = 37
    RULE_comment = 38
    RULE_number = 39
    RULE_numeric = 40
    RULE_string = 41
    RULE_delay = 42

    ruleNames =  [ "script", "script_fragment", "script_full", "concurency", 
                   "define_referenciel_statement", "define_state_statement", 
                   "constant_declaration", "value", "state", "initializing", 
                   "initializing_item", "on_event_statement", "switch_state", 
                   "execute", "execute2", "execute3", "matchings", "matching", 
                   "action", "arguments", "argument", "argumentValue", "contextPath", 
                   "jsonPathSegment", "rule_conditions", "event_declaration_statement", 
                   "unique_keys", "action_declaration_statement", "artifact_declaration_statement", 
                   "rule_declaration_statement", "rule_script", "expression", 
                   "primaryExpression", "parameters", "parameter", "type", 
                   "key", "compositekey", "comment", "number", "numeric", 
                   "string", "delay" ]

    EOF = Token.EOF
    ACTION=1
    AFTER=2
    AND=3
    ARTIFACT=4
    AS=5
    BEFORE=6
    CONST=7
    CONCURENCY=8
    DESCRIPTION=9
    DAY=10
    DEFINE=11
    DECIMAL=12
    EVENT=13
    EXECUTE=14
    ENTER=15
    EQUAL=16
    EXIT=17
    EXPIRE=18
    FALSE=19
    FRAGMENT=20
    HOUR=21
    IN=22
    INCLUDE=23
    INITIALIZE=24
    INTEGER=25
    IS=26
    MATCHING=27
    MINUTE=28
    NAME=29
    NOT=30
    NULL=31
    ON=32
    OR=33
    PARAMETER=34
    RULE=35
    RECURSIVE=36
    SWITCH=37
    STATE=38
    STORE=39
    TEXT=40
    TIME=41
    TRUE=42
    UNIQUE=43
    USING=44
    VERSION=45
    WAITING=46
    WITH=47
    WHEN=48
    WORKFLOW=49
    CHAR_STRING=50
    LEFT_PAREN=51
    RIGHT_PAREN=52
    SEMICOLON=53
    COLON=54
    COMMA=55
    DOT=56
    AROBASE=57
    LEFT_BRACKET=58
    RIGHT_BRACKET=59
    NOT_EQUAL=60
    LESS_EQUAL=61
    GREATER_EQUAL=62
    LESS=63
    GREATER=64
    PLUS=65
    MINUS=66
    STAR=67
    SLASH=68
    SPACES=69
    NUMBER=70
    SINGLE_LINE_COMMENT=71
    MULTI_LINE_COMMENT=72
    REGULAR_ID=73

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
            self.state = 90
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [20]:
                self.enterOuterAlt(localctx, 1)
                self.state = 86
                self.script_fragment()
                pass
            elif token in [23, 29]:
                self.enterOuterAlt(localctx, 2)
                self.state = 87
                self.script_full()
                self.state = 88
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
            self.state = 92
            self.match(WorkflowParser.FRAGMENT)
            self.state = 93
            self.match(WorkflowParser.NAME)
            self.state = 94
            self.key()
            self.state = 97
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==9:
                self.state = 95
                self.match(WorkflowParser.DESCRIPTION)
                self.state = 96
                self.comment()


            self.state = 102 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 99
                self.define_referenciel_statement()
                self.state = 100
                self.match(WorkflowParser.SEMICOLON)
                self.state = 104 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==11):
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
            self.state = 110
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==23:
                self.state = 106
                self.match(WorkflowParser.INCLUDE)
                self.state = 107
                self.match(WorkflowParser.CHAR_STRING)
                self.state = 112
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 113
            self.match(WorkflowParser.NAME)
            self.state = 114
            self.key()
            self.state = 117
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==45:
                self.state = 115
                self.match(WorkflowParser.VERSION)
                self.state = 116
                localctx.versionNumber = self.number()


            self.state = 120
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 119
                self.concurency()


            self.state = 124
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==9:
                self.state = 122
                self.match(WorkflowParser.DESCRIPTION)
                self.state = 123
                self.comment()


            self.state = 128
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==27:
                self.state = 126
                self.match(WorkflowParser.MATCHING)
                self.state = 127
                self.matchings()


            self.state = 135
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 130
                    self.define_referenciel_statement()
                    self.state = 131
                    self.match(WorkflowParser.SEMICOLON) 
                self.state = 137
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

            self.state = 139
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==24:
                self.state = 138
                self.initializing()


            self.state = 146
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==11:
                self.state = 141
                self.define_state_statement()
                self.state = 142
                self.match(WorkflowParser.SEMICOLON)
                self.state = 148
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
            self.state = 149
            self.match(WorkflowParser.CONCURENCY)
            self.state = 150
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


        def artifact_declaration_statement(self):
            return self.getTypedRuleContext(WorkflowParser.Artifact_declaration_statementContext,0)


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
            self.state = 152
            self.match(WorkflowParser.DEFINE)
            self.state = 158
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [13]:
                self.state = 153
                self.event_declaration_statement()
                pass
            elif token in [35]:
                self.state = 154
                self.rule_declaration_statement()
                pass
            elif token in [1]:
                self.state = 155
                self.action_declaration_statement()
                pass
            elif token in [4]:
                self.state = 156
                self.artifact_declaration_statement()
                pass
            elif token in [7]:
                self.state = 157
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
            self.state = 160
            self.match(WorkflowParser.DEFINE)
            self.state = 161
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
            self.state = 163
            self.match(WorkflowParser.CONST)
            self.state = 164
            self.key()
            self.state = 165
            self.value()
            self.state = 167
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 166
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
            self.state = 173
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,13,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 169
                self.string()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 170
                self.number()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 171
                self.delay()
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 172
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
            self.schemaRef = None # CompositekeyContext

        def STATE(self):
            return self.getToken(WorkflowParser.STATE, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def AS(self):
            return self.getToken(WorkflowParser.AS, 0)

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


        def compositekey(self):
            return self.getTypedRuleContext(WorkflowParser.CompositekeyContext,0)


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
            self.state = 175
            self.match(WorkflowParser.STATE)
            self.state = 176
            self.key()
            self.state = 178
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 177
                self.comment()


            self.state = 182
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 180
                self.match(WorkflowParser.AS)
                self.state = 181
                localctx.schemaRef = self.compositekey()


            self.state = 187
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,16,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 184
                    self.execute() 
                self.state = 189
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,16,self._ctx)

            self.state = 193
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==18 or _la==32:
                self.state = 190
                self.on_event_statement()
                self.state = 195
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
            self.state = 196
            self.match(WorkflowParser.INITIALIZE)
            self.state = 197
            self.match(WorkflowParser.WORKFLOW)
            self.state = 199 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 198
                self.initializing_item()
                self.state = 201 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==32):
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
            self.state = 203
            self.match(WorkflowParser.ON)
            self.state = 204
            self.match(WorkflowParser.EVENT)
            self.state = 205
            self.key()
            self.state = 208
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==48:
                self.state = 206
                self.match(WorkflowParser.WHEN)
                self.state = 207
                self.rule_conditions(0)


            self.state = 211
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==36:
                self.state = 210
                self.match(WorkflowParser.RECURSIVE)


            self.state = 213
            self.match(WorkflowParser.SWITCH)
            self.state = 214
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
            self.state = 222
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [32]:
                self.state = 216
                self.match(WorkflowParser.ON)
                self.state = 217
                self.match(WorkflowParser.EVENT)
                self.state = 218
                self.key()
                pass
            elif token in [18]:
                self.state = 219
                self.match(WorkflowParser.EXPIRE)
                self.state = 220
                self.match(WorkflowParser.AFTER)
                self.state = 221
                self.delay()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 225 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 224
                self.switch_state()
                self.state = 227 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((((_la - 14)) & ~0x3f) == 0 and ((1 << (_la - 14)) & 576460773820203009) != 0)):
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
            self.state = 231
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,23,self._ctx)
            if la_ == 1:
                self.state = 229
                self.match(WorkflowParser.WHEN)
                self.state = 230
                self.rule_conditions(0)


            self.state = 246
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,26,self._ctx)
            if la_ == 1:
                self.state = 236
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while ((((_la - 14)) & ~0x3f) == 0 and ((1 << (_la - 14)) & 576460773811814401) != 0):
                    self.state = 233
                    self.execute2()
                    self.state = 238
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 239
                self.match(WorkflowParser.SWITCH)
                self.state = 240
                self.key()
                pass

            elif la_ == 2:
                self.state = 242 
                self._errHandler.sync(self)
                _alt = 1
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt == 1:
                        self.state = 241
                        self.execute2()

                    else:
                        raise NoViableAltException(self)
                    self.state = 244 
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,25,self._ctx)

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
            self.state = 248
            self.match(WorkflowParser.ON)
            self.state = 257
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,27,self._ctx)
            if la_ == 1:
                self.state = 249
                self.match(WorkflowParser.ENTER)
                self.state = 250
                self.match(WorkflowParser.STATE)
                pass

            elif la_ == 2:
                self.state = 251
                self.match(WorkflowParser.EXIT)
                self.state = 252
                self.match(WorkflowParser.STATE)
                pass

            elif la_ == 3:
                self.state = 253
                self.match(WorkflowParser.ENTER)
                self.state = 254
                self.match(WorkflowParser.AND)
                self.state = 255
                self.match(WorkflowParser.EXIT)
                self.state = 256
                self.match(WorkflowParser.STATE)
                pass


            self.state = 259
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
            self.state = 263
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==48:
                self.state = 261
                self.match(WorkflowParser.WHEN)
                self.state = 262
                self.rule_conditions(0)


            self.state = 269
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==46:
                self.state = 265
                self.match(WorkflowParser.WAITING)
                self.state = 266
                self.delay()
                self.state = 267
                self.match(WorkflowParser.BEFORE)


            self.state = 272 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 271
                    self.execute3()

                else:
                    raise NoViableAltException(self)
                self.state = 274 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,30,self._ctx)

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
            self.state = 291
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [14, 73]:
                self.enterOuterAlt(localctx, 1)
                self.state = 278
                self._errHandler.sync(self)
                token = self._input.LA(1)
                if token in [14]:
                    self.state = 276
                    self.match(WorkflowParser.EXECUTE)
                    pass
                elif token in [73]:
                    self.state = 277
                    self.key()
                    pass
                else:
                    raise NoViableAltException(self)

                self.state = 281 
                self._errHandler.sync(self)
                _alt = 1
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt == 1:
                        self.state = 280
                        self.action()

                    else:
                        raise NoViableAltException(self)
                    self.state = 283 
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,32,self._ctx)

                pass
            elif token in [39]:
                self.enterOuterAlt(localctx, 2)
                self.state = 285
                self.match(WorkflowParser.STORE)
                self.state = 287 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 286
                    self.matchings()
                    self.state = 289 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==51):
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
            self.state = 293
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 295 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 294
                self.matching()
                self.state = 297 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==73):
                    break

            self.state = 299
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
            self.state = 301
            self.key()
            self.state = 302
            self.match(WorkflowParser.EQUAL)
            self.state = 303
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
            self.state = 305
            self.key()
            self.state = 306
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 308
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==73:
                self.state = 307
                self.arguments()


            self.state = 310
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
            self.state = 312
            self.argument()
            self.state = 317
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==55:
                self.state = 313
                self.match(WorkflowParser.COMMA)
                self.state = 314
                self.argument()
                self.state = 319
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
            self.state = 320
            self.key()
            self.state = 321
            self.match(WorkflowParser.EQUAL)
            self.state = 322
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


        def contextPath(self):
            return self.getTypedRuleContext(WorkflowParser.ContextPathContext,0)


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
            self.state = 327
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,38,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 324
                self.string()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 325
                self.contextPath()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 326
                self.compositekey()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ContextPathContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def AROBASE(self):
            return self.getToken(WorkflowParser.AROBASE, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def jsonPathSegment(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.JsonPathSegmentContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.JsonPathSegmentContext,i)


        def getRuleIndex(self):
            return WorkflowParser.RULE_contextPath

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContextPath" ):
                return visitor.visitContextPath(self)
            else:
                return visitor.visitChildren(self)




    def contextPath(self):

        localctx = WorkflowParser.ContextPathContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_contextPath)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 329
            self.match(WorkflowParser.AROBASE)
            self.state = 330
            self.key()
            self.state = 334
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,39,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 331
                    self.jsonPathSegment() 
                self.state = 336
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,39,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class JsonPathSegmentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DOT(self):
            return self.getToken(WorkflowParser.DOT, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def LEFT_BRACKET(self):
            return self.getToken(WorkflowParser.LEFT_BRACKET, 0)

        def NUMBER(self):
            return self.getToken(WorkflowParser.NUMBER, 0)

        def RIGHT_BRACKET(self):
            return self.getToken(WorkflowParser.RIGHT_BRACKET, 0)

        def CHAR_STRING(self):
            return self.getToken(WorkflowParser.CHAR_STRING, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_jsonPathSegment

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitJsonPathSegment" ):
                return visitor.visitJsonPathSegment(self)
            else:
                return visitor.visitChildren(self)




    def jsonPathSegment(self):

        localctx = WorkflowParser.JsonPathSegmentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_jsonPathSegment)
        try:
            self.state = 345
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,40,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 337
                self.match(WorkflowParser.DOT)
                self.state = 338
                self.key()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 339
                self.match(WorkflowParser.LEFT_BRACKET)
                self.state = 340
                self.match(WorkflowParser.NUMBER)
                self.state = 341
                self.match(WorkflowParser.RIGHT_BRACKET)
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 342
                self.match(WorkflowParser.LEFT_BRACKET)
                self.state = 343
                self.match(WorkflowParser.CHAR_STRING)
                self.state = 344
                self.match(WorkflowParser.RIGHT_BRACKET)
                pass


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
        _startState = 48
        self.enterRecursionRule(localctx, 48, self.RULE_rule_conditions, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 361
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [73]:
                self.state = 348
                self.key()
                self.state = 349
                self.match(WorkflowParser.LEFT_PAREN)
                self.state = 351
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==73:
                    self.state = 350
                    self.arguments()


                self.state = 353
                self.match(WorkflowParser.RIGHT_PAREN)
                pass
            elif token in [30]:
                self.state = 355
                self.match(WorkflowParser.NOT)
                self.state = 356
                self.rule_conditions(4)
                pass
            elif token in [51]:
                self.state = 357
                self.match(WorkflowParser.LEFT_PAREN)
                self.state = 358
                self.rule_conditions(0)
                self.state = 359
                self.match(WorkflowParser.RIGHT_PAREN)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 371
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,44,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 369
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,43,self._ctx)
                    if la_ == 1:
                        localctx = WorkflowParser.Rule_conditionsContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_rule_conditions)
                        self.state = 363
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 364
                        self.match(WorkflowParser.AND)
                        self.state = 365
                        self.rule_conditions(4)
                        pass

                    elif la_ == 2:
                        localctx = WorkflowParser.Rule_conditionsContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_rule_conditions)
                        self.state = 366
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 367
                        self.match(WorkflowParser.OR)
                        self.state = 368
                        self.rule_conditions(3)
                        pass

             
                self.state = 373
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,44,self._ctx)

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
        self.enterRule(localctx, 50, self.RULE_event_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 374
            self.match(WorkflowParser.EVENT)
            self.state = 375
            self.key()
            self.state = 377
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 376
                self.comment()


            self.state = 381
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 379
                self.match(WorkflowParser.AS)
                self.state = 380
                localctx.schemaRef = self.compositekey()


            self.state = 385
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 383
                self.match(WorkflowParser.UNIQUE)
                self.state = 384
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
        self.enterRule(localctx, 52, self.RULE_unique_keys)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 387
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 388
            self.key()
            self.state = 393
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==55:
                self.state = 389
                self.match(WorkflowParser.COMMA)
                self.state = 390
                self.key()
                self.state = 395
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 396
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
            self.scriptRef = None # CompositekeyContext

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


        def AS(self):
            return self.getToken(WorkflowParser.AS, 0)

        def compositekey(self):
            return self.getTypedRuleContext(WorkflowParser.CompositekeyContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_action_declaration_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAction_declaration_statement" ):
                return visitor.visitAction_declaration_statement(self)
            else:
                return visitor.visitChildren(self)




    def action_declaration_statement(self):

        localctx = WorkflowParser.Action_declaration_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_action_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 398
            self.match(WorkflowParser.ACTION)
            self.state = 399
            self.key()
            self.state = 400
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 402
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1099545186304) != 0):
                self.state = 401
                self.parameters()


            self.state = 404
            self.match(WorkflowParser.RIGHT_PAREN)
            self.state = 406
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 405
                self.comment()


            self.state = 410
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 408
                self.match(WorkflowParser.AS)
                self.state = 409
                localctx.scriptRef = self.compositekey()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Artifact_declaration_statementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.schemaRef = None # CompositekeyContext
            self.scriptRef = None # CompositekeyContext

        def ARTIFACT(self):
            return self.getToken(WorkflowParser.ARTIFACT, 0)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def USING(self):
            return self.getToken(WorkflowParser.USING, 0)

        def compositekey(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.CompositekeyContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.CompositekeyContext,i)


        def comment(self):
            return self.getTypedRuleContext(WorkflowParser.CommentContext,0)


        def AS(self):
            return self.getToken(WorkflowParser.AS, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_artifact_declaration_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArtifact_declaration_statement" ):
                return visitor.visitArtifact_declaration_statement(self)
            else:
                return visitor.visitChildren(self)




    def artifact_declaration_statement(self):

        localctx = WorkflowParser.Artifact_declaration_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_artifact_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 412
            self.match(WorkflowParser.ARTIFACT)
            self.state = 413
            self.key()
            self.state = 415
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 414
                self.comment()


            self.state = 419
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 417
                self.match(WorkflowParser.AS)
                self.state = 418
                localctx.schemaRef = self.compositekey()


            self.state = 421
            self.match(WorkflowParser.USING)
            self.state = 422
            localctx.scriptRef = self.compositekey()
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
            self.scriptRef = None # CompositekeyContext

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


        def AS(self):
            return self.getToken(WorkflowParser.AS, 0)

        def compositekey(self):
            return self.getTypedRuleContext(WorkflowParser.CompositekeyContext,0)


        def getRuleIndex(self):
            return WorkflowParser.RULE_rule_declaration_statement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule_declaration_statement" ):
                return visitor.visitRule_declaration_statement(self)
            else:
                return visitor.visitChildren(self)




    def rule_declaration_statement(self):

        localctx = WorkflowParser.Rule_declaration_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_rule_declaration_statement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 424
            self.match(WorkflowParser.RULE)
            self.state = 425
            self.key()
            self.state = 426
            self.match(WorkflowParser.LEFT_PAREN)
            self.state = 428
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1099545186304) != 0):
                self.state = 427
                self.parameters()


            self.state = 430
            self.match(WorkflowParser.RIGHT_PAREN)
            self.state = 432
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==50:
                self.state = 431
                self.comment()


            self.state = 436
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 434
                self.match(WorkflowParser.AS)
                self.state = 435
                localctx.scriptRef = self.compositekey()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Rule_scriptContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self):
            return self.getTypedRuleContext(WorkflowParser.ExpressionContext,0)


        def EOF(self):
            return self.getToken(WorkflowParser.EOF, 0)

        def SEMICOLON(self):
            return self.getToken(WorkflowParser.SEMICOLON, 0)

        def getRuleIndex(self):
            return WorkflowParser.RULE_rule_script

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule_script" ):
                return visitor.visitRule_script(self)
            else:
                return visitor.visitChildren(self)




    def rule_script(self):

        localctx = WorkflowParser.Rule_scriptContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_rule_script)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 438
            self.expression(0)
            self.state = 440
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==53:
                self.state = 439
                self.match(WorkflowParser.SEMICOLON)


            self.state = 442
            self.match(WorkflowParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return WorkflowParser.RULE_expression

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class CompareExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.op = None # Token
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def EQUAL(self):
            return self.getToken(WorkflowParser.EQUAL, 0)
        def NOT_EQUAL(self):
            return self.getToken(WorkflowParser.NOT_EQUAL, 0)
        def LESS(self):
            return self.getToken(WorkflowParser.LESS, 0)
        def LESS_EQUAL(self):
            return self.getToken(WorkflowParser.LESS_EQUAL, 0)
        def GREATER(self):
            return self.getToken(WorkflowParser.GREATER, 0)
        def GREATER_EQUAL(self):
            return self.getToken(WorkflowParser.GREATER_EQUAL, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompareExpression" ):
                return visitor.visitCompareExpression(self)
            else:
                return visitor.visitChildren(self)


    class OrExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def OR(self):
            return self.getToken(WorkflowParser.OR, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrExpression" ):
                return visitor.visitOrExpression(self)
            else:
                return visitor.visitChildren(self)


    class AndExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def AND(self):
            return self.getToken(WorkflowParser.AND, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAndExpression" ):
                return visitor.visitAndExpression(self)
            else:
                return visitor.visitChildren(self)


    class InExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def IN(self):
            return self.getToken(WorkflowParser.IN, 0)
        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)
        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)
        def NOT(self):
            return self.getToken(WorkflowParser.NOT, 0)
        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.COMMA)
            else:
                return self.getToken(WorkflowParser.COMMA, i)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInExpression" ):
                return visitor.visitInExpression(self)
            else:
                return visitor.visitChildren(self)


    class AddExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.op = None # Token
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def PLUS(self):
            return self.getToken(WorkflowParser.PLUS, 0)
        def MINUS(self):
            return self.getToken(WorkflowParser.MINUS, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAddExpression" ):
                return visitor.visitAddExpression(self)
            else:
                return visitor.visitChildren(self)


    class NullExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(WorkflowParser.ExpressionContext,0)

        def IS(self):
            return self.getToken(WorkflowParser.IS, 0)
        def NULL(self):
            return self.getToken(WorkflowParser.NULL, 0)
        def NOT(self):
            return self.getToken(WorkflowParser.NOT, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNullExpression" ):
                return visitor.visitNullExpression(self)
            else:
                return visitor.visitChildren(self)


    class NotExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NOT(self):
            return self.getToken(WorkflowParser.NOT, 0)
        def expression(self):
            return self.getTypedRuleContext(WorkflowParser.ExpressionContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNotExpression" ):
                return visitor.visitNotExpression(self)
            else:
                return visitor.visitChildren(self)


    class MultiplyExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.op = None # Token
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def STAR(self):
            return self.getToken(WorkflowParser.STAR, 0)
        def SLASH(self):
            return self.getToken(WorkflowParser.SLASH, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMultiplyExpression" ):
                return visitor.visitMultiplyExpression(self)
            else:
                return visitor.visitChildren(self)


    class NegateExpressionContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def MINUS(self):
            return self.getToken(WorkflowParser.MINUS, 0)
        def expression(self):
            return self.getTypedRuleContext(WorkflowParser.ExpressionContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNegateExpression" ):
                return visitor.visitNegateExpression(self)
            else:
                return visitor.visitChildren(self)


    class PrimaryContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def primaryExpression(self):
            return self.getTypedRuleContext(WorkflowParser.PrimaryExpressionContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrimary" ):
                return visitor.visitPrimary(self)
            else:
                return visitor.visitChildren(self)



    def expression(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = WorkflowParser.ExpressionContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 62
        self.enterRecursionRule(localctx, 62, self.RULE_expression, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 450
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [66]:
                localctx = WorkflowParser.NegateExpressionContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 445
                self.match(WorkflowParser.MINUS)
                self.state = 446
                self.expression(10)
                pass
            elif token in [30]:
                localctx = WorkflowParser.NotExpressionContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 447
                self.match(WorkflowParser.NOT)
                self.state = 448
                self.expression(4)
                pass
            elif token in [19, 31, 42, 50, 51, 57, 70, 73]:
                localctx = WorkflowParser.PrimaryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 449
                self.primaryExpression()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 491
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,63,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 489
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,62,self._ctx)
                    if la_ == 1:
                        localctx = WorkflowParser.MultiplyExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 452
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 453
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==67 or _la==68):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 454
                        self.expression(10)
                        pass

                    elif la_ == 2:
                        localctx = WorkflowParser.AddExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 455
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 456
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==65 or _la==66):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 457
                        self.expression(9)
                        pass

                    elif la_ == 3:
                        localctx = WorkflowParser.CompareExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 458
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 459
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(((((_la - 16)) & ~0x3f) == 0 and ((1 << (_la - 16)) & 545357767376897) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 460
                        self.expression(8)
                        pass

                    elif la_ == 4:
                        localctx = WorkflowParser.AndExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 461
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 462
                        self.match(WorkflowParser.AND)
                        self.state = 463
                        self.expression(4)
                        pass

                    elif la_ == 5:
                        localctx = WorkflowParser.OrExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 464
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 465
                        self.match(WorkflowParser.OR)
                        self.state = 466
                        self.expression(3)
                        pass

                    elif la_ == 6:
                        localctx = WorkflowParser.InExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 467
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 469
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)
                        if _la==30:
                            self.state = 468
                            self.match(WorkflowParser.NOT)


                        self.state = 471
                        self.match(WorkflowParser.IN)
                        self.state = 472
                        self.match(WorkflowParser.LEFT_PAREN)
                        self.state = 473
                        self.expression(0)
                        self.state = 478
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)
                        while _la==55:
                            self.state = 474
                            self.match(WorkflowParser.COMMA)
                            self.state = 475
                            self.expression(0)
                            self.state = 480
                            self._errHandler.sync(self)
                            _la = self._input.LA(1)

                        self.state = 481
                        self.match(WorkflowParser.RIGHT_PAREN)
                        pass

                    elif la_ == 7:
                        localctx = WorkflowParser.NullExpressionContext(self, WorkflowParser.ExpressionContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 483
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 484
                        self.match(WorkflowParser.IS)
                        self.state = 486
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)
                        if _la==30:
                            self.state = 485
                            self.match(WorkflowParser.NOT)


                        self.state = 488
                        self.match(WorkflowParser.NULL)
                        pass

             
                self.state = 493
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,63,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class PrimaryExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return WorkflowParser.RULE_primaryExpression

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class IdentifierContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifier" ):
                return visitor.visitIdentifier(self)
            else:
                return visitor.visitChildren(self)


    class NullLiteralContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NULL(self):
            return self.getToken(WorkflowParser.NULL, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNullLiteral" ):
                return visitor.visitNullLiteral(self)
            else:
                return visitor.visitChildren(self)


    class StringLiteralContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def string(self):
            return self.getTypedRuleContext(WorkflowParser.StringContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStringLiteral" ):
                return visitor.visitStringLiteral(self)
            else:
                return visitor.visitChildren(self)


    class FunctionCallContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def key(self):
            return self.getTypedRuleContext(WorkflowParser.KeyContext,0)

        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)
        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)
        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(WorkflowParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(WorkflowParser.ExpressionContext,i)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(WorkflowParser.COMMA)
            else:
                return self.getToken(WorkflowParser.COMMA, i)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunctionCall" ):
                return visitor.visitFunctionCall(self)
            else:
                return visitor.visitChildren(self)


    class ParenthesizedContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LEFT_PAREN(self):
            return self.getToken(WorkflowParser.LEFT_PAREN, 0)
        def expression(self):
            return self.getTypedRuleContext(WorkflowParser.ExpressionContext,0)

        def RIGHT_PAREN(self):
            return self.getToken(WorkflowParser.RIGHT_PAREN, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParenthesized" ):
                return visitor.visitParenthesized(self)
            else:
                return visitor.visitChildren(self)


    class IntegerLiteralContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def number(self):
            return self.getTypedRuleContext(WorkflowParser.NumberContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntegerLiteral" ):
                return visitor.visitIntegerLiteral(self)
            else:
                return visitor.visitChildren(self)


    class PathValueContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def contextPath(self):
            return self.getTypedRuleContext(WorkflowParser.ContextPathContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPathValue" ):
                return visitor.visitPathValue(self)
            else:
                return visitor.visitChildren(self)


    class NumericLiteralContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def numeric(self):
            return self.getTypedRuleContext(WorkflowParser.NumericContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumericLiteral" ):
                return visitor.visitNumericLiteral(self)
            else:
                return visitor.visitChildren(self)


    class BooleanLiteralContext(PrimaryExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a WorkflowParser.PrimaryExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def TRUE(self):
            return self.getToken(WorkflowParser.TRUE, 0)
        def FALSE(self):
            return self.getToken(WorkflowParser.FALSE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBooleanLiteral" ):
                return visitor.visitBooleanLiteral(self)
            else:
                return visitor.visitChildren(self)



    def primaryExpression(self):

        localctx = WorkflowParser.PrimaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_primaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 519
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,66,self._ctx)
            if la_ == 1:
                localctx = WorkflowParser.NumericLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 494
                self.numeric()
                pass

            elif la_ == 2:
                localctx = WorkflowParser.IntegerLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 495
                self.number()
                pass

            elif la_ == 3:
                localctx = WorkflowParser.StringLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 496
                self.string()
                pass

            elif la_ == 4:
                localctx = WorkflowParser.BooleanLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 497
                _la = self._input.LA(1)
                if not(_la==19 or _la==42):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass

            elif la_ == 5:
                localctx = WorkflowParser.NullLiteralContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 498
                self.match(WorkflowParser.NULL)
                pass

            elif la_ == 6:
                localctx = WorkflowParser.PathValueContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 499
                self.contextPath()
                pass

            elif la_ == 7:
                localctx = WorkflowParser.FunctionCallContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 500
                self.key()
                self.state = 501
                self.match(WorkflowParser.LEFT_PAREN)
                self.state = 510
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 19)) & ~0x3f) == 0 and ((1 << (_la - 19)) & 20407217140275201) != 0):
                    self.state = 502
                    self.expression(0)
                    self.state = 507
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    while _la==55:
                        self.state = 503
                        self.match(WorkflowParser.COMMA)
                        self.state = 504
                        self.expression(0)
                        self.state = 509
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)



                self.state = 512
                self.match(WorkflowParser.RIGHT_PAREN)
                pass

            elif la_ == 8:
                localctx = WorkflowParser.IdentifierContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 514
                self.key()
                pass

            elif la_ == 9:
                localctx = WorkflowParser.ParenthesizedContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 515
                self.match(WorkflowParser.LEFT_PAREN)
                self.state = 516
                self.expression(0)
                self.state = 517
                self.match(WorkflowParser.RIGHT_PAREN)
                pass


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
        self.enterRule(localctx, 66, self.RULE_parameters)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 521
            self.parameter()
            self.state = 526
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==55:
                self.state = 522
                self.match(WorkflowParser.COMMA)
                self.state = 523
                self.parameter()
                self.state = 528
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
        self.enterRule(localctx, 68, self.RULE_parameter)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 529
            self.type_()
            self.state = 530
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
        self.enterRule(localctx, 70, self.RULE_type)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 532
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 1099545186304) != 0)):
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
        self.enterRule(localctx, 72, self.RULE_key)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 534
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
        self.enterRule(localctx, 74, self.RULE_compositekey)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 537
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==57:
                self.state = 536
                self.match(WorkflowParser.AROBASE)


            self.state = 539
            self.key()
            self.state = 544
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==56:
                self.state = 540
                self.match(WorkflowParser.DOT)
                self.state = 541
                self.key()
                self.state = 546
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
        self.enterRule(localctx, 76, self.RULE_comment)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 547
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
        self.enterRule(localctx, 78, self.RULE_number)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 549
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
        self.enterRule(localctx, 80, self.RULE_numeric)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 551
            self.number()
            self.state = 552
            self.match(WorkflowParser.DOT)
            self.state = 553
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
        self.enterRule(localctx, 82, self.RULE_string)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 555
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
        self.enterRule(localctx, 84, self.RULE_delay)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 557
            self.number()
            self.state = 558
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 270533632) != 0)):
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
        self._predicates[24] = self.rule_conditions_sempred
        self._predicates[31] = self.expression_sempred
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
         

    def expression_sempred(self, localctx:ExpressionContext, predIndex:int):
            if predIndex == 2:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 3)
         

            if predIndex == 6:
                return self.precpred(self._ctx, 2)
         

            if predIndex == 7:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 8:
                return self.precpred(self._ctx, 5)
         




