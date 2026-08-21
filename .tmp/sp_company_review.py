"""Batch SP company review helper - prints SOQL fragments and company list."""
COMPANIES = [
    "Anderson Custom Window Coverings, Inc.",
    "Atlantic Window Coverings",
    "Bigelow Refrigeration",
    "DesignTeam Inc",
    "Just Rite Acoustics",
    "Ryan Fireprotection, Inc",
    "Service Pro Locksmith",
    "Ambius Nashville",
    "Crespo's Wildlife Solutions LLC",
    "Glass Doctor of Finger Lakes",
    "Jiffy Rooter, LLC",
    "Luxeshine Cleaning NY 8 LLC",
    "Northmen Glass LLC",
    "Summit Fire & Security LLC",
    "Summit Fire National Accounts",
    "The Flying Locksmiths - Sarasota",
    "The Village Locksmith",
    "Epic Septic & Service LLC",
    "TS Backflow",
    "Precision Locksmith & Door Maintenance",
    "C&K Paving Contractors, Inc",
    "G&H WorX",
    "Richards Board Up Service",
    "Franks Appliance Repair",
    "Johnson Equipment Company",
]

SEARCH_TERMS = {
    "Anderson Custom Window Coverings, Inc.": ["Anderson Custom Window", "Anderson Custom"],
    "Atlantic Window Coverings": ["Atlantic Window Coverings", "Atlantic Window"],
    "Bigelow Refrigeration": ["Bigelow Refrigeration", "Bigelow"],
    "DesignTeam Inc": ["DesignTeam", "Design Team"],
    "Just Rite Acoustics": ["Just Rite Acoustics", "Just Rite"],
    "Ryan Fireprotection, Inc": ["Ryan Fireprotection", "Ryan Fire"],
    "Service Pro Locksmith": ["Service Pro Locksmith"],
    "Ambius Nashville": ["Ambius Nashville", "Ambius"],
    "Crespo's Wildlife Solutions LLC": ["Crespo Wildlife", "Crespo"],
    "Glass Doctor of Finger Lakes": ["Glass Doctor Finger", "Glass Doctor of Finger"],
    "Jiffy Rooter, LLC": ["Jiffy Rooter"],
    "Luxeshine Cleaning NY 8 LLC": ["Luxeshine Cleaning", "Luxeshine"],
    "Northmen Glass LLC": ["Northmen Glass", "Northmen"],
    "Summit Fire & Security LLC": ["Summit Fire & Security", "Summit Fire"],
    "Summit Fire National Accounts": ["Summit Fire National", "Summit National Accounts"],
    "The Flying Locksmiths - Sarasota": ["Flying Locksmiths Sarasota", "Flying Locksmiths"],
    "The Village Locksmith": ["Village Locksmith"],
    "Epic Septic & Service LLC": ["Epic Septic", "Epic Septic & Service"],
    "TS Backflow": ["TS Backflow"],
    "Precision Locksmith & Door Maintenance": ["Precision Locksmith", "Precision Locksmith & Door"],
    "C&K Paving Contractors, Inc": ["C&K Paving", "C and K Paving"],
    "G&H WorX": ["G&H WorX", "G and H WorX"],
    "Richards Board Up Service": ["Richards Board Up", "Richards Board"],
    "Franks Appliance Repair": ["Franks Appliance", "Frank Appliance"],
    "Johnson Equipment Company": ["Johnson Equipment"],
}

if __name__ == "__main__":
    for company in COMPANIES:
        terms = SEARCH_TERMS.get(company, [company.split(",")[0]])
        like = " OR ".join(f"Name LIKE '%{t.replace(chr(39), chr(92)+chr(39))}%'" for t in terms)
        print(f"--- {company} ---")
        print(f"SELECT Id, Name, Service_Provider_Number__c FROM Account WHERE Type = 'Service Provider' AND ({like}) LIMIT 5")
