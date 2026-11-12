/*
  Indicador 02: Taxa de Sobrevivência por Tipo de Lesão
  ----------------------------------------------------
  Objetivo:
    Avaliar o impacto do tipo de lesão diagnosticada no desfecho 
    clínico dos animais atendidos.
*/[cite: 6]

SELECT 
    surgical_lesion,
    COUNT(case_id) AS total_casos,
    SUM(CASE WHEN outcome_label = 'lived' THEN 1 ELSE 0 END) AS total_sobreviventes,
    ROUND(
        SUM(CASE WHEN outcome_label = 'lived' THEN 1 ELSE 0 END) * 100.0 / COUNT(case_id), 2
    ) AS taxa_sobrevivencia_pct
FROM 
    equine_cases
GROUP BY 
    surgical_lesion
ORDER BY 
    taxa_sobrevivencia_pct DESC;