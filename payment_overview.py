from typing import Literal
from tabulate import tabulate


from Helpfulfunctions import *


MAX_NUMBER_OF_COLUMNS_ON_SCREEN=5



def ZahlungsübersichtnachZeiten(dimension: Literal["Monat","Jahr"],onlyoneyear=True,year="2025")->list[tuple]:
    if onlyoneyear:
        whereClause=" WHERE Jahr=?"
        parameters=(year,)
    else:
        whereClause=""
        parameters=()
    Query=f"""
        SELECT * FROM Zahlungsübersicht{dimension}
        """+whereClause
    with sqlite3.connect(DBNAME) as connection:
        return connection.execute(Query,parameters).fetchall()

def FormatierteEintraegeZahlungsübersichtZeilen(year,headers,mode:Literal["Monat","Jahr"]):
    QueryresultMonat=ZahlungsübersichtnachZeiten(mode,onlyoneyear=True,year=year)
    Numberofentries=12 if mode=="Monat" else 1
    In=[["" for i in headers] for j in range(Numberofentries)]
    Out=[["" for i in headers] for j in range(Numberofentries)]
    InOut=[Out,In]
    for Zeile in QueryresultMonat:
        BetragPositiv: Literal[0,1]=Zeile[1]
        Kategorie: str=Zeile[0]
        if mode=="Monat":
            Monat=int(Zeile[4])
        Total=Zeile[2]
        assert Zeile[3]==year
        if Kategorie in headers:
            InOut[BetragPositiv][Monat-1 if mode=="Monat" else 0][headers.index(Kategorie)]=str(Total)
    LeftsideHeader=Monate if mode=="Monat" else {1: "Insgesamt: "}
    print(In)
    Data=[
        [
            f"{In[i][j-1]}{"/" if In[i][j-1]!="" and Out[i][j-1]!="" else ""} {Out[i][j-1]}" if j!=0 else LeftsideHeader[i+1] for j in range(len(In[i])+1)
            ]
        for i in range(len(In))
        ]
    return Data


def Zahlungsübersicht():
    year="2025"
    QueryresultJahr=ZahlungsübersichtnachZeiten("Jahr",onlyoneyear=True,year=year)
    KategorienOrdnung=most_relevant_categories()
    getcategories()
    headers=KategorienOrdnung[:MAX_NUMBER_OF_COLUMNS_ON_SCREEN]
    # sideheaders=[str(i)+" "+inout for i in range(1,13) for inout in ["Out","In"]]
    DataMonth=FormatierteEintraegeZahlungsübersichtZeilen(year,headers,"Monat")
    DataYear=FormatierteEintraegeZahlungsübersichtZeilen(year,headers,"Jahr")
    Data=DataMonth+DataYear
    root=tkinter.Tk()
    root.state("zoomed")
    tabelle=tkinter.Text(root, font=("Courier New", 10))
    tabelle.insert(tkinter.END,tabulate(Data, headers=[""]+headers,tablefmt="grid"))
    tabelle.pack(expand=True, fill="both")
    root.bind("<Return>",lambda e: root.destroy(

    ))
    root.mainloop()