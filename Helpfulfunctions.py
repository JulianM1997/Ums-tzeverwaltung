import sqlite3
from dotenv import load_dotenv
import os
import tkinter
from typing import Literal
import textwrap
from tabulate import tabulate

# Helpful (and needed) constants
load_dotenv()
dbname=os.getenv("DBNAME")
assert dbname is not None
DBNAME=dbname
MONATE=[ "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November","Dezember"]
Categories: list[str]
MAX_NUMBER_IN_MULTIPLE_CHOICE_MENU=10
MAX_HEADER_WIDTH=20
MAX_NUMBER_OF_COLUMNS_ON_SCREEN=5




# Queries
def make_simple_query(Query,Parameters:tuple=())-> list[tuple]:
    with sqlite3.connect(DBNAME) as connection:
        return connection.execute(Query,Parameters).fetchall()
    
def make_simple_read_query_and_get_headers_as_first_line(Query,Parameters:tuple=())-> list[tuple]:
    with sqlite3.connect(DBNAME) as connection:
        cursor=connection.execute(Query,Parameters)
        description=cursor.description
        headers=tuple(i[0] for i in description)
        result=cursor.fetchall()
        result.insert(0,headers)
        return result

# Read-Queries
# Write-Queries   
def createcategory(name: str) -> None:
    Query="""INSERT INTO Ausgabenkategorie VALUES (?)"""
    make_simple_query(Query,(name,))



#tkinter

def yesnowindow(Text: str, root=None, title:str|None=None,Textheight=5)->bool:
    Window=tkinter.Tk() if root==None else tkinter.Toplevel(root)
    title=title if title is not None else ""
    Window.title(title)
    Confirmation=False
    Textfeld=tkinter.Text(Window,height=Textheight)
    Textfeld.tag_configure("center",justify="center")
    Textfeld.insert(tkinter.END,Text,"center")
    Textfeld.pack()
    def buttonclick(confirm: bool):
        nonlocal Confirmation
        print(f"{confirm} received")
        Confirmation=confirm
        Window.destroy()
    for i in [True,False]:
        Button=tkinter.Button(Window,text="Ja" if i else "Nein", command=lambda k=i: buttonclick(k),width=50,height=2)
        Button.pack(side="left" if i else "right")
        Window.bind(f"<{"j" if i else "n"}>",lambda e,k=i:buttonclick(k))
    Window.focus_force()
    Window.mainloop()
    return Confirmation

def alldonewindow():
    root=tkinter.Tk()
    Text=tkinter.Text(root,font=("Arial",30))
    Text.insert(tkinter.END,"All Done!")
    Text.pack()
    root.bind("<Return>",lambda e: root.destroy())
    root.focus_force()
    root.mainloop()

def multiplechoicemenu_small(Text:str, ListOfOptions: list[str], root=None) -> str:
    Window=tkinter.Tk() if root==None else tkinter.Toplevel(root)
    Window.title(Text)
    Selection:str|None=None
    Buttons:dict[str,tkinter.Button]={}
    def buttonclick(selection: str):
        nonlocal Selection
        Selection=selection
        Window.destroy()
    for i in ListOfOptions:
        Buttons[i]=tkinter.Button(
            Window,
            text=f"{i} {str(i)[0]}" if i not in ["...",".."] else i, 
            command=lambda k=i: buttonclick(k),
            width=100,
            height=2
            )
        Buttons[i].pack()
    SelectionIfReturnIsPressed:str|None=None
    def changefocus(Option: str):
        nonlocal SelectionIfReturnIsPressed
        SelectionIfReturnIsPressed=Option
        assert SelectionIfReturnIsPressed in ListOfOptions
        Buttons[SelectionIfReturnIsPressed].focus_set()
    def keystroke(event: tkinter.Event):
        if event.char.isalpha():
            #Set to next entry beginning with the letter
            if event.char in (i[0].lower() for i in ListOfOptions):
                aktueller_index=ListOfOptions.index(SelectionIfReturnIsPressed) if SelectionIfReturnIsPressed is not None else -1
                nextindex=nextIndexStartingWith(aktueller_index,ListOfOptions,event.char)
                changefocus(ListOfOptions[nextindex])
        elif event.char=="\r":
            if SelectionIfReturnIsPressed is None:
                return
            buttonclick(SelectionIfReturnIsPressed)
        elif event.keysym=="Down":
            if ".." in ListOfOptions:
                changefocus("..")
        elif event.keysym=="Up":
            if "..." in ListOfOptions:
                changefocus("...")
                
    Window.bind("<KeyPress>",keystroke)
    Window.focus_force()
    Window.mainloop()
    if Selection is None:
        raise ValueError("No Input received")
    return Selection

def multiplechoicemenu(Text:str, ListOfOptions: list[str], root=None) -> str:
    if len(ListOfOptions)<=MAX_NUMBER_IN_MULTIPLE_CHOICE_MENU:
        return multiplechoicemenu_small(Text,ListOfOptions,root)
    PartitionOfOptions=[[]]
    for i in ListOfOptions:
        if len(PartitionOfOptions[-1])<MAX_NUMBER_IN_MULTIPLE_CHOICE_MENU-1:
            PartitionOfOptions[-1].append(i)
        else:
            PartitionOfOptions[-1].append("...")
            PartitionOfOptions.append(["..",i])
    if len(PartitionOfOptions[-1])==2:
        Overhang=PartitionOfOptions.pop()[1]
        PartitionOfOptions[-1][-1]=Overhang
    i=0
    while True:
        Option=multiplechoicemenu_small(Text,PartitionOfOptions[i],root)
        if Option=="...":
            i+=1
        elif Option=="..":
            i-=1
        else:
            return Option

def displayTable(headers:tuple[str],tabledata:list[tuple],index=0):
    print(headers)
    print(tabledata)
    includedHeaders=headers[index:index+MAX_NUMBER_OF_COLUMNS_ON_SCREEN]
    includedData=[i[index:index+MAX_NUMBER_OF_COLUMNS_ON_SCREEN] for i in tabledata]
    root=tkinter.Tk()
    root.state("zoomed")
    tabelle=tkinter.Text(root, font=("Courier New", 10))
    print(includedHeaders)
    FormattedHeaders=[textwrap.fill(str(i),width=MAX_HEADER_WIDTH) for i in includedHeaders]
    tabelle.insert(
        tkinter.END,
        tabulate(includedData, headers=FormattedHeaders,tablefmt="grid"))
    tabelle.pack(expand=True, fill="both")
    root.bind("<Return>",lambda e: root.destroy())
    def move_to_left_or_right(Right:bool):
        nonlocal Do_something_afterwards
        nonlocal index
        step=1 if Right else -1
        if index+step>=0 and index+step+MAX_NUMBER_OF_COLUMNS_ON_SCREEN<=len(headers):
            Do_something_afterwards=True
            index=index+step
            root.destroy()
    root.bind("<Left>",lambda e: move_to_left_or_right(False))
    root.bind("<Right>",lambda e: move_to_left_or_right(True))
    Do_something_afterwards=False
    root.mainloop()
    if Do_something_afterwards:
        displayTable(headers,tabledata,index)

# Sonstige

def getcategories(sorted_by_number_of_appearances=False, in_what: Literal["KategorieZuordnung","mehrdeutige Umsaetze"]="KategorieZuordnung")->list[str]:
    if not sorted_by_number_of_appearances:
        Query="SELECT KategorieNAME FROM Ausgabenkategorie"
    elif in_what=="KategorieZuordnung":
        Query="SELECT KategorieNAME FROM Kategorien_ordered_by_vendors"
    elif in_what=="mehrdeutige Umsaetze":
        Query="SELECT KategorieNAME FROM Kategorien_ordered_by_payments_of_ambiguous_vendors"
    else:
        raise NotImplementedError
    Result=make_simple_query(Query)
    return [i[0] for i in Result]

def most_relevant_categories()->list[str]:
    Query="""
    SELECT DISTINCT Kategorie
    FROM ZahlungsübersichtJahr
    ORDER BY ABS(Total) DESC
    """
    Result=make_simple_query(Query)
    return [i[0] for i in Result]

def delete_category(categoryname:str):
    Query1="DELETE FROM KategorieZuordnung WHERE KategorieNAME=?"
    Query2="""
    UPDATE TABLE Umsaetze 
    SET KategorieifAuftraggeberEmpfaengerAmbiguous=NULL 
    WHERE KategorieifAuftraggeberEmpfaengerAmbiguous=?
    """
    make_simple_query(Query1,(categoryname,))
    make_simple_query(Query2,(categoryname,))

def rename_category(old,new):
    Query1="""
    UPDATE KategorieZuordnung 
    SET KategorieNAME=?
    WHERE KategorieNAME=?
    """
    Query2="""
    UPDATE Umsaetze 
    SET KategorieifAuftraggeberEmpfaengerAmbiguous=? 
    WHERE KategorieifAuftraggeberEmpfaengerAmbiguous=?
    """
    make_simple_query(Query1,(new,old))
    make_simple_query(Query2,(new,old))

TABLES=[i[0] for i in make_simple_query("SELECT name FROM sqlite_master")]
def getcolumns(tablename):
    assert tablename in TABLES
    Query=f"PRAGMA table_info({tablename})"
    return [i[1] for i in make_simple_query(Query)]



# def TabelleCursor(Curs):
#     headers=[i[0] for i in Curs.description]
#     data=Curs.fetchall()
#     return tabulate(data,headers)


#Other
def nextIndexStartingWith(currentIndex:int,List:list[str],Startingletter):
    return min(
        (index for index,value in enumerate(List) if value[0].lower()==Startingletter),
        key=lambda index: (index-currentIndex-1)%len(List)
        )
        
def reformatDate(dd_mm_yyyy:str)->str:
    mm=dd_mm_yyyy[3:5]
    yyyy=dd_mm_yyyy[6:]
    return f"{MONATE[int(mm)]} {yyyy}"