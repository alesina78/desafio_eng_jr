/*
  Indicador 01: Distribuição Percentual dos Desfechos Clínicos
  ------------------------------------------------------------
  Objetivo: 
    Calcular o volume absoluto e o percentual de cada desfecho 
    hospitalar (sobrevivência, óbito ou eutanásia) com base na tabela limpa 
    da camada Silver ('equine_cases').
*/

SELECT 
    outcome_label AS desfecho_clinico,
    COUNT(case_id) AS total_casos,
    ROUND(
        COUNT(case_id) * 100.0 / SUM(COUNT(case_id)) OVER(), 2
    ) AS percentual_total
FROM 
    equine_cases
WHERE 
    outcome_label IS NOT NULL
GROUP BY 
    outcome_label
ORDER BY 
    total_casos DESC;