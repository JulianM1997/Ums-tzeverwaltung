import os
from dotenv import load_dotenv
import hashlib
import sqlite3
import csv


load_dotenv()
ORDNER=os.getenv("UmsatzOrdner")
assert ORDNER is not None
DBName=os.getenv("DBName")
assert DBName is not None
DBNAME=DBName
ColumnnamesinDBbycolumnnameinCSV={"Buchung": "Buchung",
                                  "Wertstellungsdatum": "Wertstellungsdatum",
                                  "Auftraggeber/Empfänger": "AuftraggeberEmpfaenger",
                                  "Buchungstext": "Buchungstext",
                                  "Verwendungszweck": "Verwendungszweck",
                                  "Betrag": "Betrag",
                                  "Währung": "Währung",
                                  "Notiz": "Notiz"}
Columnsrelevantforhash=["Buchung", "Wertstellungsdatum", "AuftraggeberEmpfaenger", "Buchungstext", "Verwendungszweck", "Betrag", "Währung"]

def initialize() -> None:
    with sqlite3.connect(DBNAME) as connection:
        with open("ddl.sql","r", encoding="UTF-8") as file:
            script=file.read()
        connection.executescript(script)

def is_valid_header(list: list[str]) -> bool:
    return all([i in ColumnnamesinDBbycolumnnameinCSV.keys() for i in list])


def bereinigeCSVmatrixundheader(matrix: list[list[str]])-> tuple[list[list[str]],list[str]]:
    while matrix[-1]==[""]:
        matrix.pop()
    for i in range(len(matrix)):
        if matrix[i]!=[] and matrix[i][0]=="Buchung":
            assert is_valid_header(matrix[i])
            return matrix[i+1:],[ColumnnamesinDBbycolumnnameinCSV[j] for j in matrix[i]]
    raise ValueError("csv is not of expected syntax")
        
def Entriesnotyetindb(matrix: list[list[str]],headers)-> tuple[list[list[str]],list[str]]:
    return [[createhashofrow(row,headers)]+row for row in matrix if not entryindb(row,headers)], ["hashofentry"]+headers

def entryindb(row: list[str], headers: list[str]) -> bool:
    sql=f"SELECT count(*) FROM Umsaetze WHERE hashofentry=? AND Buchung=?"
    return connection.execute(sql,(createhashofrow(row,headers),row[0])).fetchone()[0]!=0


def createhashofrow(row: list[str],headers: list[str])->str:
    row_in_correct_order_for_consistent_hash=[
        row[headers.index(header)] if header in headers else "" 
        for header in Columnsrelevantforhash
        ]
    return hashlib.md5(",".join(row_in_correct_order_for_consistent_hash).encode()).hexdigest()

def is_list_of_actual_columns(list):
    SQL=f"""
        PRAGMA table_info(Umsaetze)
        """
    table_info=connection.execute(SQL).fetchall()
    actual_columns=[i[1] for i in table_info]
    return all([i in actual_columns for i in list])

def insertsql(matrix: list[list[str]], headers: list[str]) -> None:
    assert is_list_of_actual_columns(headers) #make extra sure no SQL Injection may happen
    assert len(matrix)==0 or len(matrix[0])==len(headers)
    SQL=f"""
        INSERT INTO Umsaetze ({", ".join(headers)})
        VALUES ({",".join(("?" for i in range(len(headers))))})
        """
    connection.executemany(SQL,matrix)
    connection.commit()

def is_file_scanned(filename: str)-> bool:
    Query="""
    SELECT EXISTS(
        SELECT 1 
        FROM ScannedCSVs
        WHERE Dateiname=?
    );
    """
    Output=connection.execute(Query,(filename,)).fetchone()[0]
    print(Output)
    return bool(Output)
    
def tell_db_that_file_is_scanned(filename: str)->None:
    Query="""
    INSERT INTO ScannedCSVs
    VALUES (?)
    """
    connection.execute(Query,(filename,))

def reformatnumbers(matrix: list[list[str]],headers: list[str])-> list[list[str]]:
    return [[entry if headers[i]!="Betrag" else entry.replace('.', '').replace(',', '.') for i,entry in enumerate(row)] for row in matrix]

def scancsv(Ordner, csvpath):
    with open(Ordner+"/"+csvpath,"r",encoding="cp1252", newline="") as file:
        csvmatrix=list(csv.reader(file,delimiter=";"))
    csvmatrix,headers=bereinigeCSVmatrixundheader(csvmatrix)
    csvmatrix=reformatnumbers(csvmatrix,headers)
    csvmatrix,headers=Entriesnotyetindb(csvmatrix, headers)
    insertsql(csvmatrix, headers)
    tell_db_that_file_is_scanned(csvpath)

if not os.path.exists(DBNAME):
    initialize()
with sqlite3.connect(DBNAME) as connection:
    for csvpath in os.listdir(ORDNER):
        if csvpath[-4:]==".csv" and not is_file_scanned(csvpath):
            scancsv(ORDNER,csvpath)
            
            

        

        