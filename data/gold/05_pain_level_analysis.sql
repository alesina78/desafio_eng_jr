/*
  Indicador 05: Análise do Nível de Dor vs Desfecho
  -----------------------------------------------
  Objetivo:
    Verificar a correlação entre o nível de dor registrado na triagem 
    e a taxa de mortalidade/eutanásia dos casos.
*/[cite: 3]

SELECT 
    c.pain,
    e.outcome_label,
    COUNT(e.case_id) AS total_casos
FROM 
    equine_cases e
JOIN 
    clinical_measures c ON e.case_id = c.case_id
WHERE 
    c.pain IS NOT NULL AND e.outcome_label IS NOT NULL
GROUP BY 
    c.pain,
    e.outcome_label
ORDER BY 
    c.pain, 
    total_casos DESC;