from typing import Literal

from Helpfulfunctions import yesnowindow,sqlite3,tkinter,DBNAME,make_simple_query,make_simple_read_query_and_get_headers_as_first_line, createcategory, getcategories, alldonewindow


def confirmcategory(name: str, root) -> bool:
    return yesnowindow(f"Soll das Konto der Kategorie '{name}' zugeordnet werden?",root,"Kategorie existiert bereits")



# Queries
#  - Reads
def getuncategorizedline()->tuple[list[tuple],tuple]:
    Query="""
    SELECT U.* 
    FROM Umsaetze U LEFT JOIN KategorieZuordnung K
    ON U.AuftraggeberEmpfaenger = K.AuftraggeberEmpfaenger
    WHERE K.AuftraggeberEmpfaenger is NULL
    LIMIT 1
    """
    with sqlite3.connect(DBNAME) as connection:
            cursor=connection.execute(Query)
            uncategorizedline=cursor.fetchall()
            headers=tuple(i[0] for i in cursor.description)
    return uncategorizedline,headers

def get_uncategorized_lines_of_ambiguous_categorized_entities()-> list[tuple]:
    Query="""
    SELECT U.* 
    FROM Umsaetze U LEFT JOIN KategorieZuordnung K
    ON U.AuftraggeberEmpfaenger = K.AuftraggeberEmpfaenger
    WHERE K.KategorieNAME='Mehrdeutig' AND U.KategorieifAuftraggeberEmpfaengerAmbiguous is NULL
    """
    return make_simple_read_query_and_get_headers_as_first_line(Query)

def categories_sorted_by_likelyhood(words:list[str])->list[str]:
    Query=f"""
    SELECT KategorieNAME
    FROM WordLikelyCategory
    WHERE Word in ({",".join("?" for w in words)})
    GROUP BY KategorieNAME
    ORDER BY count(Word) DESC
    """
    Response=make_simple_query(Query,tuple(words))
    Mostlikelycategories=[i[0] for i in Response]
    return Mostlikelycategories+[i for i in Categories if i not in Mostlikelycategories]


#  - Writes
def connectentitytocategory(entity: str,category: str) -> None:
    Query="""
    INSERT INTO KategorieZuordnung (AuftraggeberEmpfaenger, KategorieNAME)
    VALUES (?,?)
    """
    make_simple_query(Query,(entity,category))

def set_category_of_line(key,category):
    Query="""
    UPDATE Umsaetze
    SET KategorieifAuftraggeberEmpfaengerAmbiguous=?
    WHERE hashofentry=?
    """
    make_simple_query(Query,(category,key))




def open_menu(option_menu):
    x = option_menu.winfo_rootx()
    y = option_menu.winfo_rooty() + option_menu.winfo_height()
    option_menu["menu"].post(x, y)

def categorizationwindow(line:tuple[str],headers:tuple[str],insertcategory,title: str,sorted_categories: list[str])-> None:
    root = tkinter.Tk()
    root.title(title)
    Textfeld=tkinter.Text()
    Textfeld.insert(tkinter.END,"\n".join([f"{header}: {line[i]}" for i,header in enumerate(headers)]))
    Textfeld.pack()
    selected=tkinter.StringVar(root)
    selected.set(sorted_categories[0])
    dropdown=tkinter.OptionMenu(root, selected, *sorted_categories)
    dropdown.pack()
    entry=tkinter.Entry(root)
    entry.pack()
    def submit():
        category=selected.get()
        if category=="Sonstige":
            category=entry.get()
            if category=="":
                category="Sonstige"
            if not category in Categories:
                createcategory(category)
                Categories.append(category)
        insertcategory(category)
        root.destroy()
    def keystroke(event: tkinter.Event):
        if event.keysym == "Down":
            open_menu(dropdown)
        elif event.char.isalpha():
            print(event.char)
            #Set to next entry beginning with the letter
            if event.char in (i[0].lower() for i in sorted_categories):
                aktueller_index=sorted_categories.index(selected.get())
                nextindex=min(
                    (index for index,cat in enumerate(sorted_categories) if cat[0].lower()==event.char),
                    key=lambda index: (index-aktueller_index-1)%len(sorted_categories)
                    )
                selected.set(sorted_categories[nextindex])
        elif event.char=="\r":
            submit()
    button = tkinter.Button(root, text="Submit", command=submit)
    button.pack()
    root.bind("<KeyPress>",keystroke)
    root.focus_force()
    root.mainloop()

def categorizeline(line: tuple[str], headers: tuple[str],level: Literal["line","entity"]) -> None:
    if level=="entity":
        entity=line[headers.index("AuftraggeberEmpfaenger")]
        insertcategory=lambda x: connectentitytocategory(entity,x)
        title="Kategorie des Zahlungspartner"
        words=entity.split()
    else:
        key=line[headers.index("hashofentry")]
        insertcategory=lambda x: set_category_of_line(key,x)
        title="Kategorie der Zahlung"
        words=line[headers.index("Verwendungszweck")].split()
    categorizationwindow(line,headers,insertcategory,title,categories_sorted_by_likelyhood(words))
    
    



#Main functions            
def assigncategories():
    global Categories 
    Categories=getcategories(True,"KategorieZuordnung")
    while True:    
        uncategorizedline,headers=getuncategorizedline()
        if not uncategorizedline:
            break
        categorizeline(uncategorizedline[0],headers,"entity")
    alldonewindow()

def categorize_ambiguous_payments():
    global Categories
    Categories=getcategories(True,"mehrdeutige Umsaetze")
    lines=get_uncategorized_lines_of_ambiguous_categorized_entities()
    headers=lines.pop(0)
    for line in lines:
        categorizeline(line,headers,"line")
    alldonewindow()
