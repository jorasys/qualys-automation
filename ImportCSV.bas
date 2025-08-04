Attribute VB_Name = "ImportCSV"
' Procédure principale pour importer les fichiers CSV
Public Sub ImporterFichiersCSV()
    Dim FileManager As FileManager
    Dim CSVImporter As CSVImporter
    Dim targetSheet As Worksheet
    Dim FileName As Variant
    Dim importCount As Long
    Dim errorCount As Long
    
    ' Initialiser les objets
    Set FileManager = New FileManager
    Set CSVImporter = New CSVImporter
    
    ' Sélectionner les fichiers CSV
    If Not FileManager.SelectCSVFiles() Then
        MsgBox "Aucun fichier sélectionné."
        Exit Sub
    End If
    
    ' Vérifier qu'au moins un fichier a été sélectionné
    If FileManager.FileCount = 0 Then
        MsgBox "Aucun fichier sélectionné."
        Exit Sub
    End If
    
    ' Préparer la feuille de destination
    Set targetSheet = PrepareTargetSheet()
    
    ' Initialiser l'importateur CSV
    CSVImporter.Initialize targetSheet, 4 ' Commencer à la colonne D
    
    ' Importer chaque fichier sélectionné
    For Each FileName In FileManager.Files
        If CSVImporter.ImportCSVFile(CStr(FileName)) Then
            importCount = importCount + 1
        Else
            errorCount = errorCount + 1
        End If
    Next FileName
    
    ' Formater les données importées
'    csvImporter.FormatImportedData
    
    ' Afficher le résumé de l'importation
    MsgBox "Importation terminée !" & vbCrLf & _
           "Fichiers importés avec succès : " & importCount & vbCrLf & _
           "Erreurs : " & errorCount
End Sub

' Fonction pour préparer la feuille de destination
Private Function PrepareTargetSheet() As Worksheet
    Dim ws As Worksheet
    Dim response As VbMsgBoxResult
    
    ' Demander à l'utilisateur s'il veut utiliser la feuille active ou en créer une nouvelle
    response = MsgBox("Voulez-vous utiliser la feuille active pour l'importation ?" & vbCrLf & _
                     "Cliquez sur 'Non' pour créer une nouvelle feuille.", _
                     vbYesNoCancel + vbQuestion, "Feuille de destination")
    
    Select Case response
        Case vbYes
            Set ws = ActiveSheet
            ' Vider la feuille active
            ws.Cells.Clear
            
        Case vbNo
            ' Créer une nouvelle feuille
            Set ws = Worksheets.Add
            ws.Name = "Import_CSV_" & Format(Now, "yyyymmdd_hhmmss")
            
        Case vbCancel
            Set PrepareTargetSheet = Nothing
            Exit Function
    End Select
    
    ' Ajouter les en-têtes
'    ws.Cells(1, 1).value = "Fichier Source"
'    ws.Cells(1, 2).value = "Ligne"
'    ws.Cells(1, 3).value = "Données CSV"
    
'    ' Formater les en-têtes
'    With ws.Range("A1:C1")
'        .Font.Bold = True
'        .Interior.Color = RGB(184, 204, 228)
'        .Borders.LineStyle = xlContinuous
'    End With
    
    Set PrepareTargetSheet = ws
End Function

' Procédure pour nettoyer les données importées
Public Sub NettoyerDonnees()
    Dim ws As Worksheet
    Dim response As VbMsgBoxResult
    
    Set ws = ActiveSheet
    
    response = MsgBox("Êtes-vous sûr de vouloir effacer toutes les données de la feuille active ?", _
                     vbYesNo + vbCritical, "Confirmation")
    
    If response = vbYes Then
        ws.Cells.Clear
        MsgBox "Données effacées."
    End If
End Sub

