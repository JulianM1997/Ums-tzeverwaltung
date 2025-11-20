import sqlite3
from dotenv import load_dotenv
import os
import tkinter
from typing import Literal

# Helpful (and needed) constants
load_dotenv()
dbname=os.getenv("DBNAME")
assert dbname is not None
DBNAME=dbname
MONATE=[ "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November","Dezember"]
Categories: list[str]




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



# def TabelleCursor(Curs):
#     headers=[i[0] for i in Curs.description]
#     data=Curs.fetchall()
#     return tabulate(data,headers)