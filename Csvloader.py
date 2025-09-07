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

def initialize() -> None:
    with sqlite3.connect(DBNAME) as connection:
        with open("ddl.sql","r", encoding="UTF-8") as file:
            script=file.read()
        connection.executescript(script)


def bereinigeCSVmatrix(matrix: list[list[str]])-> list[list[str]]:
    while matrix[-1]==[""]:
        matrix.pop()
    for i in range(len(matrix)):
        if matrix[i]!=[] and matrix[i][0]=="Buchung":
            assert matrix[i]=="Buchung;Wertstellungsdatum;Auftraggeber/Empfänger;Buchungstext;Verwendungszweck;Betrag;Währung".split(";")
            return matrix[i+1:]
    raise ValueError("csv is not of expected syntax")
        
def Entriesnotyetindb(matrix: list[list[str]])-> list[list[str]]:
    return [[createhashofrow(row)]+row for row in matrix if not entryindb(row)]

def entryindb(row: list[str]) -> bool:
    sql=f"SELECT count(*) FROM Umsaetze WHERE hashofentry=? AND Buchung=?"
    return connection.execute(sql,(createhashofrow(row),row[0])).fetchone()[0]!=0


def createhashofrow(row: list[str])->str:
    return hashlib.md5(",".join(row).encode()).hexdigest()

def insertsql(matrix: list[list[str]]) -> None:
    SQL="""INSERT INTO Umsaetze (hashofentry,
    Buchung,
    Wertstellungsdatum,
    AuftraggeberEmpfaenger,
    Buchungstext,
    Verwendungszweck,
    Betrag,
    Währung)
VALUES (?,?,?,?,?,?,?,?)"""
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

def reformatnumbers(matrix: list[list[str]])-> list[list[str]]:
    return [[entry if i!=5 else entry.replace('.', '').replace(',', '.') for i,entry in enumerate(row)] for row in matrix]

def scancsv(Ordner, csvpath):
    with open(Ordner+"/"+csvpath,"r",encoding="cp1252", newline="") as file:
        csvmatrix=list(csv.reader(file,delimiter=";"))
    csvmatrix=bereinigeCSVmatrix(csvmatrix)
    csvmatrix=reformatnumbers(csvmatrix)
    csvmatrix=Entriesnotyetindb(csvmatrix)
    insertsql(csvmatrix)
    tell_db_that_file_is_scanned(csvpath)

if not os.path.exists(DBNAME):
    initialize()
with sqlite3.connect(DBNAME) as connection:
    for csvpath in os.listdir(ORDNER):
        if csvpath[-4:]==".csv" and not is_file_scanned(csvpath):
            scancsv(ORDNER,csvpath)
            
            

        

        