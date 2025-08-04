VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "CSVImporter"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
' Classe CSVImporter - Version robuste pour l'import CSV
' Fichier : CSVImporter.cls

Option Explicit

Private ws As Worksheet
Private startColumn As Long
Private startRow As Long
Private pCurrentRow As Long
Private columnMappings As Object ' Dictionary pour mapper les colonnes
Private expectedColumns As Collection ' Colonnes attendues dans l'ordre

' Constructeur
Public Sub Initialize(targetWorksheet As Worksheet, Optional startCol As Long = 4)
    Set ws = targetWorksheet
    startColumn = startCol
    pCurrentRow = 1
    
    ' Initialiser le mapping des colonnes
    Set columnMappings = CreateObject("Scripting.Dictionary")
    
    ' Définir l'ordre des colonnes attendues
    Set expectedColumns = New Collection
    InitializeExpectedColumns
End Sub

' Définir les colonnes attendues dans l'ordre souhaité
Private Sub InitializeExpectedColumns()
    expectedColumns.Add "Scan Title"
    expectedColumns.Add "Ticket"
    expectedColumns.Add "Comments"
    expectedColumns.Add "IP"
    expectedColumns.Add "DNS"
    expectedColumns.Add "NetBIOS"
    expectedColumns.Add "Tracking Method"
    expectedColumns.Add "OS"
    expectedColumns.Add "IP Status"
    expectedColumns.Add "QID"
    expectedColumns.Add "Title"
    expectedColumns.Add "Vuln Status"
    expectedColumns.Add "Type"
    expectedColumns.Add "Severity"
    expectedColumns.Add "Port"
    expectedColumns.Add "Protocol"
    expectedColumns.Add "FQDN"
    expectedColumns.Add "SSL"
    expectedColumns.Add "First Detected"
    expectedColumns.Add "Last Detected"
    expectedColumns.Add "Times Detected"
    expectedColumns.Add "Date Last Fixed"
    expectedColumns.Add "CVE ID"
    expectedColumns.Add "Vendor Reference"
    expectedColumns.Add "Bugtraq ID"
    expectedColumns.Add "Threat"
    expectedColumns.Add "Impact"
    expectedColumns.Add "Solution"
    expectedColumns.Add "Exploitability"
    expectedColumns.Add "Results"
    expectedColumns.Add "PCI Vuln"
    expectedColumns.Add "Ticket State"
    expectedColumns.Add "Instance"
    expectedColumns.Add "Category"
    expectedColumns.Add "QDS"
    expectedColumns.Add "ARS"
    expectedColumns.Add "ACS"
    expectedColumns.Add "TruRisk Score"
End Sub
' Analyser les en-têtes du fichier CSV et créer le mapping
Private Sub AnalyzeHeaders(headerRecord As Collection)
    Dim i As Long
    Dim headerName As String
    
    ' Vider le mapping précédent
    columnMappings.RemoveAll
    
    ' Créer le mapping colonne source -> position attendue
    For i = 1 To headerRecord.Count
        headerName = Trim(CStr(headerRecord(i)))
        
        ' Chercher si cette colonne existe dans nos colonnes attendues
        Dim j As Long
        For j = 1 To expectedColumns.Count
            If StrComp(headerName, expectedColumns(j), vbTextCompare) = 0 Then
                ' Mapper : position source -> position de destination
                columnMappings(i) = j
                Exit For
            End If
        Next j
    Next i
    
    ' Debug: afficher le mapping trouvé
    Debug.Print "=== Mapping des colonnes pour le fichier ==="
    For i = 1 To headerRecord.Count
        headerName = Trim(CStr(headerRecord(i)))
        If columnMappings.Exists(i) Then
            Debug.Print "Colonne " & i & " [" & headerName & "] -> Position " & columnMappings(i) & " [" & expectedColumns(columnMappings(i)) & "]"
        Else
            Debug.Print "Colonne " & i & " [" & headerName & "] -> NON MAPPÉE"
        End If
    Next i
End Sub

' Propriétés
Public Property Get currentRow() As Long
    currentRow = pCurrentRow
End Property

Public Property Let currentRow(value As Long)
    pCurrentRow = value
End Property

' Méthode principale pour importer un fichier CSV
Public Function ImportCSVFile(FilePath As String, Optional Delimiter As String = ",", Optional textQualifier As String = """") As Boolean
    On Error GoTo ErrorHandler
    
    Dim FileName As String
    Dim fileContent As String
    Dim csvLines As Variant
    Dim i As Long
    
    ' Extraire le nom du fichier sans le chemin
    FileName = Right(FilePath, Len(FilePath) - InStrRev(FilePath, "\"))
    
    ' Lire tout le contenu du fichier d'un coup
    fileContent = ReadFileContent(FilePath)
    
    If Len(fileContent) = 0 Then
        ImportCSVFile = False
        Exit Function
    End If
    
    ' Parser le CSV en lignes logiques
    csvLines = ParseCSVContent(fileContent, Delimiter, textQualifier)
    
    startRow = 0
    While (InStr(1, UCase(Trim(CStr(csvLines(startRow)))), "SEVERITY") <= 0 Or InStr(1, UCase(Trim(CStr(csvLines(startRow)))), "PORT") <= 0 Or InStr(1, UCase(Trim(CStr(csvLines(startRow)))), "IP") <= 0 Or InStr(1, UCase(Trim(CStr(csvLines(i)))), "DNS") <= 0 And InStr(1, UCase(Trim(CStr(csvLines(i)))), "NETBIOS") > 0 And InStr(1, UCase(Trim(CStr(csvLines(i)))), "QID") <= 0 And InStr(1, UCase(Trim(CStr(csvLines(i)))), "TITLE") <= 0) And startRow < UBound(csvLines)
        startRow = startRow + 1
    Wend
    Debug.Print "" & csvLines(startRow)
    If IsArray(csvLines) And UBound(csvLines) >= 0 Then
        ' Importer chaque ligne
        For i = startRow + 1 To UBound(csvLines)
            If Len(Trim(CStr(csvLines(i)))) > 0 Then
                ImportCSVLine CStr(csvLines(i)), FileName
            End If
        Next i
    End If
    
    ImportCSVFile = True
    Exit Function
    
ErrorHandler:
    ImportCSVFile = False
    MsgBox "Erreur lors de l'importation du fichier : " & FileName & vbCrLf & Err.Description
End Function

' Fonction pour lire le contenu complet du fichier
Private Function ReadFileContent(FilePath As String) As String
    Dim fileNum As Integer
    Dim fileContent As String
    
    On Error GoTo ErrorHandler
    
    fileNum = FreeFile
    Open FilePath For Binary As fileNum
    
    If LOF(fileNum) > 0 Then
        fileContent = Space$(LOF(fileNum))
        Get fileNum, , fileContent
    End If
    
    Close fileNum
    ReadFileContent = fileContent
    Exit Function
    
ErrorHandler:
    If fileNum > 0 Then Close fileNum
    ReadFileContent = ""
End Function

' Parser CSV robuste qui gère les cas complexes
Private Function ParseCSVContent(content As String, Delimiter As String, textQualifier As String) As Variant
    Dim Lines() As String
    Dim lineCount As Long
    Dim i As Long
    Dim pos As Long
    Dim currentLine As String
    Dim inQuotes As Boolean
    Dim char As String
    Dim nextChar As String
    
    ' Initialiser le tableau de lignes
    ReDim Lines(0 To 1000) ' Taille initiale
    lineCount = 0
    currentLine = ""
    inQuotes = False
    pos = 1
    
    ' Parser caractère par caractère
    Do While pos <= Len(content)
        char = Mid(content, pos, 1)
        
        ' Gérer les qualifiers de texte (guillemets)
        If char = textQualifier Then
            ' Vérifier si c'est un guillemet échappé (doublé)
            If pos < Len(content) Then
                nextChar = Mid(content, pos + 1, 1)
                If nextChar = textQualifier And inQuotes Then
                    ' Guillemet échappé - ajouter un seul guillemet au résultat
                    currentLine = currentLine & textQualifier
                    pos = pos + 2 ' Passer les deux guillemets
                    GoTo nextChar
                End If
            End If
            
            ' Basculer l'état des guillemets
            inQuotes = Not inQuotes
            currentLine = currentLine & char
            
        ' Gérer les sauts de ligne
        ElseIf (char = vbCr Or char = vbLf) Then
            If inQuotes Then
                ' Saut de ligne à l'intérieur des guillemets - faire partie du champ
                currentLine = currentLine & char
            Else
                ' Fin de ligne logique
                If Len(Trim(currentLine)) > 0 Then
                    ' Redimensionner le tableau si nécessaire
                    If lineCount > UBound(Lines) Then
                        ReDim Preserve Lines(0 To UBound(Lines) + 1000)
                    End If
                    Lines(lineCount) = currentLine
                    lineCount = lineCount + 1
                End If
                currentLine = ""
            End If
            
            ' Gérer CRLF (passer le LF si on vient de traiter CR)
            If char = vbCr And pos < Len(content) Then
                If Mid(content, pos + 1, 1) = vbLf Then
                    pos = pos + 1
                End If
            End If
            
        Else
            ' Caractère normal
            currentLine = currentLine & char
        End If
        
nextChar:
        pos = pos + 1
    Loop
    
    ' Ajouter la dernière ligne si elle n'est pas vide
    If Len(Trim(currentLine)) > 0 Then
        If lineCount > UBound(Lines) Then
            ReDim Preserve Lines(0 To lineCount)
        End If
        Lines(lineCount) = currentLine
        lineCount = lineCount + 1
    End If
    
    ' Redimensionner le tableau à la taille exacte
    If lineCount > 0 Then
        ReDim Preserve Lines(0 To lineCount - 1)
        ParseCSVContent = Lines
    Else
        ' Retourner un tableau vide avec la bonne structure
        ReDim Lines(0 To -1)
        ParseCSVContent = Lines
    End If
End Function

' Parser une ligne CSV en champs individuels
Private Function ParseCSVLine(csvLine As String, Delimiter As String, textQualifier As String) As Variant
    Dim fields() As String
    Dim fieldCount As Long
    Dim i As Long
    Dim pos As Long
    Dim currentField As String
    Dim inQuotes As Boolean
    Dim char As String
    Dim nextChar As String
    
    ReDim fields(0 To 100) ' Taille initiale
    fieldCount = 0
    currentField = ""
    inQuotes = False
    pos = 1
    
    Do While pos <= Len(csvLine)
        char = Mid(csvLine, pos, 1)
        
        If char = textQualifier Then
            ' Vérifier si c'est un guillemet échappé
            If pos < Len(csvLine) Then
                nextChar = Mid(csvLine, pos + 1, 1)
                If nextChar = textQualifier And inQuotes Then
                    ' Guillemet échappé
                    currentField = currentField & textQualifier
                    pos = pos + 2
                    GoTo NextCharInLine
                End If
            End If
            
            ' Basculer l'état des guillemets
            inQuotes = Not inQuotes
            
        ElseIf char = Delimiter And Not inQuotes Then
            ' Délimiteur trouvé hors guillemets - fin de champ
            If fieldCount > UBound(fields) Then
                ReDim Preserve fields(0 To UBound(fields) + 100)
            End If
            
            ' Nettoyer le champ (enlever les guillemets externes)
            fields(fieldCount) = CleanField(currentField, textQualifier)
            fieldCount = fieldCount + 1
            currentField = ""
            
        Else
            ' Caractère normal
            currentField = currentField & char
        End If
        
NextCharInLine:
        pos = pos + 1
    Loop
    
    ' Ajouter le dernier champ
    If fieldCount > UBound(fields) Then
        ReDim Preserve fields(0 To fieldCount)
    End If
    fields(fieldCount) = CleanField(currentField, textQualifier)
    fieldCount = fieldCount + 1
    
    ' Redimensionner à la taille exacte
    ReDim Preserve fields(0 To fieldCount - 1)
    ParseCSVLine = fields
End Function

' Nettoyer un champ (enlever les guillemets externes et gérer l'échappement)
Private Function CleanField(Field As String, textQualifier As String) As String
    Dim Result As String
    Result = Trim(Field)
    
    ' Enlever les guillemets externes si présents
    If Len(Result) >= 2 Then
        If Left(Result, 1) = textQualifier And Right(Result, 1) = textQualifier Then
            Result = Mid(Result, 2, Len(Result) - 2)
        End If
    End If
    
    CleanField = Result
End Function

' Importer une ligne CSV dans la feuille
Private Sub ImportCSVLine(csvLine As String, FileName As String)
    Dim fields As Variant
    Dim col As Long
    
    ' Parser la ligne en champs
    fields = ParseCSVLine(csvLine, ",", """")
    
    ' Ajouter le nom du fichier dans la première colonne
    ws.Cells(pCurrentRow, 1).value = FileName
    
    ' Importer les champs à partir de la colonne spécifiée
    If IsArray(fields) Then
        For col = 0 To UBound(fields)
            ws.Cells(pCurrentRow, startColumn + col).value = CStr(fields(col))
        Next col
    End If
    
    pCurrentRow = pCurrentRow + 1
End Sub

' Méthode pour formater les données importées
Public Sub FormatImportedData()
    Dim lastRow As Long
    Dim lastCol As Long
    
    ' Trouver la dernière ligne et colonne utilisées
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow < 1 Then lastRow = 1
    
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If lastCol < 1 Then lastCol = 1
    
    ' Appliquer un formatage basique
    With ws.Range(ws.Cells(1, 1), ws.Cells(lastRow, lastCol))
        .Borders.LineStyle = xlContinuous
        .Borders.Weight = xlThin
    End With
    
    ' Formater la première colonne (noms de fichiers)
    With ws.Range(ws.Cells(1, 1), ws.Cells(lastRow, 1))
        .Font.Bold = True
        .Interior.Color = RGB(220, 230, 241)
    End With
    
    ' Ajuster automatiquement la largeur des colonnes
    ws.Columns.AutoFit
End Sub

' Méthode utilitaire pour tester l'import avec une chaîne CSV
Public Sub TestCSVParsing(csvString As String)
    Dim Lines As Variant
    Dim fields As Variant
    Dim i As Long, j As Long
    
    Debug.Print "=== Test de parsing CSV ==="
    Debug.Print "Chaîne d'entrée: " & csvString
    Debug.Print ""
    
    Lines = ParseCSVContent(csvString, ",", """")
    
    If IsArray(Lines) And UBound(Lines) >= 0 Then
        For i = 0 To UBound(Lines)
            Debug.Print "Ligne " & (i + 1) & ": " & CStr(Lines(i))
            fields = ParseCSVLine(CStr(Lines(i)), ",", """")
            
            If IsArray(fields) Then
                For j = 0 To UBound(fields)
                    Debug.Print "  Champ " & (j + 1) & ": [" & CStr(fields(j)) & "]"
                Next j
            End If
            Debug.Print ""
        Next i
    Else
        Debug.Print "Aucune ligne trouvée"
    End If
End Sub
