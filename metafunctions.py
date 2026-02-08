from Helpfulfunctions import *

def vendor_categorizations():
    Query="""
    SELECT KategorieNAME, AuftraggeberEmpfaenger 
    FROM KategorieZuordnung 
    ORDER BY KategorieNAME
    """
    Result=make_simple_query(Query)
    Todisplaytextlines=[]
    PreviousCategory:str|None=None
    for (i,j) in Result:
        assert type(i)==str
        assert type(j)==str
        if i!=PreviousCategory:
            Todisplaytextlines.append(i)
        PreviousCategory=i
        Todisplaytextlines.append("   "+j)
    DisplayedText="\n".join(Todisplaytextlines)
    DisplaySimpleText(DisplayedText)


def convert_existing_category_to_subcategory(category:str ,parent_category: str)->None:
    Query="""UPDATE Ausgabenkategorie SET ParentCategory=? WHERE KategorieNAME=?;"""
    make_simple_query(Query,(parent_category,category))

def list_all_vendors_of_category(category:str):
    Query="SELECT AuftraggeberEmpfaenger FROM KategorieZuordnung WHERE KategorieNAME=?;"
    return make_simple_query(Query,(category,))

def does_category_exist(name)->bool:
    Query="SELECT count(*) FROM Ausgabenkategorie WHERE KategorieNAME=?"
    result=make_simple_query(Query,(name,))
    return result[0][0]==1

def add_subcategory_to_DB(Name:str,parent_category:str):
    if does_category_exist(Name) and yesnowindow(f"Category already exists. Do you wish to overwrite the parent?"):
        Query="UPDATE Ausgabenkategorie SET ParentCategory=? WHERE KategorieNAME=?"
        make_simple_query(Query,(parent_category,Name))
        return
    Query="""
    INSERT INTO Ausgabenkategorie(KategorieNAME,ParentCategory)
    VALUES (?,?)
    """
    make_simple_query(Query,(Name,parent_category))

def recategorizeTableEntry(table,idcolumn,newcategory,parent_category):
    assert is_valid_tablename(table)
    assert is_valid_columnname(table,idcolumn)
    def list_all_entries_of_category(category:str):
        Query=f"SELECT {idcolumn} FROM {table} WHERE KategorieNAME=?;"
        return make_simple_query(Query,(category,))
    affected_entries=list_all_entries_of_category(parent_category)
    entries_to_recategorize=multiple_select_window(
        f"Welche dieser Einträge sollen der Kategorie {newcategory} zugeordnet werden?",
        affected_entries
        )
    Query2=f"""
    UPDATE {table} 
    SET KategorieNAME=? 
    WHERE {idcolumn} IN ({", ".join(["?" for i in entries_to_recategorize])});
    """
    make_simple_query(Query2,(newcategory,*[i[0] for i in entries_to_recategorize]))


def create_new_subcategory_old_version(Name:str,parent_category:str):
    add_subcategory_to_DB(Name,parent_category)
    affected_vendors=list_all_vendors_of_category(parent_category)
    vendors_to_recategorize=multiple_select_window(
        f"Welche dieser Verkäufer sollen der Kategorie {Name} zugeordnet werden?",
        affected_vendors
        )
    Query2=f"""
    UPDATE KategorieZuordnung 
    SET KategorieNAME=? 
    WHERE AuftraggeberEmpfaenger IN ({", ".join(["?" for i in vendors_to_recategorize])});
    """
    make_simple_query(Query2,(Name,*[i[0] for i in vendors_to_recategorize]))

def create_new_subcategory(Name:str,parent_category:str):
    add_subcategory_to_DB(Name,parent_category)
    tables_idcolumn_to_recategorize=[
        ("KategorieZuordnung","AuftraggeberEmpfaenger"),
        ("WordLikelyCategory","Word")
    ]
    for i in tables_idcolumn_to_recategorize:
        recategorizeTableEntry(*i,Name,parent_category)

def create_subcategory_window():
    parent=multiplechoicemenu("Welche Kategorie soll eine Unterkategorie bekommen?",getcategories())
    Name=TextinputWindow("Wie soll die Kategorie heißen?")
    create_new_subcategory(Name,parent)