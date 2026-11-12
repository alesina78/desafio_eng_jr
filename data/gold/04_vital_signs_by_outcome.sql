/*
  Indicador 04: Sinais Vitais por Desfecho Clínico
  ----------------------------------------------
  Objetivo:
    Analisar a média de sinais vitais críticos (como temperatura retal 
    e pulsação) associados a cada desfecho final do atendimento.
*/[cite: 4]

SELECT 
    e.outcome_label,
    ROUND(AVG(c.rectal_temperature)::numeric, 2) AS media_temperatura_retal,
    ROUND(AVG(c.pulse)::numeric, 2) AS media_pulso,
    ROUND(AVG(c.respiratory_rate)::numeric, 2) AS media_frequencia_respiratoria,
    COUNT(e.case_id) AS amostra_total
FROM 
    equine_cases e
JOIN 
    clinical_measures c ON e.case_id = c.case_id
WHERE 
    e.outcome_label IS NOT NULL
GROUP BY 
    e.outcome_label
ORDER BY 
    media_pulso ASC;