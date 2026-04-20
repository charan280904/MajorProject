DENTAL_KB = {

# ============================================================
# 1. DENTAL CARIES
# ============================================================
"caries": {
    "description": "Tooth decay caused by acid-producing bacteria damaging enamel.",
    
    "causes": [
        "High sugar consumption",
        "Poor oral hygiene",
        "Bacterial plaque accumulation",
        "Frequent snacking",
        "Low fluoride exposure"
    ],

    "symptoms": [
        "Tooth pain",
        "Visible holes",
        "Sensitivity to hot/cold",
        "Bad breath"
    ],

    "risk_factors": [
        "Sugary diet",
        "Not brushing twice daily",
        "Skipping dental visits",
        "Dry mouth"
    ],

    "lifestyle_risks": {
        "brush_once": "Increases plaque buildup and decay risk",
        "sweets": "Primary cause of caries",
        "softdrinks": "Acid erosion and sugar damage"
    },

    "recommendations": {
        "general": [
            "Brush twice daily with fluoride toothpaste",
            "Use dental floss regularly",
            "Rinse mouth after meals",
            "Limit sugar intake"
        ],

        "lifestyle_based": {
            "sweets": "Reduce sugary foods significantly",
            "softdrinks": "Avoid carbonated drinks",
            "brush_once": "Increase brushing frequency to twice daily"
        }
    },

    "daily_routine": {
        "morning": [
            "Brush with fluoride toothpaste",
            "Avoid sugary breakfast"
        ],
        "afternoon": [
            "Rinse after meals",
            "Drink water instead of sugary drinks"
        ],
        "night": [
            "Brush before sleep",
            "Floss thoroughly"
        ]
    },

    "treatment": [
        "Fluoride treatment",
        "Dental fillings",
        "Root canal (if severe)"
    ],

    "severity_rules": {
        "high": "Pain + visible cavity",
        "medium": "Sensitivity",
        "low": "Early enamel damage"
    }
},

# ============================================================
# 2. CALCULUS
# ============================================================
"calculus": {
    "description": "Hardened plaque (tartar) that sticks to teeth and gums.",
    
    "causes": [
        "Poor brushing habits",
        "Plaque accumulation",
        "Mineralized deposits"
    ],

    "symptoms": [
        "Yellow or brown deposits",
        "Bad breath",
        "Gum irritation"
    ],

    "risk_factors": [
        "Irregular brushing",
        "Smoking",
        "Lack of flossing"
    ],

    "lifestyle_risks": {
        "tobacco": "Accelerates tartar formation",
        "poor_hygiene": "Main cause"
    },

    "recommendations": {
        "general": [
            "Brush twice daily",
            "Use tartar-control toothpaste",
            "Floss daily"
        ],

        "lifestyle_based": {
            "tobacco": "Stop tobacco usage",
            "brush_once": "Improve brushing frequency"
        }
    },

    "daily_routine": {
        "morning": ["Brush thoroughly"],
        "afternoon": ["Rinse mouth"],
        "night": ["Floss and brush"]
    },

    "treatment": [
        "Professional scaling",
        "Deep cleaning"
    ],

    "severity_rules": {
        "high": "Heavy deposits",
        "medium": "Visible tartar",
        "low": "Early buildup"
    }
},

# ============================================================
# 3. GINGIVITIS
# ============================================================
"gingivitis": {
    "description": "Inflammation of gums due to plaque buildup.",
    
    "causes": [
        "Plaque accumulation",
        "Poor oral hygiene",
        "Smoking"
    ],

    "symptoms": [
        "Bleeding gums",
        "Swelling",
        "Redness"
    ],

    "risk_factors": [
        "Smoking",
        "Diabetes",
        "Poor brushing"
    ],

    "lifestyle_risks": {
        "tobacco": "Worsens gum inflammation",
        "diabetes": "Increases infection risk"
    },

    "recommendations": {
        "general": [
            "Brush gently with soft brush",
            "Use antiseptic mouthwash",
            "Floss daily"
        ],

        "lifestyle_based": {
            "tobacco": "Stop smoking immediately",
            "diabetes": "Maintain blood sugar control"
        }
    },

    "daily_routine": {
        "morning": ["Brush gently", "Salt water rinse"],
        "afternoon": ["Stay hydrated"],
        "night": ["Floss carefully", "Use mouthwash"]
    },

    "treatment": [
        "Professional cleaning",
        "Antibacterial treatment"
    ],

    "severity_rules": {
        "high": "Bleeding + swelling",
        "medium": "Red gums",
        "low": "Mild irritation"
    }
},

# ============================================================
# 4. TOOTH DISCOLORATION
# ============================================================
"tooth discoloration": {
    "description": "Change in tooth color due to stains or internal factors.",
    
    "causes": [
        "Coffee/tea",
        "Smoking",
        "Poor hygiene"
    ],

    "symptoms": [
        "Yellowing teeth",
        "Brown stains"
    ],

    "risk_factors": [
        "Smoking",
        "Colored drinks"
    ],

    "lifestyle_risks": {
        "tea": "Causes staining",
        "tobacco": "Severe discoloration"
    },

    "recommendations": {
        "general": [
            "Brush twice daily",
            "Use whitening toothpaste",
            "Rinse after drinks"
        ],

        "lifestyle_based": {
            "tea": "Limit tea/coffee",
            "tobacco": "Quit tobacco"
        }
    },

    "daily_routine": {
        "morning": ["Brush teeth"],
        "afternoon": ["Rinse after drinks"],
        "night": ["Brush again"]
    },

    "treatment": [
        "Teeth whitening",
        "Dental cleaning"
    ],

    "severity_rules": {}
},

# ============================================================
# 5. ULCERS
# ============================================================
"ulcers": {
    "description": "Painful sores inside the mouth.",
    
    "causes": [
        "Stress",
        "Vitamin deficiency",
        "Injury"
    ],

    "symptoms": [
        "Painful sores",
        "Burning sensation"
    ],

    "risk_factors": [
        "Spicy food",
        "Low immunity"
    ],

    "lifestyle_risks": {
        "spicy_food": "Triggers ulcers"
    },

    "recommendations": {
        "general": [
            "Avoid spicy food",
            "Maintain oral hygiene"
        ],

        "lifestyle_based": {}
    },

    "daily_routine": {
        "morning": ["Use mild toothpaste"],
        "afternoon": ["Drink water"],
        "night": ["Apply gel"]
    },

    "treatment": [
        "Topical gels",
        "Vitamin supplements"
    ],

    "severity_rules": {}
},

# ============================================================
# 6. HYPODONTIA
# ============================================================
"hypodontia": {
    "description": "Missing teeth condition.",
    
    "causes": [
        "Genetics",
        "Developmental issues"
    ],

    "symptoms": [
        "Missing teeth",
        "Spacing issues"
    ],

    "risk_factors": [],

    "lifestyle_risks": {},

    "recommendations": {
        "general": [
            "Maintain hygiene in gaps",
            "Regular dental checkups"
        ],

        "lifestyle_based": {}
    },

    "daily_routine": {
        "morning": ["Clean gaps"],
        "afternoon": ["Rinse"],
        "night": ["Floss"]
    },

    "treatment": [
        "Dental implants",
        "Braces",
        "Prosthetics"
    ],

    "severity_rules": {}
}

}