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
