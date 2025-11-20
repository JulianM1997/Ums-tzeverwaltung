from typing import Literal
from tabulate import tabulate
import textwrap

from Helpfulfunctions import *


MAX_NUMBER_OF_COLUMNS_ON_SCREEN=5
MAX_HEADER_WIDTH=20




def ConvertqueryresultwithX_Y_ValueColumns_TO_XxY_Table_and_unite_pos_and_neg_values(Queryresult:list[tuple],headerlist:tuple[str],XColumnName:str,YColumnName:str,ValueColumnName:str,PossibleXvalues:list,InterestingYvalues:list[str]):
    In=[["" for i in InterestingYvalues] for j in PossibleXvalues]
    Out=[["" for i in InterestingYvalues] for j in PossibleXvalues]
    InOut=[Out,In]
    for Zeile in Queryresult:
        Yvalue: str=Zeile[headerlist.index(YColumnName)]
        Xvalue=Zeile[headerlist.index(XColumnName)]
        print(Xvalue,PossibleXvalues)
        assert Xvalue in PossibleXvalues
        Value=int(Zeile[headerlist.index(ValueColumnName)])
        ValuePositive=Value>=0
        if Yvalue in InterestingYvalues:
            InOut[ValuePositive][PossibleXvalues.index(Xvalue)][InterestingYvalues.index(Yvalue)]=str(Value)
    Data=[
        [
            mergeInOutDataPoint(In[i][j],Out[i][j]) for j in range(len(In[i]))
            ]
        for i in range(len(In))
        ]
    return Data

def appendleftsideheaderstotable(data:list[list[str]],leftsideheaders:list[str])->list[list[str]]:
    return [[leftsideheaders[i]]+row for i,row in enumerate(data)]


def TabellenWerteZahlungsübersichtZeilen(year:str,headers:list[str],mode:Literal["Monat","Jahr"],Queryheaders:tuple[str],Queryresult:list[tuple],ColumnNameOfHeaderinQuery:str):
    Leftsideheaders=MONATE if mode=="Monat" else [year]
    Data=ConvertqueryresultwithX_Y_ValueColumns_TO_XxY_Table_and_unite_pos_and_neg_values(
        Queryresult,
        Queryheaders,
        XColumnName=mode,
        YColumnName=ColumnNameOfHeaderinQuery,
        ValueColumnName="Total",
        PossibleXvalues=([f"{i:02d}" for i in range(1,13)] if mode=="Monat" else [year]),
        InterestingYvalues=headers
        )
    return appendleftsideheaderstotable(Data,Leftsideheaders)


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


def Zahlungsübersicht_neu(ColumnOrdnung:list[str],MonthlydataQuery:str,YeardataQuery:str,ColumnNameofHeaderinQuery:str,year="2025",index=0):
    headers=ColumnOrdnung[index:min(index+MAX_NUMBER_OF_COLUMNS_ON_SCREEN,len(ColumnOrdnung))]
    # sideheaders=[str(i)+" "+inout for i in range(1,13) for inout in ["Out","In"]]
    MonthlydataQueryResult=make_simple_read_query_and_get_headers_as_first_line(MonthlydataQuery,(year,))
    YeardataQueryResult=make_simple_read_query_and_get_headers_as_first_line(YeardataQuery,(year,))
    TableDataMonth=TabellenWerteZahlungsübersichtZeilen(year,headers,"Monat",MonthlydataQueryResult.pop(0),MonthlydataQueryResult,ColumnNameofHeaderinQuery)
    TableDataYear=TabellenWerteZahlungsübersichtZeilen(year,headers,"Jahr",YeardataQueryResult.pop(0),YeardataQueryResult,ColumnNameofHeaderinQuery)
    MainData=TableDataMonth+TableDataYear
    TotalColumn=GesamtSpalteData(year)
    Data=[MainData[i]+TotalColumn[i] for i in range(13)]
    root=tkinter.Tk()
    root.state("zoomed")
    tabelle=tkinter.Text(root, font=("Courier New", 10))
    headers=[textwrap.fill(i,width=MAX_HEADER_WIDTH) for i in headers]
    tabelle.insert(tkinter.END,tabulate(Data, headers=[""]+headers+["Gesamt"],tablefmt="grid"))
    tabelle.pack(expand=True, fill="both")
    root.bind("<Return>",lambda e: root.destroy())
    def move_to_left_or_right(Right:bool):
        nonlocal Do_something_afterwards
        nonlocal index
        step=1 if Right else -1
        if index+step>=0 and index+step+MAX_NUMBER_OF_COLUMNS_ON_SCREEN<=len(ColumnOrdnung):
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
        Zahlungsübersicht_neu(ColumnOrdnung,MonthlydataQuery,YeardataQuery,ColumnNameofHeaderinQuery,year,index)

def ZahlungsübersichtNachKategorie():
    ColumnOrdnung=most_relevant_categories()
    def Querybydimension(dimension: Literal["Monat","Jahr"])->str:
        return f"""
            SELECT * FROM Zahlungsübersicht{dimension}
            WHERE Jahr=?
            """
    Zahlungsübersicht_neu(
        ColumnOrdnung=ColumnOrdnung,
        MonthlydataQuery=Querybydimension("Monat"),
        YeardataQuery=Querybydimension("Jahr"),
        ColumnNameofHeaderinQuery="Kategorie"
    )

def Detailansicht():
    ÜbersichtnachLadenetc()

def most_relevant_chains(year):
    Query=f"""
            SELECT Gruppe FROM ZahlungsübersichtJahrnachGruppe
            WHERE Jahr=?
            ORDER BY Total
            """
    Result=make_simple_query(Query,(year,))
    return [i[0] for i in Result]

def ÜbersichtnachLadenetc():
    def Querybydimension(dimension: Literal["Monat","Jahr"])->str:
        return f"""
            SELECT * FROM Zahlungsübersicht{dimension}nachGruppe
            WHERE Jahr=?
            """
    Zahlungsübersicht_neu(
        ColumnOrdnung=most_relevant_chains("2025"),
        MonthlydataQuery=Querybydimension("Monat"),
        YeardataQuery=Querybydimension("Jahr"),
        ColumnNameofHeaderinQuery="Gruppe"
    )