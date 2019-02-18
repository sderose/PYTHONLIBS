#!/usr/bin/env python
#
# TokensEN.py
#
# English-specific reference data for use with Tokenizers.
# Extracted and ported from Tokenizer.pm by Steven J. DeRose.
#
# To do:
#
from __future__ import print_function
#import sys
import regex as re  # Adds support for \p{}
#import codecs

#from MarkupHelpFormatter import MarkupHelpFormatter

__version__ = "2018-08-21"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2012-08-22",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-08-21",
}

#########################################################################
# Language-specific tokens for English.
#     Personal titles, calendar and temporal names, contractions.
#     (pulled from SJD Volsunga and lexicon/)
#
class TokensEN:
    def __init__(self):
        # Locale names also available from the calendar module:
        # from calendar import TimeEncoding,month_name,day_name,day_abbr
        #
        self.months = (
            "January|February|March|April|May|June|" +
            "July|August|September|October|November|December|" +
            "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec"
        )
        self.weekdays = (
            "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|" +
            "Mon|Tues?|Weds?|Thurs?|Fri|Sat|Sun"
        )

        self.relativeDays = "today|tomorrow|yesterday|eve"
        self.dayParts  = (
            "morning|noon|afternoon|night|midnight|" +
            "dawn|dusk|matins|vespers|lauds"
        )

        self.titles = (
            "Mr|Dr|Mrs|Ms|Messr|Messrs|Rev|Fr|St|Msgnr|" +
            "Pres|Gen|Cpl|Maj|Pvt|" +
            "Mister|Doctor|Mistress|Miss|Reverend|Father|Saint|Monsignor|" +
            "President|General|Corporal|Major|Private"
        )

        self.unitPrefixes = {
            "deci|centi|milli|micro|nano|pico|atto|femto|" +
            "deka|hekta|kilo|mega|giga|tera|peta|exa|zeta|yotta"
        }

        self.countryCodes = {  # For URIs, etc.
            'AF': ('AFG',   4, "Afghanistan"),
            'AX': ('ALA', 248, "Aland Islands"),
            'AL': ('ALB',   8, "Albania"),
            'DZ': ('DZA',  12, "Algeria"),
            'AS': ('ASM',  16, "American Samoa"),
            'AD': ('AND',  20, "Andorra"),
            'AO': ('AGO',  24, "Angola"),
            'AI': ('AIA', 660, "Anguilla"),
            'AQ': ('ATA',  10, "Antarctica"),
            'AG': ('ATG',  28, "Antigua and Barbuda"),
            'AR': ('ARG',  32, "Argentina"),
            'AM': ('ARM',  51, "Armenia"),
            'AW': ('ABW', 533, "Aruba"),
            'AU': ('AUS',  36, "Australia"),
            'AT': ('AUT',  40, "Austria"),
            'AZ': ('AZE',  31, "Azerbaijan"),
            'BS': ('BHS',  44, "Bahamas"),
            'BH': ('BHR',  48, "Bahrain"),
            'BD': ('BGD',  50, "Bangladesh"),
            'BB': ('BRB',  52, "Barbados"),
            'BY': ('BLR', 112, "Belarus"),
            'BE': ('BEL',  56, "Belgium"),
            'BZ': ('BLZ',  84, "Belize"),
            'BJ': ('BEN', 204, "Benin"),
            'BM': ('BMU',  60, "Bermuda"),
            'BT': ('BTN',  64, "Bhutan"),
            'BO': ('BOL',  68, "Bolivia"),
            'BA': ('BIH',  70, "Bosnia and Herzegovina"),
            'BW': ('BWA',  72, "Botswana"),
            'BV': ('BVT',  74, "Bouvet Island"),
            'BR': ('BRA',  76, "Brazil"),
            'VG': ('VGB',  92, "British Virgin Islands"),
            'IO': ('IOT',  86, "British Indian Ocean Territory"),
            'BN': ('BRN',  96, "Brunei Darussalam"),
            'BG': ('BGR', 100, "Bulgaria"),
            'BF': ('BFA', 854, "Burkina Faso"),
            'BI': ('BDI', 108, "Burundi"),
            'KH': ('KHM', 116, "Cambodia"),
            'CM': ('CMR', 120, "Cameroon"),
            'CA': ('CAN', 124, "Canada"),
            'CV': ('CPV', 132, "Cape Verde"),
            'KY': ('CYM', 136, "Cayman Islands"),
            'CF': ('CAF', 140, "Central African Republic"),
            'TD': ('TCD', 148, "Chad"),
            'CL': ('CHL', 152, "Chile"),
            'CN': ('CHN', 156, "China"),
            'HK': ('HKG', 344, "Hong Kong, Special Administrative Region of China",),
            'MO': ('MAC', 446, "Macao, Special Administrative Region of China"),
            'CX': ('CXR', 162, "Christmas Island"),
            'CC': ('CCK', 166, "Cocos (Keeling) Islands"),
            'CO': ('COL', 170, "Colombia"),
            'KM': ('COM', 174, "Comoros"),
            'CG': ('COG', 178, "Congo (Brazzaville)"),
            'CD': ('COD', 180, "Congo, Democratic Republic of the"),
            'CK': ('COK', 184, "Cook Islands"),
            'CR': ('CRI', 188, "Costa Rica"),
            'CI': ('CIV', 384, "Cote de'Ivoire"),
            'HR': ('HRV', 191, "Croatia"),
            'CU': ('CUB', 192, "Cuba"),
            'CY': ('CYP', 196, "Cyprus"),
            'CZ': ('CZE', 203, "Czech Republic"),
            'DK': ('DNK', 208, "Denmark"),
            'DJ': ('DJI', 262, "Djibouti"),
            'DM': ('DMA', 212, "Dominica"),
            'DO': ('DOM', 214, "Dominican Republic"),
            'EC': ('ECU', 218, "Ecuador"),
            'EG': ('EGY', 818, "Egypt"),
            'SV': ('SLV', 222, "El Salvador"),
            'GQ': ('GNQ', 226, "Equatorial Guinea"),
            'ER': ('ERI', 232, "Eritrea"),
            'EE': ('EST', 233, "Estonia"),
            'ET': ('ETH', 231, "Ethiopia"),
            'FK': ('FLK', 238, "Falkland Islands (Malvinas)"),
            'FO': ('FRO', 234, "Faroe Islands"),
            'FJ': ('FJI', 242, "Fiji"),
            'FI': ('FIN', 246, "Finland"),
            'FR': ('FRA', 250, "France"),
            'GF': ('GUF', 254, "French Guiana"),
            'PF': ('PYF', 258, "French Polynesia"),
            'TF': ('ATF', 260, "French Southern Territories"),
            'GA': ('GAB', 266, "Gabon"),
            'GM': ('GMB', 270, "Gambia"),
            'GE': ('GEO', 268, "Georgia"),
            'DE': ('DEU', 276, "Germany"),
            'GH': ('GHA', 288, "Ghana"),
            'GI': ('GIB', 292, "Gibraltar"),
            'GR': ('GRC', 300, "Greece"),
            'GL': ('GRL', 304, "Greenland"),
            'GD': ('GRD', 308, "Grenada"),
            'GP': ('GLP', 312, "Guadeloupe"),
            'GU': ('GUM', 316, "Guam"),
            'GT': ('GTM', 320, "Guatemala"),
            'GG': ('GGY', 831, "Guernsey"),
            'GN': ('GIN', 324, "Guinea"),
            'GW': ('GNB', 624, "Guinea-Bissau"),
            'GY': ('GUY', 328, "Guyana"),
            'HT': ('HTI', 332, "Haiti"),
            'HM': ('HMD', 334, "Heard Island and Mcdonald Islands"),
            'VA': ('VAT', 336, "Holy See (Vatican City State)"),
            'HN': ('HND', 340, "Honduras"),
            'HU': ('HUN', 348, "Hungary"),
            'IS': ('ISL', 352, "Iceland"),
            'IN': ('IND', 356, "India"),
            'ID': ('IDN', 360, "Indonesia"),
            'IR': ('IRN', 364, "Iran, Islamic Republic of"),
            'IQ': ('IRQ', 368, "Iraq"),
            'IE': ('IRL', 372, "Ireland"),
            'IM': ('IMN', 833, "Isle of Man"),
            'IL': ('ISR', 376, "Israel"),
            'IT': ('ITA', 380, "Italy"),
            'JM': ('JAM', 388, "Jamaica"),
            'JP': ('JPN', 392, "Japan"),
            'JE': ('JEY', 832, "Jersey"),
            'JO': ('JOR', 400, "Jordan"),
            'KZ': ('KAZ', 398, "Kazakhstan"),
            'KE': ('KEN', 404, "Kenya"),
            'KI': ('KIR', 296, "Kiribati"),
            'KP': ('PRK', 408, "Korea, Democratic People&apos;s Republic of"),
            'KR': ('KOR', 410, "Korea, Republic of"),
            'KW': ('KWT', 414, "Kuwait"),
            'KG': ('KGZ', 417, "Kyrgyzstan"),
            'LA': ('LAO', 418, "Lao PDR"),
            'LV': ('LVA', 428, "Latvia"),
            'LB': ('LBN', 422, "Lebanon"),
            'LS': ('LSO', 426, "Lesotho"),
            'LR': ('LBR', 430, "Liberia"),
            'LY': ('LBY', 434, "Libya"),
            'LI': ('LIE', 438, "Liechtenstein"),
            'LT': ('LTU', 440, "Lithuania"),
            'LU': ('LUX', 442, "Luxembourg"),
            'MK': ('MKD', 807, "Macedonia, Republic of"),
            'MG': ('MDG', 450, "Madagascar"),
            'MW': ('MWI', 454, "Malawi"),
            'MY': ('MYS', 458, "Malaysia"),
            'MV': ('MDV', 462, "Maldives"),
            'ML': ('MLI', 466, "Mali"),
            'MT': ('MLT', 470, "Malta"),
            'MH': ('MHL', 584, "Marshall Islands"),
            'MQ': ('MTQ', 474, "Martinique"),
            'MR': ('MRT', 478, "Mauritania"),
            'MU': ('MUS', 480, "Mauritius"),
            'YT': ('MYT', 175, "Mayotte"),
            'MX': ('MEX', 484, "Mexico"),
            'FM': ('FSM', 583, "Micronesia, Federated States of"),
            'MD': ('MDA', 498, "Moldova"),
            'MC': ('MCO', 492, "Monaco"),
            'MN': ('MNG', 496, "Mongolia"),
            'ME': ('MNE', 499, "Montenegro"),
            'MS': ('MSR', 500, "Montserrat"),
            'MA': ('MAR', 504, "Morocco"),
            'MZ': ('MOZ', 508, "Mozambique"),
            'MM': ('MMR', 104, "Myanmar"),
            'NA': ('NAM', 516, "Namibia"),
            'NR': ('NRU', 520, "Nauru"),
            'NP': ('NPL', 524, "Nepal"),
            'NL': ('NLD', 528, "Netherlands"),
            'AN': ('ANT', 530, "Netherlands Antilles"),
            'NC': ('NCL', 540, "New Caledonia"),
            'NZ': ('NZL', 554, "New Zealand"),
            'NI': ('NIC', 558, "Nicaragua"),
            'NE': ('NER', 562, "Niger"),
            'NG': ('NGA', 566, "Nigeria"),
            'NU': ('NIU', 570, "Niue"),
            'NF': ('NFK', 574, "Norfolk Island"),
            'MP': ('MNP', 580, "Northern Mariana Islands"),
            'NO': ('NOR', 578, "Norway"),
            'OM': ('OMN', 512, "Oman"),
            'PK': ('PAK', 586, "Pakistan"),
            'PW': ('PLW', 585, "Palau"),
            'PA': ('PAN', 591, "Panama"),
            'PG': ('PNG', 598, "Papua New Guinea"),
            'PY': ('PRY', 600, "Paraguay"),
            'PE': ('PER', 604, "Peru"),
            'PH': ('PHL', 608, "Philippines"),
            'PN': ('PCN', 612, "Pitcairn"),
            'PL': ('POL', 616, "Poland"),
            'PT': ('PRT', 620, "Portugal"),
            'PR': ('PRI', 630, "Puerto Rico"),
            'QA': ('QAT', 634, "Qatar"),
            'RE': ('REU', 638, "Reunion"),
            'RO': ('ROU', 642, "Romania"),
            'RU': ('RUS', 643, "Russian Federation"),
            'RW': ('RWA', 646, "Rwanda"),
            'BL': ('BLM', 652, "Saint-Barthelemy"),
            'SH': ('SHN', 654, "Saint Helena"),
            'KN': ('KNA', 659, "Saint Kitts and Nevis"),
            'LC': ('LCA', 662, "Saint Lucia"),
            'MF': ('MAF', 663, "Saint-Martin (French part)"),
            'PM': ('SPM', 666, "Saint Pierre and Miquelon"),
            'VC': ('VCT', 670, "Saint Vincent and Grenadines"),
            'WS': ('WSM', 882, "Samoa"),
            'SM': ('SMR', 674, "San Marino"),
            'ST': ('STP', 678, "Sao Tome and Principe"),
            'SA': ('SAU', 682, "Saudi Arabia"),
            'SN': ('SEN', 686, "Senegal"),
            'RS': ('SRB', 688, "Serbia"),
            'SC': ('SYC', 690, "Seychelles"),
            'SL': ('SLE', 694, "Sierra Leone"),
            'SG': ('SGP', 702, "Singapore"),
            'SK': ('SVK', 703, "Slovakia"),
            'SI': ('SVN', 705, "Slovenia"),
            'SB': ('SLB',  90, "Solomon Islands"),
            'SO': ('SOM', 706, "Somalia"),
            'ZA': ('ZAF', 710, "South Africa"),
            'GS': ('SGS', 239, "South Georgia and the South Sandwich Islands"),
            'SS': ('SSD', 728, "South Sudan"),
            'ES': ('ESP', 724, "Spain"),
            'LK': ('LKA', 144, "Sri Lanka"),
            'SD': ('SDN', 736, "Sudan"),
            'SR': ('SUR', 740, "Suriname"),
            'SJ': ('SJM', 744, "Svalbard and Jan Mayen Islands"),
            'SZ': ('SWZ', 748, "Swaziland"),
            'SE': ('SWE', 752, "Sweden"),
            'CH': ('CHE', 756, "Switzerland"),
            'SY': ('SYR', 760, "Syrian Arab Republic (Syria)"),
            'TW': ('TWN', 158, "Taiwan, Republic of China"),
            'TJ': ('TJK', 762, "Tajikistan"),
            'TZ': ('TZA', 834, "Tanzania *, United Republic of"),
            'TH': ('THA', 764, "Thailand"),
            'TL': ('TLS', 626, "Timor-Leste"),
            'TG': ('TGO', 768, "Togo"),
            'TK': ('TKL', 772, "Tokelau"),
            'TO': ('TON', 776, "Tonga"),
            'TT': ('TTO', 780, "Trinidad and Tobago"),
            'TN': ('TUN', 788, "Tunisia"),
            'TR': ('TUR', 792, "Turkey"),
            'TM': ('TKM', 795, "Turkmenistan"),
            'TC': ('TCA', 796, "Turks and Caicos Islands"),
            'TV': ('TUV', 798, "Tuvalu"),
            'UG': ('UGA', 800, "Uganda"),
            'UA': ('UKR', 804, "Ukraine"),
            'AE': ('ARE', 784, "United Arab Emirates"),
            'GB': ('GBR', 826, "United Kingdom"),
            'US': ('USA', 840, "United States of America"),
            'UM': ('UMI', 581, "United States Minor Outlying Islands"),
            'UY': ('URY', 858, "Uruguay"),
            'UZ': ('UZB', 860, "Uzbekistan"),
            'VU': ('VUT', 548, "Vanuatu"),
            'VE': ('VEN', 862, "Venezuela (Bolivarian Republic of)"),
            'VN': ('VNM', 704, "Viet Nam"),
            'VI': ('VIR', 850, "Virgin Islands, US"),
            'WF': ('WLF', 876, "Wallis and Futuna Islands"),
            'EH': ('ESH', 732, "Western Sahara"),
            'YE': ('YEM', 887, "Yemen"),
            'ZM': ('ZMB', 894, "Zambia"),
            'ZW': ('ZWE', 716, "Zimbabwe"),
        }

        self.abbrs = {  # Not including final '.'
            "Mr", "Dr", "Mrs", "Ms", "Messr", "Messrs",
            "Rev", "Fr", "St", "Msgnr",
            "Pres", "Gen", "Cpl", "Maj", "Pvt",

            "Jan", "Feb", "Mar", "Apr", "May",
            "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec",
            "Mon", "Tue", "Tues", "Wed", "Weds",
            "Thu", "Thur", "Thurs", "Fri", "Sat", "Sun",

            "Ave", "Blvd", "Rd", "Ln", "St", "Ct",
            "Co", "Inc"
            "i.e", "e.g",
        }

        self.contractionList = {
            # NOT
            "can't"             : [ "can not"               , "MD NEG" ],
            "won't"             : [ "will not"              , "MD NEG" ],
            "shan't"            : [ "shall not"             , "MD NEG" ],
            "ain't"             : [ "is not"                , "BE NEG" ],
            "can't've"          : [ "can not have"          , "MD NEG HV" ],
            "won't've"          : [ "will not have"         , "MD NEG HV" ],
            "tain't"            : [ "it is not"             , "PRO BE NEG" ],

            # Regular
            "mayn't"            : [ "may not"               , "MD NEG" ],
            "mustn't"           : [ "must not"              , "MD NEG" ],
            "mightn't"          : [ "might not"             , "MD NEG" ],
            "wouldn't"          : [ "would not"             , "MD NEG" ],
            "couldn't"          : [ "could not"             , "MD NEG" ],
            "shouldn't"         : [ "should not"            , "MD NEG" ],
            "don't"             : [ "do not"                , "DO NEG" ],
            "doesn't"           : [ "does not"              , "DOZ NEG" ],
            "didn't"            : [ "did not"               , "DOD NEG" ],
            "haven't"           : [ "have not"              , "HV NEG" ],
            "hasn't"            : [ "has not"               , "HVZ NEG" ],
            "hadn't"            : [ "had not"               , "HVD NEG" ],

            "aren't"            : [ "are not"               , "BE NEG" ],
            "isn't"             : [ "is not"                , "BE NEG" ],
            "wasn't"            : [ "was not"               , "BE NEG" ],
            "weren't"           : [ "were not"              , "BE NEG" ],

            "shouldn't've"      : [ "should not have"       , "MD NEG HV" ],
            "wouldn't've"       : [ "would not have"        , "MD NEG HV" ],
            "couldn't've"       : [ "could not have"        , "MD NEG HV" ],
            "mightn't've"       : [ "might not have"        , "MD NEG HV" ],
            "mayn't've"         : [ "may not have"          , "MD NEG HV" ],


            # HAS and HAVE
            #
            #"NN's"             : [ "NN's"                  , "" ],
            #"NNS've"           : [ "NNS've"                , "" ],

            "I've"              : [ "I have"                , "PRP HV" ],
            "we've"             : [ "we have"               , "PRP HV" ],
            "you've"            : [ "you have"              , "PRP HV" ],
            "they've"           : [ "they have"             , "PRP HV" ],
            "these've"          : [ "these have"            , "PRO HV" ],
            "those've"          : [ "those have"            , "PRO HV" ],

            "should've"         : [ "should have"           , "MD HV" ],
            "would've"          : [ "would have"            , "MD HV" ],
            "could've"          : [ "could have"            , "MD HV" ],
            "might've"          : [ "might have"            , "MD HV" ],
            "may've"            : [ "may have"              , "MD HV" ],
            "can've"            : [ "can have"              , "MD HV" ],
            "will've"           : [ "will have"             , "MD HV" ],

            "who've"            : [ "who have"              , "WP HV" ],
            "where've"          : [ "where have"            , "WP HV" ],
            "what've"           : [ "what have"             , "WP HV" ],
            "when've"           : [ "when have"             , "WP HV" ],
            "why've"            : [ "why have"              , "WP HV" ],
            "how've"            : [ "how have"              , "WP HV" ],


            # IS/ARE
            #
            #"NN's"             : [ "NN's"                  , "PRP BE" ],
            #"NNS're"           : [ "NNS're"                , "PRP BE" ],
            "I'm"               : [ "I am"                  , "PRP BE" ],
            "we're"             : [ "we are"                , "PRP BE" ],
            "you're"            : [ "you are"               , "PRP BE" ],
            "he's"              : [ "he is"                 , "PRP BE" ],
            "she's"             : [ "she is"                , "PRP BE" ],
            "they're"           : [ "they are"              , "PRP BE" ],
            "it's"              : [ "it is"                 , "PRP BE" ],

            "there's"           : [ "there is"              , "PRP BE" ],
            "all's"             : [ "all is"                , "PRP BE" ],
            "anybody's"         : [ "anybody is"            , "PRP BE" ],
            "everybody's"       : [ "everybody is"          , "PRP BE" ],
            "somebody's"        : [ "somebody is"           , "PRP BE" ],
            "nobody's"          : [ "nobody is"             , "PRP BE" ],

            "who's"             : [ "who is"                , "WP BE" ],
            "where's"           : [ "where is"              , "WP BE" ],
            "what's"            : [ "what is"               , "WP BE" ],
            "when's"            : [ "when is"               , "WP BE" ],
            "why's"             : [ "why is"                , "WP BE" ],
            "how's"             : [ "how is"                , "WP BE" ],

            "who're"            : [ "who are"               , "WP BE" ],
            "where're"          : [ "where are"             , "WP BE" ],
            "what're"           : [ "what are"              , "WP BE" ],
            "when're"           : [ "when are"              , "WP BE" ],
            "why're"            : [ "why are"               , "WP BE" ],
            "how're"            : [ "how are"               , "WP BE" ],

            "that's"            : [ "that is"               , "PRO BE" ],
            "these're"          : [ "these are"             , "PRO BE" ],
            "those're"          : [ "those are"             , "PRO BE" ],


            # WILL
            #
            #"NN'll"             : [ "NN'll"                 , "" ],

            "I'll"              : [ "I will"                , "" ],
            "we'll"             : [ "we will"               , "" ],
            "you'll"            : [ "you will"              , "" ],
            "he'll"             : [ "he will"               , "" ],
            "she'll"            : [ "she will"              , "" ],
            "they'll"           : [ "they will"             , "" ],
            "it'll"             : [ "it will"               , "" ],

            "there'll"          : [ "there will"            , "" ],
            "all'l"             : [ "all will"              , "" ],
            "anybody'll"        : [ "anybody will"          , "" ],
            "everybody'll"      : [ "everybody will"        , "" ],
            "somebody'll"       : [ "somebody will"         , "" ],
            "nobody'll"         : [ "nobody will"           , "" ],

            "who'll"            : [ "who will"              , "" ],
            "where'll"          : [ "where will"            , "" ],
            "what'll"           : [ "what will"             , "" ],
            "when'll"           : [ "when will"             , "" ],
            "why'll"            : [ "why will"              , "" ],
            "how'll"            : [ "how will"              , "" ],

            "that'll"           : [ "that will"             , "" ],
            "this'll"           : [ "this will"             , "" ],
            "these'll"          : [ "these will"            , "" ],
            "those'll"          : [ "those will"            , "" ],


            # WOULD (these can all also take "'ve")
            #
            #"NN'd"              : [ "NN'd"                  , "" ],
            #"NNS'd"             : [ "NNS'd"                 , "" ],

            "I'd"               : [ "I would"               , "" ],
            "we'd"              : [ "we would"              , "" ],
            "you'd"             : [ "you would"             , "" ],
            "he'd"              : [ "he would"              , "" ],
            "she'd"             : [ "she would"             , "" ],
            "they'd"            : [ "they would"            , "" ],
            "it'd"              : [ "it would"              , "" ],

            "there'd"           : [ "there would"           , "" ],
            "all'd"             : [ "all would"             , "" ],
            "anybody'd"         : [ "anybody would"         , "" ],
            "everybody'd"       : [ "everybody would"       , "" ],
            "somebody'd"        : [ "somebody would"        , "" ],
            "nobody'd"          : [ "nobody would"          , "" ],

            "who'd"             : [ "who would"             , "" ],
            "where'd"           : [ "where would"           , "" ],
            "what'd"            : [ "what would"            , "" ],
            "when'd"            : [ "when would"            , "" ],
            "why'd"             : [ "why would"             , "" ],
            "how'd"             : [ "how would"             , "" ],

            "that'd"            : [ "that would"            , "" ],
            "this'd"            : [ "this would"            , "" ],
            "these'd"           : [ "these would"           , "" ],
            "those'd"           : [ "those would"           , "" ],

            "let's"             : [ "let us"                , "" ],
            "let'r"             : [ "let her"               , "" ],
            "let'm"             : [ "let him"               , "" ], # "let them"

            "y'all"             : [ "you all"               , "" ],
            "y'know"            : [ "you know"              , "" ],
            "ye're"             : [ "you are"               , "" ],
            "'tis"              : [ "it is"                 , "" ],
            "g'ahn"             : [ "go on"                 , "" ],

            "lighter'n"         : [ "lighter than"          , "" ],
            "more'n"            : [ "more than"             , "" ],
            "tug-o'-war"        : [ "tug of war"            , "" ],
            "will-o'-the-wisp"  : [ "will-of-the-wisp"      , "" ],
            "c'mon"             : [ "c'mon"                 , "" ],

            # Apostrophe-initial
            "'em"               : [ "them"                   , "PPO" ],
            "'til"              : [ "until"                  , "IN" ],

            # NO APOSTROPHE
            "cannot"            : [ "can not"               , "" ],
            "lookit"            : [ "look at"               , "" ],
            "hafta"             : [ "have to"               , "HV TO" ],
            "howda"             : [ "how do"                , "WP DO" ],
            "whaddya"           : [ "whad do you"           , "WP DO PRP" ],
            "willya"            : [ "will you"              , "WP PRP" ],

            "gonna"             : [ "going to"              , "" ],
            "gotta"             : [ "got to"                , "" ],
            "wanna"             : [ "want to"               , "" ],
            "wanta"             : [ "want to"               , "" ],

            "lemme"             : [ "let me"                , "" ],
            "gimme"             : [ "give me"               , "" ],
            "ahm"               : [ "I am"                  , "" ],

            "outta"             : [ "out of"                , "" ],
            "lotta"             : [ "lot of"                , "" ],
            "buncha"            : [ "bunch of"              , "" ],

            "woulda"            : [ "would have"            , "MD HV" ],
            "coulda"            : [ "could have"            , "MD HV" ],
            "shoulda"           : [ "should have"           , "MD HV" ],
            "oughta"            : [ "ought have"            , "MD HV" ],
            "musta"             : [ "must have"             , "MD HV" ],
            "ima"               : [ "i am going to"         , "" ],
            "wadna"             : [ "would not have"        , "" ],

            # FOREIGN
            "D'art"             : [ "D'art"                 , "" ],
            "L'Institut"        : [ "L'Institut"            , "" ],
            "c'est"             : [ "c'est"                 , "" ],
            "dell'"             : [ "dell'"                 , "" ],
            "j'ai"              : [ "j'ai"                  , "" ],
            "s'accuse"          : [ "s'accuse"              , "" ],
            "j'accuse"          : [ "j'accuse"              , "" ],
        }

        self.semiRegularContractionList = {
            # Semi-regular, that require a word before
            "n't"		        : [ "not"                   , [ "MD" ] ],
            "'ve"	            : [ "have"                  , [ "NNS"] ],
            "'ll"		        : [ "will"                  , [ "NN", "NNS" ] ],
            "'n"		        : [ "than"                  , [ "JJR" ] ],
        }

        self.expr = "|".join(self.contractionList.keys())
        self.contExpr = r'\b(' + self.expr + r')\b'

        self.srexpr = "|".join(self.semiRegularContractionList.keys())
        self.srContExpr = r'(\w)(' + self.srexpr + r')\b'  # Remember \\1

        # wh words can take 're 's 'd (some ambiguous)
        self.whContrExpr = r'\b(who|where|what|when|why|how)(\'re|\'s|\'d)\b'


    def doContractions(self, s):
        s = re.sub(r'self.contExpr',
            self.contractionList, s)
        if ("'" not in s): return
        s = re.sub(self.srContExpr,
            self.semiRegularContractionList, s)
        #s = re.sub(self.contExp,
        #    self.contractionList, s)
        return s


#########################################################################
#########################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def processOptions():
        descr = """
=pod

=head1 Description

English-specific reference data for use with tokenizers.
Extracted and ported from Tokenizer.pm and Volsunga, by Steven J. DeRose.

The class provides the following data, almost exclusively English-specific
(comparable classes can be made for other langauges, of course).

Short lists of tokens are provided as "|"-separated strings, which can be
inserted straight into regex matches. These do *not* include an abbreviation
period (perhaps they should?)

=item * B<months> Month names and abbreviations (3-letter plus "Sept").

=item * B<weekdays> Weekday names and abbreviations (3-letter plus "Thur" and "Thurs").


=item * B<relativeDays> "today|tomorrow|yesterday|eve"

=item * B<dayParts> terms for parts of days, such as "noon", "lauds", etc.

=item * B<titles> Personal titles, including some religious, military,
and governmental; and their abbreviations.

=item * B<unitPrefixes> Metric prefixes, such as "kilo".

=back

More complex lists include:

=over

=item * B<countryCodes> A Python C<dict> keyed by 2-letter country code.
The values are 3-tuples of the corresponding 3-letter code, numeric code, and
full name (in ASCII only). For example:
    'FO': ('FRO', 234, "Faroe Islands"),
    'FJ': ('FJI', 242, "Fiji"),

=item * B<contractionList> A Python C<dict> mapping contracted forms to
their (usually) multi-word expansions and (usually) the appropriate POS tags.
For example:
    "those'll"          : [ "those will",            , "" ],
    "I'd"               : [ "I would",               , "" ],
    "we'd"              : [ "we would",              , "" ],

This does not include productive cases such as C<[noun]'s> for possessive
or contracted "is" (see next item)

Note that not all contractions contain apostrophes ("cannot", "gonna", "ima"),
and apostrophes can be token-initial ("'em") or multiple ("you'd've").


=item * B<semiRegularContractionList> Is a Python dict mapping (fairly)
productive contractions to their expansions and a list of the word classes
they apply to. For example:
    "n't"		        : "not",        [ "MD" ] ],
    "'n"	            [ "than",       [ "JJR" ] ],

Cases that are already covered by the explicit I<contractionList>
(such as "I'd"), do not trigger adding their POS to the I<semiRegularContractionList>.

=back

A few more items are derived automatically from the lists already described:

    self.expr = "|".join(self.contractionList.keys())
    self.contExpr = r'\b(' + self.expr + r')\b'
    self.srexpr = "|".join(self.semiRegularContractionList.keys())
    self.srContExpr = r'(\w)(' + self.srexpr + r')\b'  # Remember \\1
    self.whContrExpr = r'\b(who|where|what|when|why|how)(\'re|\'s|\'d)\b'

And finally, one method:

    doContractions(self, s) -- This will take the string I<s>, and replace any
contractions found in I<contractionList>, with their expanded forms. It then
applies the I<semiRegularContractionList>, I<but> it does not check the POS
(since it is only passed a string anyway, without POS tags).


=head1 Related Commands

Tokenize.py, Tokenizer.pm, Volsunga tokenizer (qv).

=head1 Known bugs and Limitations

The lists are English specific, and some (like abbreviations) are (like
Wikipedia's "List of Numbers"), necessarily incomplete.

=head1 Licensing

Copyright 2012, 2018 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

=head1 Options
"""
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--oencoding",        type=str, metavar='E',
            help='Use this character set for output files.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--simple",           action='store_true',
            help='Use Simple instead of Heavy tokenizer.')
        parser.add_argument(
            "--unicode",          action='store_const',  dest='iencoding',
            const='utf8', help='Assume utf-8 for input files.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)
