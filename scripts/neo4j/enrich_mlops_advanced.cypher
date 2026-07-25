// === ENRICHISSEMENT DES DATA CONTRACTS (CONTRAINTES) ===

MERGE (sc_tel:SemanticConcept {name: 'CameroonianPhoneNumber'})
MERGE (c_tel:Constraint {name: 'phone_format'})
SET c_tel += {type: 'regex', value: '^(\\\\+237|237)?6[2-9][0-9]{7}$', description: 'Format telephone camerounais valide (MTN, Orange, Nexttel)'}
MERGE (sc_tel)-[:HAS_CONSTRAINT]->(c_tel);

MERGE (sc_mon:SemanticConcept {name: 'MonetaryValue'})
MERGE (c_mon:Constraint {name: 'positive_amount'})
SET c_mon += {type: 'min_value', value: 0, description: 'Le montant financier doit etre superieur ou egal a 0'}
MERGE (sc_mon)-[:HAS_CONSTRAINT]->(c_mon);

MERGE (sc_cur:SemanticConcept {name: 'AfricanCurrency'})
MERGE (c_cur:Constraint {name: 'positive_currency_amount'})
SET c_cur += {type: 'min_value', value: 0, description: 'Le montant de transaction en devise locale doit etre superieur ou egal a 0'}
MERGE (sc_cur)-[:HAS_CONSTRAINT]->(c_cur);

// === ENRICHISSEMENT DES SEUILS D'ÉQUITÉ (FAIRNESS GUARDRALLS) ===

MERGE (d_gen:Domain {name: 'general'})
MERGE (f_gen:FairnessThreshold {domain: 'general'})
SET f_gen += {min_disparate_impact: 0.80, max_disparate_impact: 1.25, metric: 'disparate_impact_ratio'}
MERGE (d_gen)-[:HAS_FAIRNESS_THRESHOLD]->(f_gen);

MERGE (d_fin:Domain {name: 'finance'})
MERGE (f_fin:FairnessThreshold {domain: 'finance'})
SET f_fin += {min_disparate_impact: 0.85, max_disparate_impact: 1.20, metric: 'disparate_impact_ratio'}
MERGE (d_fin)-[:HAS_FAIRNESS_THRESHOLD]->(f_fin);
