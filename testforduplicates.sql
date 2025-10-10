SELECT *
FROM Umsaetze 
GROUP BY 
    Wertstellungsdatum,
    AuftraggeberEmpfaenger,
    Buchungstext,
    Verwendungszweck
HAVING count(*)>1;