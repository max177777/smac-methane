from __future__ import annotations
"""
Policy, sector, and pathway content for the 11 pilot countries.
Curated, literature-derived. Used by the country profile, dashboard,
and the methane chat assistant.
"""

POLICY = {
    "USA": {
        "summary": "The world's largest oil & gas producer carries a methane footprint dominated by upstream and midstream operations, with Texas, Pennsylvania, and Louisiana driving most of the variance. Federal rules set a floor; state rules drive the ceiling.",
        "governance": "Federal government plus 50 states with independent climate authority. Methane regulation is split between the EPA's federal performance standards and state-level rules that often go further.",
        "policies": [
            ("EPA OOOOb/c (2024)", "Federal performance standards for new and existing oil & gas sources; LDAR, flaring restrictions, pneumatic device retrofits."),
            ("IRA §136 — Methane Emissions Reduction Program", "Charge of up to $1,500/tonne on facilities exceeding intensity thresholds; first methane fee in any country."),
            ("State rules", "Colorado intensity standard, New Mexico waste rule, California cap-and-invest, Pennsylvania VOC rule. Strong subnational variation."),
        ],
    },
    "BRA": {
        "summary": "Brazil's methane profile is overwhelmingly agricultural — enteric fermentation from the world's second-largest cattle herd, plus land-use-related emissions concentrated in the Amazon and Cerrado states.",
        "governance": "Federal government plus 27 states (federation) with shared environmental authority. State-level implementation is critical for land-use methane.",
        "policies": [
            ("Plano ABC+ (2020–2030)", "Federal low-carbon agriculture plan; integrated crop-livestock-forest systems."),
            ("Global Methane Pledge", "Brazil committed to a 30% methane reduction by 2030 from 2020 levels."),
            ("PNMC (National Climate Policy)", "Sectoral plans implemented by states; Pará, Mato Grosso, and São Paulo carry most of the methane abatement obligation."),
        ],
    },
    "CAN": {
        "summary": "Canada is a small absolute emitter but methane-intensive on a per-barrel basis. Alberta and British Columbia carry most of the upstream load; agricultural methane is concentrated in the Prairie provinces.",
        "governance": "Federal government plus 13 provinces and territories with concurrent jurisdiction. Equivalency agreements let provinces run their own regimes.",
        "policies": [
            ("Federal Methane Regs (2023 amendments)", "Targeting a 75% reduction in oil & gas methane by 2030 from 2012 levels — the most ambitious national target."),
            ("Equivalency Agreements", "Alberta, BC, and Saskatchewan run provincial regimes deemed equivalent to the federal rules."),
            ("Federal Landfill Methane Regs", "Proposed rules to mandate landfill gas capture at large municipal sites."),
        ],
    },
    "DEU": {
        "summary": "Germany's methane is driven by agriculture and waste; oil & gas is small. EU-wide regulation now sets the pace.",
        "governance": "Federal government plus 16 Länder. EU regulation increasingly binds the national framework.",
        "policies": [
            ("EU Methane Regulation (2024)", "Binding LDAR, venting and flaring limits, import standards from 2027."),
            ("Federal Climate Protection Act", "Sectoral targets including waste and agriculture."),
            ("Bundesländer programs", "Bavaria, Lower Saxony lead on agricultural methane via biogas capture."),
        ],
    },
    "IND": {
        "summary": "Methane in India is dominated by enteric fermentation and rice cultivation. Subnational variation tracks agro-ecological zones.",
        "governance": "Union government plus 28 states and 8 union territories. State agriculture ministries shape methane outcomes.",
        "policies": [
            ("GOBARdhan Scheme", "Biogas capture from cattle manure; rolling out across rural India."),
            ("National Action Plan on Climate Change", "Eight missions covering agriculture, water, sustainable habitat."),
            ("State agricultural plans", "Punjab, Haryana drive rice-paddy methane decisions; Uttar Pradesh leads on cattle."),
        ],
    },
    "KOR": {
        "summary": "Korea's methane is dominated by waste and a smaller agricultural share. Centralised regulation, limited subnational variation.",
        "governance": "National government plus 17 provinces and metropolitan cities. Highly centralised climate policy.",
        "policies": [
            ("Framework Act on Carbon Neutrality (2022)", "Statutory 40% reduction by 2030."),
            ("K-ETS", "National emissions trading covers some methane sources."),
            ("Waste sector targets", "Mandatory landfill gas capture at major sites."),
        ],
    },
    "MEX": {
        "summary": "Mexico has substantial oil & gas methane (Veracruz, Tabasco, Campeche) plus agricultural methane in the central highlands. Regulatory enforcement is the binding constraint, not data.",
        "governance": "Federal government plus 32 states. CONAGUA, SEMARNAT, ASEA share methane oversight.",
        "policies": [
            ("NOM-EM-001-ASEA-2017", "Methane control in upstream oil & gas (suspended in 2024 — major regulatory gap)."),
            ("General Climate Change Law", "Sets sectoral targets but enforcement is uneven."),
            ("Global Methane Pledge", "Mexico signed but has not finalised an implementation plan."),
        ],
    },
    "NGA": {
        "summary": "Nigeria's methane is split between Niger Delta oil & gas flaring/venting and agricultural methane in the northern states. Flaring is the headline issue.",
        "governance": "Federal government plus 36 states and FCT. Niger Delta states dominate oil & gas methane.",
        "policies": [
            ("Decade of Gas (2021–2030)", "Plan to monetise associated gas and reduce flaring."),
            ("Flare Gas Commercialisation Programme", "Auctions of flare-gas access to third-party developers."),
            ("Climate Change Act 2021", "Establishes National Council on Climate Change."),
        ],
    },
    "ZAF": {
        "summary": "South Africa's methane is dominated by coal mining (Mpumalanga) and waste. Coal mine methane is a focal mitigation opportunity.",
        "governance": "National government plus 9 provinces. Mpumalanga dominates coal methane.",
        "policies": [
            ("Climate Change Act (2024)", "Statutory carbon budgets, sector emission targets."),
            ("Carbon Tax", "Now applies to methane on a CO₂e basis."),
            ("Just Energy Transition Partnership", "$8.5B international finance for coal phase-out."),
        ],
    },
    "ARG": {
        "summary": "Argentina's methane is dominated by enteric fermentation in Buenos Aires Province, Santa Fe, and Córdoba, with growing oil & gas methane from Neuquén.",
        "governance": "Federal government plus 24 provinces. Buenos Aires Province alone hosts the bulk of cattle.",
        "policies": [
            ("National Climate Plan 2030", "Sectoral targets for agriculture, energy, waste."),
            ("Vaca Muerta development", "Major shale gas play — methane intensity is a watch item."),
            ("Provincial agricultural extension", "Largest beef-producing provinces shape mitigation."),
        ],
    },
    "ESP": {
        "summary": "Spain's methane is split across agriculture, waste, and a small oil & gas share. Catalonia and Andalusia dominate waste-sector methane.",
        "governance": "Central government plus 17 autonomous communities. EU regulation binds the framework.",
        "policies": [
            ("Climate Change and Energy Transition Law (2021)", "Statutory targets for 2030 and 2050."),
            ("EU Methane Regulation", "Now applies; LDAR and import standards."),
            ("Autonomous-community plans", "Galicia, Castile and León lead on agricultural methane."),
        ],
    },
}


# Sector decomposition: % share of national CH4 (literature-derived approximations)
SECTORS = {
    "USA": [
        ("Oil & Gas", 38), ("Enteric Fermentation", 27), ("Landfills", 17),
        ("Manure Management", 9), ("Coal Mining", 5), ("Other", 4),
    ],
    "BRA": [
        ("Enteric Fermentation", 62), ("Land-use & Burning", 14), ("Landfills", 10),
        ("Manure Management", 6), ("Rice Cultivation", 4), ("Other", 4),
    ],
    "CAN": [
        ("Oil & Gas", 44), ("Enteric Fermentation", 24), ("Landfills", 18),
        ("Manure Management", 7), ("Coal Mining", 4), ("Other", 3),
    ],
    "DEU": [
        ("Enteric Fermentation", 38), ("Landfills & Waste", 24), ("Manure Management", 18),
        ("Energy", 12), ("Other", 8),
    ],
    "IND": [
        ("Enteric Fermentation", 52), ("Rice Cultivation", 18), ("Landfills & Waste", 14),
        ("Coal Mining", 9), ("Other", 7),
    ],
    "KOR": [
        ("Landfills & Waste", 42), ("Rice Cultivation", 22), ("Enteric Fermentation", 18),
        ("Energy", 12), ("Other", 6),
    ],
    "MEX": [
        ("Oil & Gas", 32), ("Enteric Fermentation", 30), ("Landfills", 22),
        ("Manure Management", 8), ("Other", 8),
    ],
    "NGA": [
        ("Oil & Gas (flaring/venting)", 46), ("Enteric Fermentation", 28),
        ("Landfills & Waste", 14), ("Rice Cultivation", 6), ("Other", 6),
    ],
    "ZAF": [
        ("Coal Mining", 48), ("Enteric Fermentation", 24), ("Landfills & Waste", 18),
        ("Manure Management", 6), ("Other", 4),
    ],
    "ARG": [
        ("Enteric Fermentation", 58), ("Manure Management", 14), ("Oil & Gas", 12),
        ("Landfills", 10), ("Other", 6),
    ],
    "ESP": [
        ("Enteric Fermentation", 36), ("Landfills & Waste", 28), ("Manure Management", 22),
        ("Energy", 8), ("Other", 6),
    ],
}


# Mitigation pathways with anti-greenwashing flags
PATHWAYS = {
    "USA": [
        {"sector": "Oil & Gas", "issue": "Fugitive leaks, venting, flaring inefficiency",
         "actions": ["LDAR quarterly", "Vent capture", "Flare destruction efficiency", "Orphan well plug"],
         "flag": "Watch: 'voluntary' programs without verification"},
        {"sector": "Agriculture", "issue": "Enteric fermentation, manure lagoons",
         "actions": ["Feed additives (3-NOP)", "Anaerobic digesters", "Manure cover & flare"],
         "flag": "Watch: digester credits double-counted as RNG"},
        {"sector": "Waste", "issue": "Landfill gas, organic waste in MSW stream",
         "actions": ["Landfill gas capture", "Organics diversion", "Composting infra"],
         "flag": "Watch: capture rates self-reported without satellite check"},
    ],
    "BRA": [
        {"sector": "Enteric Ferm.", "issue": "Large extensive cattle herd, low productivity",
         "actions": ["Pasture restoration", "Crop-livestock integration", "Genetic improvement"],
         "flag": "Watch: 'sustainable beef' labels without herd-level data"},
        {"sector": "Land Use", "issue": "Burning practices and deforestation linked CH₄",
         "actions": ["Deforestation enforcement", "No-burn protocols", "Indigenous land protection"],
         "flag": "Watch: offset projects in already-protected areas"},
        {"sector": "Waste", "issue": "Open dumps, limited capture infrastructure",
         "actions": ["Sanitary landfill conversion", "LFG capture in São Paulo / RJ", "Municipal organics"],
         "flag": "Watch: capture credits without metering"},
    ],
    "CAN": [
        {"sector": "Oil & Gas", "issue": "Upstream venting in Alberta heavy oil & gas plays",
         "actions": ["LDAR + aerial surveys", "Pneumatic device retrofit", "Venting elimination"],
         "flag": "Watch: provincial equivalency without satellite verification"},
        {"sector": "Agriculture", "issue": "Cattle in Prairie provinces",
         "actions": ["Feed efficiency programs", "Manure storage cover", "Rotational grazing"],
         "flag": "Watch: voluntary protocols without enforcement"},
        {"sector": "Waste", "issue": "Municipal landfills in BC, Ontario, Quebec",
         "actions": ["LFG capture mandate", "Organics diversion", "Compost infra"],
         "flag": "Watch: gaps between proposed federal rule and provincial uptake"},
    ],
    "DEU": [
        {"sector": "Agriculture", "issue": "Enteric fermentation + manure",
         "actions": ["Biogas digesters", "Feed additives", "Slurry cover"],
         "flag": "Watch: biogas credit stacking with EU ETS"},
        {"sector": "Waste", "issue": "Legacy landfills still emitting",
         "actions": ["LFG capture", "Mechanical-biological treatment", "Organics ban"],
         "flag": "Watch: closed-landfill emissions under-reported"},
        {"sector": "Energy", "issue": "Coal mine methane, gas distribution leaks",
         "actions": ["Coal mine drainage", "Distribution-line LDAR"],
         "flag": "Watch: imports without methane intensity disclosure"},
    ],
    "IND": [
        {"sector": "Enteric Ferm.", "issue": "Largest cattle and buffalo population globally",
         "actions": ["Feed quality", "Productivity gains", "Genetic improvement"],
         "flag": "Watch: 'natural farming' claims without measurement"},
        {"sector": "Rice", "issue": "Continuous flooding emits CH₄",
         "actions": ["Alternate wetting & drying", "Direct seeded rice", "SRI methodology"],
         "flag": "Watch: AWD adoption rates self-reported"},
        {"sector": "Waste", "issue": "Open dumping in Tier-2 cities",
         "actions": ["Sanitary landfill conversion", "LFG capture (Delhi, Mumbai)", "Source segregation"],
         "flag": "Watch: dump-to-landfill conversion credits without monitoring"},
    ],
    "KOR": [
        {"sector": "Waste", "issue": "High-density urban landfills",
         "actions": ["LFG capture", "Organics ban", "Anaerobic digestion"],
         "flag": "Watch: incineration substitution shifting impacts"},
        {"sector": "Rice", "issue": "Concentrated paddy regions",
         "actions": ["AWD irrigation", "Drainage timing", "Cultivar selection"],
         "flag": "Watch: subsidy-driven over-application of straw"},
        {"sector": "Agriculture", "issue": "Smaller cattle base, manure-driven",
         "actions": ["Manure cover & flare", "Compost infra", "Feed efficiency"],
         "flag": "Watch: protocol misalignment with K-ETS"},
    ],
    "MEX": [
        {"sector": "Oil & Gas", "issue": "Pemex venting and flaring; Veracruz, Tabasco",
         "actions": ["LDAR", "Vent capture", "Flare efficiency", "Pneumatics retrofit"],
         "flag": "Watch: NOM suspension means gap in enforceable rules"},
        {"sector": "Agriculture", "issue": "Enteric fermentation in central highlands",
         "actions": ["Feed additives", "Pasture management", "Genetic improvement"],
         "flag": "Watch: extension service capacity"},
        {"sector": "Waste", "issue": "Mexico City basin, Monterrey landfills",
         "actions": ["LFG capture", "Sanitary conversion", "Organics diversion"],
         "flag": "Watch: capture rates without third-party check"},
    ],
    "NGA": [
        {"sector": "Oil & Gas", "issue": "Niger Delta flaring and venting",
         "actions": ["Flare-out", "Associated gas monetisation", "Vent elimination"],
         "flag": "Watch: flare-gas auction credibility, sat-verified flare detection"},
        {"sector": "Agriculture", "issue": "Cattle in northern states",
         "actions": ["Feed quality", "Pasture management", "Genetic improvement"],
         "flag": "Watch: pastoralist data gaps"},
        {"sector": "Waste", "issue": "Lagos and Abuja dumps",
         "actions": ["Sanitary landfill conversion", "LFG capture pilots", "Organics composting"],
         "flag": "Watch: capture rates without metering"},
    ],
    "ZAF": [
        {"sector": "Coal Mining", "issue": "Mpumalanga concentration, abandoned mines",
         "actions": ["Mine drainage", "Ventilation air methane", "Abandoned mine plugging"],
         "flag": "Watch: VAM oxidation costs and verification"},
        {"sector": "Agriculture", "issue": "Cattle in Eastern Cape, KZN",
         "actions": ["Feed efficiency", "Genetic improvement", "Pasture management"],
         "flag": "Watch: smallholder data gaps"},
        {"sector": "Waste", "issue": "Gauteng landfills",
         "actions": ["LFG capture", "Organics ban", "Compost infra"],
         "flag": "Watch: capture rates without sat-verification"},
    ],
    "ARG": [
        {"sector": "Enteric Ferm.", "issue": "Beef production in Buenos Aires, Santa Fe",
         "actions": ["Feed efficiency", "Pasture rotation", "Genetic improvement"],
         "flag": "Watch: export-driven 'sustainable beef' without measurement"},
        {"sector": "Oil & Gas", "issue": "Vaca Muerta shale development",
         "actions": ["LDAR", "Vent capture", "Flare efficiency", "Pneumatics retrofit"],
         "flag": "Watch: methane intensity reporting at well level"},
        {"sector": "Waste", "issue": "Buenos Aires metro landfills",
         "actions": ["LFG capture", "Sanitary conversion", "Organics diversion"],
         "flag": "Watch: closed-landfill gas under-reported"},
    ],
    "ESP": [
        {"sector": "Enteric Ferm.", "issue": "Cattle in Galicia, Castile and León",
         "actions": ["Feed additives", "Pasture management", "Productivity gains"],
         "flag": "Watch: PAC funding alignment with methane outcomes"},
        {"sector": "Waste", "issue": "Catalonia, Andalusia landfills",
         "actions": ["LFG capture", "Organics ban", "Compost infra"],
         "flag": "Watch: closed-landfill emissions under-reported"},
        {"sector": "Manure", "issue": "Pig farming concentration in Catalonia, Aragon",
         "actions": ["Slurry cover", "Anaerobic digestion", "Application timing"],
         "flag": "Watch: digester credit double-counting under EU ETS"},
    ],
}


# IPCC AR6 GWP factors (non-fossil CH4)
GWP100 = 27
GWP20 = 80
