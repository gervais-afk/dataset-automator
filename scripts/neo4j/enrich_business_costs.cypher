// === ENRICHISSEMENT DES COÛTS ET GAINS MÉTIERS PAR DÉFAUT (RAG) ===

MERGE (d_edu:Domain {name: 'education'})
MERGE (d_tel:Domain {name: 'telecom'})
MERGE (d_fin:Domain {name: 'finance'})
MERGE (d_gen:Domain {name: 'general'});

MERGE (c_edu:BusinessCost {domain: 'education'})
SET c_edu += {cost_FP: 1000, cost_FN: 10000, gain_TP: 2000, currency: 'FCFA'};

MERGE (c_tel:BusinessCost {domain: 'telecom'})
SET c_tel += {cost_FP: 2500, cost_FN: 25000, gain_TP: 5000, currency: 'FCFA'};

MERGE (c_fin:BusinessCost {domain: 'finance'})
SET c_fin += {cost_FP: 5000, cost_FN: 50000, gain_TP: 10000, currency: 'FCFA'};

MERGE (c_gen:BusinessCost {domain: 'general'})
SET c_gen += {cost_FP: 2000, cost_FN: 20000, gain_TP: 4000, currency: 'FCFA'};
