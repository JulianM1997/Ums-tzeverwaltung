from Helpfulfunctions import *
from assign_category import *
from payment_overview import *
from periodic_expenses import *



def getlikelykeywords() -> dict[tuple[str,str],int]:#The goal is to find likely keywords (such as REWE) in the name of an entity to identify a category
    Query="SELECT AuftraggeberEmpfaenger, KategorieNAME FROM KategorieZuordnung"
    with sqlite3.connect(DBNAME) as connection:
        cursor=connection.execute(Query)
        response=cursor.fetchall()
    numberofwordcategorycombination:dict[tuple[str,str],int]={}
    for line in response:
        category=line[1]
        entity=line[0]
        for word in entity.split():
            numberofwordcategorycombination[word,category]=numberofwordcategorycombination.get((word,category),0)+1
    return numberofwordcategorycombination
        
def assign_likely_groups():
    Likely_Gruppenzuordnung=make_simple_query("SELECT GruppenNAME, KontoNAME FROM LikelyKontoGruppenMatch")
    for Gruppe,Konto in Likely_Gruppenzuordnung:
        if yesnowindow(f"Soll das Konto {Konto} der Gruppe {Gruppe} zugeordnet werden?"):
            make_simple_query("INSERT INTO KontogruppenZuordnung(GruppenNAME ,KontoNAME) VALUES (?,?)",(Gruppe,Konto))
        make_simple_query("DELETE FROM LikelyKontoGruppenMatch WHERE KontoNAME=? AND GruppenNAME=?",(Konto,Gruppe))

def assign_most_likely_category():
    knowncombinations=make_simple_query("SELECT Word,KategorieNAME FROM WordLikelyCategory")
    likelykeywords=getlikelykeywords()
    if likelykeywords=={}:
        return
    totalappearancesofword={}
    for word,_ in likelykeywords:
        totalappearancesofword[word]=totalappearancesofword.get(word,0)+likelykeywords[word,_]
    def pairinteresting(pair)->bool:
        if pair in knowncombinations:
            return False
        if (pair[0],"Mehrdeutig") in knowncombinations:
            return False
        if pair[1]=="Mehrdeutig":
            return False
        if likelykeywords[pair]<2:
            return False
        return likelykeywords[pair]>=totalappearancesofword[pair[0]]*2/3
    while  not pairinteresting(pair:=max(likelykeywords)):
        likelykeywords.pop(pair)
        if likelykeywords=={}:
            return
    pair=max(likelykeywords)
    Fragetext=f"""
    Soll das Wort '{pair[0]}' der Kategorie '{pair[1]}' zugeordnet werden? 
    Vorkommen: 
    {"\n".join(Konten_mit_Word_im_Namen(pair[0]))}"""
    if yesnowindow(Fragetext,Textheight=min(2*Fragetext.count("\n"),30)):
        isChain=yesnowindow("Handelt es sich um eine Ladenkette oder ähnliches?")
        make_simple_query("INSERT INTO WordLikelyCategory VALUES (?,?,?)",(pair[0],pair[1],isChain))
        if isChain:
            Query="""
            INSERT INTO LikelyKontoGruppenMatch (GruppenNAME,KontoNAME)
            SELECT DISTINCT ?,AuftraggeberEmpfaenger
            FROM Umsaetze
            WHERE LOWER(AuftraggeberEmpfaenger) LIKE '%' || LOWER(?) || '%';
            """
            make_simple_query(Query,(pair[0],pair[0]))

    elif yesnowindow(f"Soll das Wort '{pair[0]}' als mehrdeutig gekennzeichnet werden?"):
        make_simple_query("INSERT INTO WordLikelyCategory VALUES (?,?,?)",(pair[0],"Mehrdeutig",False))

def Konten_mit_Word_im_Namen(Word)->list[str]:
    Query="""
    SELECT DISTINCT AuftraggeberEmpfaenger 
    FROM Umsaetze 
    WHERE AuftraggeberEmpfaenger LIKE ?
    """
    Vorkommen=make_simple_query(Query,(f"%{Word}%",))
    return [i[0] for i in Vorkommen]
    

def openingmenu():
    Job:str|None=None
    root=tkinter.Tk()
    root.title("Choose what you want to do")
    associatedfunction={
        "Categorize Zahlungspartner": assigncategories,
        "Zahlungsübersicht": ZahlungsübersichtNachKategorie,
        "Mehrdeutige Zahlungen kategorisieren": categorize_ambiguous_payments,
        "Detailansicht": Detailansicht,
        "Regelmäßige Ausgaben": periodic_expenses
    }
    modes=associatedfunction.keys()
    def f(mode):
        nonlocal Job
        Job=mode
        root.destroy()
    for i,mode in enumerate(modes):
        button=tkinter.Button(root,text=mode+f" [{i}]",command=lambda m=mode: f(m), width=30,height=5)
        button.pack()
        if i<10:
            root.bind(f"<Key-{i}>",lambda e,m=mode: f(m))
    root.mainloop()
    assert Job is not None
    associatedfunction[Job]()


assign_most_likely_category()
assign_likely_groups()
openingmenu()