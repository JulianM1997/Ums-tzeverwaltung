from typing import Literal
from tabulate import tabulate


from Helpfulfunctions import *


MAX_NUMBER_OF_COLUMNS_ON_SCREEN=6



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
    LeftsideHeader=Monate if mode=="Monat" else {1: f"Insgesamt ({year}): "}
    print(In)
    Data=[
        [
            mergeInOutDataPoint(In[i][j-1],Out[i][j-1]) if j!=0 else LeftsideHeader[i+1] for j in range(len(In[i])+1)
            ]
        for i in range(len(In))
        ]
    return Data

def mergeInOutDataPoint(In:str,Out:str)->str:
    return f"{In}{"/" if In!="" and Out!="" else ""}{Out}"
            

def GesamtSpalteData(Jahr: str)->list[list[str]]:
    datamonth=make_simple_query("SELECT Einnahme, Total, Monat FROM InOutByMonth WHERE Jahr=?",(Jahr,))
    datayear=make_simple_query("SELECT Einnahme, Total FROM InOutByYear WHERE Jahr=?",(Jahr,))
    InData=[[""]for i in range(13)]
    OutData=[[""]for i in range(13)]
    DataMap:dict[bool,list[list[str]]]={True: InData,False:OutData}
    for entry in datamonth:
        In=bool(entry[0])
        Total=entry[1]
        Monat=int(entry[2])
        DataMap[In][Monat-1]=[Total]
    for entry in datayear:
        In=bool(entry[0])
        Total=entry[1]
        DataMap[In][12]=[Total]
    return [[mergeInOutDataPoint(InData[i][0],OutData[i][0])] for i in range(13)]

        


def Zahlungsübersicht(year="2025",index=0):
    QueryresultJahr=ZahlungsübersichtnachZeiten("Jahr",onlyoneyear=True,year=year)
    KategorienOrdnung=most_relevant_categories()
    getcategories()
    headers=KategorienOrdnung[index:min(index+MAX_NUMBER_OF_COLUMNS_ON_SCREEN,len(KategorienOrdnung))]
    # sideheaders=[str(i)+" "+inout for i in range(1,13) for inout in ["Out","In"]]
    DataMonth=FormatierteEintraegeZahlungsübersichtZeilen(year,headers,"Monat")
    DataYear=FormatierteEintraegeZahlungsübersichtZeilen(year,headers,"Jahr")
    MainData=DataMonth+DataYear
    TotalColumn=GesamtSpalteData(year)
    Data=[MainData[i]+TotalColumn[i] for i in range(13)]
    root=tkinter.Tk()
    root.state("zoomed")
    tabelle=tkinter.Text(root, font=("Courier New", 10))
    tabelle.insert(tkinter.END,tabulate(Data, headers=[""]+headers+["Gesamt"],tablefmt="grid"))
    tabelle.pack(expand=True, fill="both")
    root.bind("<Return>",lambda e: root.destroy())
    def move_to_left_or_right(Right:bool):
        nonlocal Do_something_afterwards
        nonlocal index
        step=1 if Right else -1
        if index+step>=0 and index+step+MAX_NUMBER_OF_COLUMNS_ON_SCREEN<=len(KategorienOrdnung):
            Do_something_afterwards=True
            index=index+step
            root.destroy()
    def change_year(Up:bool):
        nonlocal Do_something_afterwards
        nonlocal year
        step=1 if Up else -1
        Do_something_afterwards=True
        year=str(int(year)+step)
        root.destroy()
    root.bind("<Left>",lambda e: move_to_left_or_right(False))
    root.bind("<Right>",lambda e: move_to_left_or_right(True))
    root.bind("<Up>",lambda e: change_year(False))
    root.bind("<Down>",lambda e: change_year(True))
    Do_something_afterwards=False
    root.mainloop()
    if Do_something_afterwards:
        Zahlungsübersicht(year,index)