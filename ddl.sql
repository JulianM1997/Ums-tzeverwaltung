CREATE TABLE Umsaetze (
    hashofentry VARCHAR(32) PRIMARY KEY,
    Buchung DATE,
    Wertstellungsdatum DATE,
    AuftraggeberEmpfaenger VARCHAR(256),
    Buchungstext VARCHAR(256),
    Verwendungszweck VARCHAR(256),
    Betrag NUMERIC(8,2),
    Währung VARCHAR(8),
    KategorieifAuftraggeberEmpfaengerAmbiguous VARCHAR(32),
    Notiz VARCHAR(256)
    );

ALTER TABLE Umsaetze
ADD COLUMN 
CorrectlyformattedDate DATE GENERATED ALWAYS
AS
(substr(Buchung,7,4)||'-'||substr(Buchung,4,2)||'-'||substr(Buchung,1,2))
VIRTUAL;


CREATE TABLE Ausgabenkategorie (
    KategorieNAME VARCHAR PRIMARY KEY
);

CREATE TABLE KategorieZuordnung (
    AuftraggeberEmpfaenger VARCHAR(256) PRIMARY KEY,
    KategorieNAME VARCHAR(16),
    FOREIGN KEY(KategorieNAME) REFERENCES Ausgabenkategorie
);

CREATE TRIGGER Auto_Update_Ausgabenkategorie
BEFORE INSERT ON KategorieZuordnung
WHEN (SELECT count(*) FROM Ausgabenkategorie WHERE KategorieNAME=NEW.KategorieNAME)=0
BEGIN
    INSERT INTO Ausgabenkategorie (KategorieNAME) VALUES (NEW.KategorieNAME);
END;

CREATE TABLE ScannedCSVs (
    Dateiname VARCHAR(256)
);

CREATE TABLE WordLikelyCategory(
    Word VARCHAR(16),
    KategorieNAME VARCHAR(16),
    isKettenName BOOLEAN
);

CREATE TABLE KontogruppenZuordnung(
    GruppenNAME VARCHAR(16),
    KontoNAME VARCHAR(256)
);

CREATE TABLE LikelyKontoGruppenMatch(
    GruppenNAME VARCHAR(16),
    KontoNAME VARCHAR(256)
)

CREATE TRIGGER addLikelyKontoGroupMatch
BEFORE INSERT ON Umsaetze
WHEN EXISTS(
    SELECT 1 FROM WordLikelyCategory 
    WHERE LOWER(NEW.AuftraggeberEmpfaenger) LIKE '%'||LOWER(WORD)||'%' AND isKettenName
    )
AND NOT EXISTS(
    SELECT 1 FROM Umsaetze 
    WHERE NEW.AuftraggeberEmpfaenger=AuftraggeberEmpfaenger
    )
BEGIN
    INSERT INTO LikelyKontoGruppenMatch 
    VALUES (
        (
            SELECT WORD FROM WordLikelyCategory 
            WHERE LOWER(NEW.AuftraggeberEmpfaenger) LIKE '%'||LOWER(WORD)||'%' AND isKettenName 
            LIMIT 1),
            NEW.AuftraggeberEmpfaenger);
END;

CREATE VIEW UmsaetzemitKategorien AS
SELECT  U.*,
        CASE
            WHEN U.KategorieifAuftraggeberEmpfaengerAmbiguous IS NULL THEN K.KategorieNAME
            ELSE U.KategorieifAuftraggeberEmpfaengerAmbiguous
        END AS Kategorie
FROM Umsaetze U
LEFT JOIN KategorieZuordnung K 
ON U.AuftraggeberEmpfaenger=K.AuftraggeberEmpfaenger;

CREATE VIEW UmsaetzemitGruppenzuordnung AS
SELECT  U.*,
        CASE
            WHEN K.GruppenNAME IS NULL THEN U.AuftraggeberEmpfaenger
            ELSE K.GruppenNAME
        END AS Gruppe
FROM Umsaetze U
LEFT JOIN KontogruppenZuordnung K
ON U.AuftraggeberEmpfaenger=K.KontoNAME;

CREATE VIEW DetailansichtUmsaetze AS
SELECT A.*, B.Gruppe AS Gruppe
FROM UmsaetzemitKategorien A LEFT JOIN UmsaetzemitGruppenzuordnung B
ON A.hashofentry=B.hashofentry;

CREATE VIEW ZahlungsübersichtMonat AS 
SELECT  Kategorie, 
    CASE 
        WHEN Betrag>0 THEN 1
        ELSE 0
    END AS Einnahme,
    sum(Betrag) AS Total,
    substr(Buchung,7,4) AS Jahr,
    substr(Buchung,4,2) AS Monat
FROM UmsaetzemitKategorien
GROUP BY Kategorie, Einnahme, Monat, Jahr;

CREATE VIEW ZahlungsübersichtJahr AS 
SELECT  Kategorie, 
    CASE 
        WHEN Betrag>0 THEN 1
        ELSE 0
    END AS Einnahme,
    sum(Betrag) AS Total,
    substr(Buchung,7,4) AS Jahr
FROM UmsaetzemitKategorien
GROUP BY Kategorie, Einnahme, Jahr;

CREATE VIEW ZahlungsübersichtMonatnachGruppe AS 
SELECT  Gruppe, 
    CASE 
        WHEN Betrag>0 THEN 1
        ELSE 0
    END AS Einnahme,
    sum(Betrag) AS Total,
    substr(Buchung,7,4) AS Jahr,
    substr(Buchung,4,2) AS Monat
FROM UmsaetzemitGruppenzuordnung
GROUP BY Gruppe, Einnahme, Monat, Jahr;

CREATE VIEW ZahlungsübersichtJahrnachGruppe AS 
SELECT  Gruppe, 
    CASE 
        WHEN Betrag>0 THEN 1
        ELSE 0
    END AS Einnahme,
    sum(Betrag) AS Total,
    substr(Buchung,7,4) AS Jahr
FROM UmsaetzemitGruppenzuordnung
GROUP BY Gruppe, Einnahme, Jahr;

CREATE VIEW InOutByMonth AS 
SELECT   
    CASE 
        WHEN Betrag>0 THEN 1
        ELSE 0
    END AS Einnahme,
    sum(Betrag) AS Total,
    substr(Buchung,7,4) AS Jahr,
    substr(Buchung,4,2) AS Monat
FROM UmsaetzemitKategorien
GROUP BY Einnahme, Jahr, Monat;

CREATE VIEW InOutByYear AS 
SELECT   
    CASE 
        WHEN Betrag>0 THEN 1
        ELSE 0
    END AS Einnahme,
    sum(Betrag) AS Total,
    substr(Buchung,7,4) AS Jahr
FROM UmsaetzemitKategorien
GROUP BY Einnahme, Jahr;

CREATE VIEW Kategorien_ordered_by_vendors AS
SELECT A.KategorieNAME AS KategorieNAME 
FROM Ausgabenkategorie A
LEFT JOIN KategorieZuordnung K
ON A.KategorieNAME=K.KategorieNAME
GROUP BY A.KategorieNAME
ORDER BY count(K.AuftraggeberEmpfaenger) DESC;

CREATE VIEW Kategorien_ordered_by_payments_of_ambiguous_vendors AS
SELECT A.KategorieNAME AS KategorieNAME 
FROM Ausgabenkategorie A
LEFT JOIN Umsaetze U
ON A.KategorieNAME=U.KategorieifAuftraggeberEmpfaengerAmbiguous
GROUP BY A.KategorieNAME
ORDER BY count(U.hashofentry) DESC;

CREATE VIEW Konten AS
SELECT DISTINCT AuftraggeberEmpfaenger AS KontoNAME
FROM Umsaetze;

CREATE VIEW WordLikelyCategory_mit_Likelyhood AS 
SELECT 
    Word,
    KategorieNAME,
    CASE 
        WHEN Totalnumberofappearances=0 THEN 0
        ELSE Appearancesofcorrectcategory*1.0/Totalnumberofappearances 
    END AS Likelyhood
FROM (SELECT 
        Word,
        KategorieNAME,
        (SELECT count(*) FROM Konten WHERE LOWER(KontoNAME) LIKE '%' || LOWER(WORD) || '%') AS Totalnumberofappearances,
        (SELECT count(*) FROM KategorieZuordnung WHERE LOWER(AuftraggeberEmpfaenger) LIKE '%' || LOWER(WORD) || '%' AND KategorieNAME=WordLikelyCategory.KategorieNAME) AS Appearancesofcorrectcategory
    FROM WordLikelyCategory
    WHERE KategorieNAME!='Mehrdeutig');
    
INSERT INTO Ausgabenkategorie(KategorieNAME) 
VALUES 
('Supermarkt'),
('Gehalt'),
('Miete'),
('Versicherung'),
('Kleidung'),
('Sonstige'),
('Mehrdeutig');

