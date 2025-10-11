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
    KategorieNAME VARCHAR(16)
);

CREATE VIEW UmsaetzemitKategorien AS
SELECT  U.*,
        CASE
            WHEN U.KategorieifAuftraggeberEmpfaengerAmbiguous IS NULL THEN K.KategorieNAME
            ELSE U.KategorieifAuftraggeberEmpfaengerAmbiguous
        END AS Kategorie
FROM Umsaetze U
LEFT JOIN KategorieZuordnung K 
ON U.AuftraggeberEmpfaenger=K.AuftraggeberEmpfaenger;

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

INSERT INTO Ausgabenkategorie(KategorieNAME) 
VALUES 
('Supermarkt'),
('Gehalt'),
('Miete'),
('Versicherung'),
('Kleidung'),
('Sonstige'),
('Mehrdeutig');

