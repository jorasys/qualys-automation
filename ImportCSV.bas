Attribute VB_Name = "ImportCSV"
' Proc�dure principale pour importer les fichiers CSV
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
    
    ' S�lectionner les fichiers CSV
    If Not FileManager.SelectCSVFiles() Then
        MsgBox "Aucun fichier s�lectionn�."
        Exit Sub
    End If
    
    ' V�rifier qu'au moins un fichier a �t� s�lectionn�
    If FileManager.FileCount = 0 Then
        MsgBox "Aucun fichier s�lectionn�."
        Exit Sub
    End If
    
    ' Pr�parer la feuille de destination
    Set targetSheet = PrepareTargetSheet()
    
    ' Initialiser l'importateur CSV
    CSVImporter.Initialize targetSheet, 4 ' Commencer � la colonne D
    
    ' Importer chaque fichier s�lectionn�
    For Each FileName In FileManager.Files
        If CSVImporter.ImportCSVFile(CStr(FileName)) Then
            importCount = importCount + 1
        Else
            errorCount = errorCount + 1
        End If
    Next FileName
    
    ' Formater les donn�es import�es
'    csvImporter.FormatImportedData
    
    ' Afficher le r�sum� de l'importation
    MsgBox "Importation termin�e !" & vbCrLf & _
           "Fichiers import�s avec succ�s : " & importCount & vbCrLf & _
           "Erreurs : " & errorCount
End Sub

' Fonction pour pr�parer la feuille de destination
Private Function PrepareTargetSheet() As Worksheet
    Dim ws As Worksheet
    Dim response As VbMsgBoxResult
    
    ' Demander � l'utilisateur s'il veut utiliser la feuille active ou en cr�er une nouvelle
    response = MsgBox("Voulez-vous utiliser la feuille active pour l'importation ?" & vbCrLf & _
                     "Cliquez sur 'Non' pour cr�er une nouvelle feuille.", _
                     vbYesNoCancel + vbQuestion, "Feuille de destination")
    
    Select Case response
        Case vbYes
            Set ws = ActiveSheet
            ' Vider la feuille active
            ws.Cells.Clear
            
        Case vbNo
            ' Cr�er une nouvelle feuille
            Set ws = Worksheets.Add
            ws.Name = "Import_CSV_" & Format(Now, "yyyymmdd_hhmmss")
            
        Case vbCancel
            Set PrepareTargetSheet = Nothing
            Exit Function
    End Select
    
    ' Ajouter les en-t�tes
'    ws.Cells(1, 1).value = "Fichier Source"
'    ws.Cells(1, 2).value = "Ligne"
'    ws.Cells(1, 3).value = "Donn�es CSV"
    
'    ' Formater les en-t�tes
'    With ws.Range("A1:C1")
'        .Font.Bold = True
'        .Interior.Color = RGB(184, 204, 228)
'        .Borders.LineStyle = xlContinuous
'    End With
    
    Set PrepareTargetSheet = ws
End Function

' Proc�dure pour nettoyer les donn�es import�es
Public Sub NettoyerDonnees()
    Dim ws As Worksheet
    Dim response As VbMsgBoxResult
    
    Set ws = ActiveSheet
    
    response = MsgBox("�tes-vous s�r de vouloir effacer toutes les donn�es de la feuille active ?", _
                     vbYesNo + vbCritical, "Confirmation")
    
    If response = vbYes Then
        ws.Cells.Clear
        MsgBox "Donn�es effac�es."
    End If
End Sub

