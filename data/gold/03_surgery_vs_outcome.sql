/*
  Indicador 03: Cirurgia vs Desfecho Clínico
  -----------------------------------------
  Objetivo:
    Comparar as taxas de sucesso entre animais que passaram por 
    intervenção cirúrgica e aqueles tratados de forma conservadora.
*/[cite: 5]

SELECT 
    surgery,
    outcome_label,
    COUNT(case_id) AS total_casos,
    ROUND(
        COUNT(case_id) * 100.0 / SUM(COUNT(case_id)) OVER(PARTITION BY surgery), 2
    ) AS percentual_dentro_do_grupo
FROM 
    equine_cases
WHERE 
    outcome_label IS NOT NULL
GROUP BY 
    surgery,
    outcome_label
ORDER BY 
    surgery, 
    total_casos DESC;