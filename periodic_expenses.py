from Helpfulfunctions import *

Query="""
SELECT 
    AuftraggeberEmpfaenger,
    Betrag,
    count(*) AS Anzahl,
    min(CorrectlyformattedDate) AS StartDate,
    max(CorrectlyformattedDate) AS EndDate
FROM Umsaetze
GROUP BY
    AuftraggeberEmpfaenger,
    Betrag
HAVING Anzahl>1 AND EndDate>=date('now','-3 months');
"""

def periodic_expenses():
    data=make_simple_read_query_and_get_headers_as_first_line(Query)
    headers=data.pop(0)
    Startindex=headers.index("StartDate")
    Endindex=headers.index("EndDate")
    reformatedData=[
        tuple(
            reformatDate(entry) if i in [Startindex,Endindex]
            else entry 
            for i,entry in enumerate(row)
            ) 
        for row in data]
    displayTable(headers,reformatedData)
    