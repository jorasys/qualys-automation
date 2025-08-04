Attribute VB_Name = "ConvertDate"
Sub ConvertirFormatDates()
    Dim ws As Worksheet
    Dim colonneActive As Long
    Dim derniereLigne As Long
    Dim i As Long
    Dim cellule As Range
    Dim dateTexte As String
    Dim dateConvertie As Date
    Dim compteurConverties As Long
    Dim fichierLog As String
    Dim numFichier As Integer
    
    On Error GoTo GestionErreur
    
    ' Obtenir un numéro de fichier libre
    numFichier = FreeFile
    
    ' Créer le fichier de log
    fichierLog = Environ("USERPROFILE") & "\Downloads\log_conversion_" & Format(Now, "yyyymmdd_hhmmss") & ".txt"
    Open fichierLog For Output As numFichier
    
    Print #numFichier, "=== DÉBUT ConvertirFormatDates ==="
    Print #numFichier, "Date/Heure: " & Now
    
    ' Initialisation
    Set ws = ActiveSheet
    colonneActive = ActiveCell.Column
    compteurConverties = 0
    
    Print #numFichier, "Feuille: " & ws.Name
    Print #numFichier, "Colonne active: " & colonneActive & " (" & Split(Cells(1, colonneActive).Address, "$")(1) & ")"
    
    ' Trouver la dernière ligne avec des données dans la colonne active
    derniereLigne = ws.Cells(ws.Rows.Count, colonneActive).End(xlUp).Row
    Print #numFichier, "Dernière ligne: " & derniereLigne
    
    ' Vérifier s'il y a des données
    If derniereLigne < 1 Then
        Print #numFichier, "Aucune donnée trouvée"
        Close numFichier
        MsgBox "Aucune donnée trouvée dans la colonne active.", vbInformation
        Exit Sub
    End If
    
    ' Désactiver les calculs automatiques pour améliorer les performances
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Parcourir chaque cellule de la colonne active
    For i = 1 To derniereLigne
        Set cellule = ws.Cells(i, colonneActive)
        
        Print #numFichier, "Ligne " & i & ": Valeur='" & cellule.value & "', Type=" & TypeName(cellule.value)
        
        ' Vérifier si la cellule contient du texte (potentiellement une date)
        If Not IsEmpty(cellule.value) And VarType(cellule.value) = vbString Then
            dateTexte = Trim(cellule.value)
            Print #numFichier, "  Texte nettoyé: '" & dateTexte & "'"
            
            ' Vérifier si le texte correspond au format mm/dd/yyyy
            If EstFormatDateAmericain(dateTexte, numFichier) Then
                Print #numFichier, "  Format US détecté"
                
                ' Convertir la date
                If ConvertirDateUS(dateTexte, dateConvertie, numFichier) Then
                    Print #numFichier, "  Conversion réussie: " & dateConvertie
                    ' Appliquer le nouveau format dd/mm/yyyy
                    cellule.value = dateConvertie
                    cellule.NumberFormat = "dd/mm/yyyy"
                    compteurConverties = compteurConverties + 1
                Else
                    Print #numFichier, "  Échec de la conversion"
                End If
            Else
                Print #numFichier, "  Format US non détecté"
            End If
        ElseIf Not IsEmpty(cellule.value) And IsDate(cellule.value) Then
            ' Si c'est déjà une date, vérifier le format d'affichage
            Print #numFichier, "  Déjà une date: " & cellule.value
            cellule.NumberFormat = "dd/mm/yyyy"
        Else
            Print #numFichier, "  Cellule vide ou non-texte"
        End If
    Next i
    
    ' Réactiver les paramètres
    Application.EnableEvents = True
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    
    Print #numFichier, "Total converties: " & compteurConverties
    Print #numFichier, "=== FIN ConvertirFormatDates ==="
    Close numFichier
    
    ' Message de confirmation
    If compteurConverties > 0 Then
        MsgBox compteurConverties & " date(s) convertie(s) du format mm/dd/yyyy vers dd/mm/yyyy dans la colonne " & _
               Split(Cells(1, colonneActive).Address, "$")(1) & vbCrLf & _
               "Log créé: " & fichierLog, vbInformation, "Conversion terminée"
    Else
        MsgBox "Aucune date au format mm/dd/yyyy trouvée dans la colonne active." & vbCrLf & _
               "Log créé: " & fichierLog, vbInformation, "Aucune conversion"
    End If
    
    Exit Sub
    
GestionErreur:
    ' Réactiver les paramètres en cas d'erreur
    Application.EnableEvents = True
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    
    If numFichier > 0 Then Close numFichier
    
    MsgBox "Erreur: " & Err.Description & vbCrLf & "Ligne: " & Erl, vbCritical
End Sub

' Fonction pour vérifier le format de date américain (sans regex)
Private Function EstFormatDateAmericain(texte As String, Optional numFichier As Integer = 0) As Boolean
    Dim partiesDate As Variant
    Dim partieDate As String
    Dim mois As Integer, jour As Integer, annee As Integer
    
    EstFormatDateAmericain = False
    
    If numFichier > 0 Then
        Print #numFichier, "    Test format US pour: '" & texte & "'"
    End If
    
    ' Extraire seulement la partie date (ignorer l'heure si présente)
    If InStr(texte, " ") > 0 Then
        partieDate = Left(texte, InStr(texte, " ") - 1)
    Else
        partieDate = texte
    End If
    
    ' Vérifier la présence de "/" et longueur minimale
    If InStr(partieDate, "/") = 0 Or Len(partieDate) < 8 Then
        If numFichier > 0 Then Print #numFichier, "    Pas de / ou trop court"
        Exit Function
    End If
    
    ' Diviser par "/"
    partiesDate = Split(partieDate, "/")
    
    ' Vérifier qu'on a exactement 3 parties
    If UBound(partiesDate) <> 2 Then
        If numFichier > 0 Then Print #numFichier, "    Pas exactement 3 parties"
        Exit Function
    End If
    
    On Error Resume Next
    
    ' Vérifier que chaque partie est numérique et dans les bonnes plages
    mois = CInt(partiesDate(0))
    jour = CInt(partiesDate(1))
    annee = CInt(partiesDate(2))
    
    If Err.Number <> 0 Then
        If numFichier > 0 Then Print #numFichier, "    Erreur conversion numérique"
        On Error GoTo 0
        Exit Function
    End If
    
    On Error GoTo 0
    
    ' Vérifier les plages de valeurs
    If mois >= 1 And mois <= 12 And jour >= 1 And jour <= 31 And annee >= 1900 And annee <= 2100 Then
        EstFormatDateAmericain = True
        If numFichier > 0 Then Print #numFichier, "    Format US valide: " & mois & "/" & jour & "/" & annee
    Else
        If numFichier > 0 Then Print #numFichier, "    Valeurs hors limites: " & mois & "/" & jour & "/" & annee
    End If
End Function

' Fonction pour convertir une date du format US vers une date VBA
Private Function ConvertirDateUS(texte As String, ByRef dateResult As Date, Optional numFichier As Integer = 0) As Boolean
    Dim partiesDate As Variant
    Dim partieDate As String
    Dim mois As Integer, jour As Integer, annee As Integer
    
    ConvertirDateUS = False
    
    On Error GoTo ErreurConversion
    
    ' Extraire la partie date
    If InStr(texte, " ") > 0 Then
        partieDate = Left(texte, InStr(texte, " ") - 1)
    Else
        partieDate = texte
    End If
    
    ' Diviser les composants
    partiesDate = Split(partieDate, "/")
    
    mois = CInt(partiesDate(0))
    jour = CInt(partiesDate(1))
    annee = CInt(partiesDate(2))
    
    ' Créer la date avec DateSerial (plus fiable que DateValue)
    dateResult = DateSerial(annee, mois, jour)
    
    ConvertirDateUS = True
    
    If numFichier > 0 Then
        Print #numFichier, "    Conversion: " & mois & "/" & jour & "/" & annee & " -> " & dateResult
    End If
    
    Exit Function
    
ErreurConversion:
    ConvertirDateUS = False
    If numFichier > 0 Then
        Print #numFichier, "    Erreur conversion: " & Err.Description
    End If
End Function

' Version simplifiée alternative
Sub ConvertirFormatDatesSimple()
    Dim ws As Worksheet
    Dim colonneActive As Long
    Dim derniereLigne As Long
    Dim i As Long
    Dim cellule As Range
    Dim dateTexte As String
    Dim partiesDate As Variant
    Dim dateConvertie As Date
    Dim compteurConverties As Long
    
    Set ws = ActiveSheet
    colonneActive = ActiveCell.Column
    compteurConverties = 0
    
    derniereLigne = ws.Cells(ws.Rows.Count, colonneActive).End(xlUp).Row
    
    If derniereLigne < 1 Then
        MsgBox "Aucune donnée trouvée dans la colonne active.", vbInformation
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    For i = 1 To derniereLigne
        Set cellule = ws.Cells(i, colonneActive)
        
        If Not IsEmpty(cellule.value) And VarType(cellule.value) = vbString Then
            dateTexte = Trim(CStr(cellule.value))
            
            ' Extraire la partie date si présence d'heure
            If InStr(dateTexte, " ") > 0 Then
                dateTexte = Left(dateTexte, InStr(dateTexte, " ") - 1)
            End If
            
            ' Vérifier format mm/dd/yyyy
            If InStr(dateTexte, "/") > 0 And Len(dateTexte) >= 8 Then
                partiesDate = Split(dateTexte, "/")
                
                If UBound(partiesDate) = 2 Then
                    On Error Resume Next
                    dateConvertie = DateSerial(CInt(partiesDate(2)), CInt(partiesDate(0)), CInt(partiesDate(1)))
                    
                    If Err.Number = 0 Then
                        cellule.value = dateConvertie
                        cellule.NumberFormat = "dd/mm/yyyy"
                        compteurConverties = compteurConverties + 1
                    End If
                    
                    On Error GoTo 0
                End If
            End If
        End If
    Next i
    
    Application.ScreenUpdating = True
    
    MsgBox compteurConverties & " date(s) convertie(s) du format mm/dd/yyyy vers dd/mm/yyyy.", vbInformation
End Sub

