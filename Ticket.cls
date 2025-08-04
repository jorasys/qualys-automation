VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Ticket"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Private pEnvData As EnvData
Private pTitlesDict As Object
Private pFooter As String
Private pHeader As String
Private pNumber As Long
Private pQidsDict As Object
Private pTargetsDict As Object
Private pResultsDict As Object
Private pThreatsDict As Object
Private pImpactsDict As Object
Private pSolutionsDict As Object
Private pTitle As String
Private pCveDict As Object
Private pMaxSeverityScore As Long
Private pMaxCVEScore As Long


Private Sub Class_Initialize()
    Set pTitlesDict = CreateObject("Scripting.Dictionary")
    pTitle = ""
    Set pQidsDict = CreateObject("Scripting.Dictionary")
    Set pTargetsDict = CreateObject("Scripting.Dictionary")
    Set pResultsDict = CreateObject("Scripting.Dictionary")
    Set pThreatsDict = CreateObject("Scripting.Dictionary")
    Set pImpactsDict = CreateObject("Scripting.Dictionary")
    Set pSolutionsDict = CreateObject("Scripting.Dictionary")
    Set pCveDict = CreateObject("Scripting.Dictionary")
    pMaxSeverityScore = 0
    pMaxCVEScore = 0
End Sub

Public Sub Initialize(ByVal envDataValue As EnvData)
    Set pEnvData = envDataValue
    pTitle = "[PCI][QUALYS][" & pEnvData.Name & "]"
    pNumber = CLng(InputBox("Veuillez entrer le numéro de ticket pour l'environnement " & pEnvData.Name & ":", "Numéro de Ticket"))
    pHeader = pHeader & "Bonjour," & vbCrLf & "Des vulnérabilités ont été détectées via la solution de scan Qualys :"
    Dim i As Long
    Dim dataObj As Data
    For i = 1 To pEnvData.Count
        Set dataObj = pEnvData.DataList(i)
        If Not pQidsDict.Exists(dataObj.qid) Then
            pQidsDict.Add dataObj.qid, "(Severity: " & dataObj.Severite & " - " & dataObj.TypeFormate & ")"
            If CLng(dataObj.Severite) > pMaxSeverityScore Then
                pMaxSeverityScore = CLng(dataObj.Severite)
            End If
            
        End If
        Dim target As String
        target = dataObj.ip
        
        ' Ajouter le port uniquement s'il existe
        If Len(Trim(dataObj.Port)) > 0 Then
            target = target & ":" & dataObj.Port
        End If
        
        ' Ajouter le protocole uniquement s'il existe
        If Len(Trim(dataObj.Protocole)) > 0 Then
            target = target & "/" & dataObj.Protocole
        End If
        
        If Not pTargetsDict.Exists(target) Then
            pTargetsDict.Add target, "(" & dataObj.Dns & ")"
        End If
        
        If Not pResultsDict.Exists(dataObj.Result) Then
            pResultsDict.Add dataObj.Result, New Collection
        End If
        pResultsDict(dataObj.Result).Add target
        
        If Not pThreatsDict.Exists(dataObj.Threat) Then
            pThreatsDict.Add dataObj.Threat, New Collection
        End If
        pThreatsDict(dataObj.Threat).Add target
        
        If Not pImpactsDict.Exists(dataObj.Impact) Then
            pImpactsDict.Add dataObj.Impact, New Collection
        End If
        pImpactsDict(dataObj.Impact).Add target
        
        If Not pSolutionsDict.Exists(dataObj.Solution) Then
            pSolutionsDict.Add dataObj.Solution, New Collection
        End If
        pSolutionsDict(dataObj.Solution).Add target
        
        If Not pTitlesDict.Exists(dataObj.Title) Then
            pTitlesDict.Add dataObj.Title, ""
        End If
        
        If Len(dataObj.cve) > 0 Then
            Dim arrCve() As String
            arrCve = Split(dataObj.cve, ",")
            ' Optionnel: nettoyage des éléments du tableau
            Dim j As Long
            For j = LBound(arrCve) To UBound(arrCve)
                If Not pCveDict.Exists(Trim(arrCve(j))) Then
                    pCveDict.Add Trim(arrCve(j)), GetCVEDetails(arrCve(j))
                End If
            Next j
        End If
    Next i
    pTitle = pTitle & " " & Join(pTitlesDict.Keys, " / ")
    pFooter = "Merci d'avance pour votre prise en compte et votre retour sur les actions envisagées."
    
End Sub
' Fonction qui récupère les détails d'une CVE via l'API NVD
' @param cveID - L'identifiant CVE au format "CVE-YYYY-NNNNN"
' @return - Une chaîne contenant l'intitulé et le score CVSS 3 séparés par un pipe (|)
Function GetCVEDetails(cveID As String) As String
    Dim xmlHTTP As Object
    Dim jsonText As String
    Dim Result As String
    Dim apiKey As String
    
    On Error GoTo ErrorHandler
    
    ' Clé API NVD fournie
    apiKey = "ac1217d5-6d6e-4607-834b-d475da755404"
    
    ' Vérification du format de l'identifiant CVE
    cveID = Trim(cveID)
    If Not (Left(cveID, 4) = "CVE-") Then
        GetCVEDetails = "Erreur: Format CVE invalide. Utilisez le format 'CVE-YYYY-NNNNN'."
        Exit Function
    End If
    
    ' Créer un objet pour effectuer la requête HTTP
    Set xmlHTTP = CreateObject("MSXML2.ServerXMLHTTP.5.1")
    
    ' Configuration des timeouts
'    xmlHTTP.setTimeouts 30000, 30000, 30000, 30000
    
    xmlHTTP.Open "GET", apiUrl, False
    xmlHTTP.setRequestHeader "User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    xmlHTTP.setRequestHeader "Accept", "application/json,*/*;q=0.8"
    xmlHTTP.setRequestHeader "X-API-KEY", apiKey
    
    ' Envoyer la requête
    xmlHTTP.send

    Debug.Print xmlHTTP.Status
    ' Vérifier si la requête a réussi
    If xmlHTTP.Status = 200 Then
        ' Récupérer la réponse JSON
        jsonText = xmlHTTP.responseText
        
        ' Extraire manuellement les informations requises du JSON
        Dim cveTitle As String
        Dim cvssScore As String
        
        ' Extraire le titre depuis le JSON (méthode manuelle)
        cveTitle = ExtractCVETitle(jsonText)
        If cveTitle = "" Then
            cveTitle = "Titre non disponible"
        End If
        
        ' Extraire le score CVSS 3 depuis le JSON (méthode manuelle)
        cvssScore = ExtractCVSS3Score(jsonText)
        If cvssScore = "" Then
            cvssScore = "Score CVSS3 non disponible"
        End If
        
        ' Construire la réponse finale
        Result = cvssScore
    Else
        ' Gérer les erreurs de l'API
        Result = "Erreur API: " & xmlHTTP.Status & " - " & xmlHTTP.statusText
    End If
    
    ' Nettoyage
    Set xmlHTTP = Nothing
    
    GetCVEDetails = Result
    Exit Function
    
ErrorHandler:
    GetCVEDetails = "Erreur"
    Debug.Print "Erreur: " & Err.Number & " - " & Err.Description
    Resume ExitFunction
    
ExitFunction:
    ' Nettoyage en cas d'erreur
    If Not xmlHTTP Is Nothing Then Set xmlHTTP = Nothing
End Function

' Fonction pour extraire le titre d'une CVE à partir de la réponse JSON de NVD
Function ExtractCVETitle(jsonStr As String) As String
    Dim startPos As Long
    Dim endPos As Long
    
    ' Rechercher la section "descriptions" qui contient le titre en anglais
    startPos = InStr(1, jsonStr, """descriptions""")
    If startPos = 0 Then Exit Function
    
    ' Chercher le premier descriptif en anglais
    startPos = InStr(startPos, jsonStr, """lang"":""en""")
    If startPos = 0 Then Exit Function
    
    ' Trouver la valeur du champ "value" qui contient le titre
    startPos = InStr(startPos, jsonStr, """value""")
    If startPos = 0 Then Exit Function
    
    ' Trouver le début de la valeur (après les deux points et les guillemets)
    startPos = InStr(startPos, jsonStr, ":")
    If startPos = 0 Then Exit Function
    
    ' Trouver le guillemet ouvrant
    startPos = InStr(startPos, jsonStr, """")
    If startPos = 0 Then Exit Function
    
    ' Avancer après le guillemet ouvrant
    startPos = startPos + 1
    
    ' Trouver le guillemet fermant (fin du titre)
    endPos = InStr(startPos, jsonStr, """")
    If endPos = 0 Then Exit Function
    
    ' Extraire le titre
    ExtractCVETitle = Mid(jsonStr, startPos, endPos - startPos)
End Function

' Fonction pour extraire uniquement le score CVSS 3.x (3.0 ou 3.1)
Function ExtractCVSS3Score(jsonStr As String) As String
    Dim startPos As Long
    Dim endPos As Long
    
    ' Rechercher la section CVSS 3.1 d'abord (priorité à la version plus récente)
    startPos = InStr(1, jsonStr, """cvssData""")
    If startPos = 0 Then Exit Function
    
    ' Chercher le champ "baseScore" dans cette section
    startPos = InStr(startPos, jsonStr, """baseScore""")
    If startPos = 0 Then Exit Function
    
    ' Trouver le début de la valeur (après les deux points)
    startPos = InStr(startPos, jsonStr, ":")
    If startPos = 0 Then Exit Function
    
    ' Avancer après les deux points
    startPos = startPos + 1
    
    ' Ignorer les espaces éventuels
    Do While Mid(jsonStr, startPos, 1) = " "
        startPos = startPos + 1
    Loop
    
    ' Trouver la fin de la valeur (virgule ou accolade)
    endPos = InStr(startPos, jsonStr, ",")
    If endPos = 0 Then
        endPos = InStr(startPos, jsonStr, "}")
    End If
    
    If endPos > 0 Then
        ExtractCVSS3Score = Trim(Mid(jsonStr, startPos, endPos - startPos))
    End If
End Function

Public Sub Show(Optional ByVal showDetails As Boolean = False)
    Dim Key As Variant
    Dim i As Long
    Dim items() As String
    
    Debug.Print String(80, "=") & vbCrLf
    Debug.Print pTitle
    If pMaxSeverityScore >= 4 Then
        Debug.Print "Priority: 1"
    Else
        If pMaxSeverityScore >= 2 Then
            Debug.Print "Priority: 3"
        Else
            Debug.Print "Priority: 5"
        End If
    End If
    Debug.Print "Ticket: " & pNumber & vbCrLf
    Debug.Print String(80, "=") & vbCrLf

    Debug.Print pHeader
    
    Debug.Print vbCrLf & "QID:"
    For Each Key In pQidsDict.Keys
        Debug.Print "  " & Key & " " & pQidsDict(Key)
    Next Key
    
    Debug.Print vbCrLf & "TARGETS:"
    For Each Key In pTargetsDict.Keys
        Debug.Print "  " & Key & " " & pTargetsDict(Key)
    Next Key
    
    If pResultsDict.Count > 0 Then
        Debug.Print vbCrLf & "RESULTS:"
        For Each Key In pResultsDict.Keys
            If pResultsDict.Count > 1 Then
                ReDim items(pResultsDict(Key).Count - 1)
                For i = 1 To pResultsDict(Key).Count
                     items(i - 1) = pResultsDict(Key)(i)
                Next i
                Debug.Print "  " & Join(items, ", ")
            End If
            Debug.Print "    " & Key
        Next Key
    End If
    
    If pThreatsDict.Count > 0 Then
    Debug.Print vbCrLf & "THREATS:"
        For Each Key In pThreatsDict.Keys
            If pThreatsDict.Count > 1 Then
                ReDim items(pThreatsDict(Key).Count)
                For i = 1 To pThreatsDict(Key).Count
                     items(i - 1) = pThreatsDict(Key)(i)
                Next i
                Debug.Print "  " & Join(items, ", ")
            End If
            Debug.Print Key
        Next Key
    End If
    
    If pImpactsDict.Count > 0 Then
        Debug.Print vbCrLf & "IMPACTS:"
        For Each Key In pImpactsDict.Keys
            If pImpactsDict.Count > 1 Then
                ReDim items(pImpactsDict(Key).Count)
                For i = 1 To pImpactsDict(Key).Count
                     items(i - 1) = pImpactsDict(Key)(i)
                Next i
                Debug.Print "  " & Join(items, ", ")
            End If
            Debug.Print Key
        Next Key
    End If
    
    If pSolutionsDict.Count > 0 Then
        Debug.Print vbCrLf & "SOLUTIONS:"
        For Each Key In pSolutionsDict.Keys
            If pSolutionsDict.Count > 1 Then
                ReDim items(pSolutionsDict(Key).Count)
                For i = 1 To pSolutionsDict(Key).Count
                     items(i - 1) = pSolutionsDict(Key)(i)
                Next i
                Debug.Print "  " & Join(items, ", ")
            End If
            Debug.Print Key
        Next Key
    End If
    
    If pCveDict.Count > 0 Then
        Debug.Print vbCrLf & "CVES:"
        For Each Key In pCveDict.Keys
            Debug.Print "    " & Key & " (CVSS3:" & pCveDict(Key) & ")"
        Next Key
    End If
    
    Debug.Print vbCrLf & pFooter
End Sub
' Fonction pour ajouter une ligne dans la feuille TICKETS
Public Sub AjouterLigneTicket()
    Dim wsTickets As Worksheet
    Dim lastRow As Long
    Dim machine As Variant
    
    ' Vérifier si la feuille TICKETS existe
    On Error Resume Next
    Set wsTickets = ThisWorkbook.Sheets("TICKETS")
    On Error GoTo 0
    
    ' Si la feuille n'existe pas, sortir de la fonction
    If wsTickets Is Nothing Then
        MsgBox "La feuille 'TICKETS' n'existe pas dans ce classeur.", vbExclamation
        Exit Sub
        
        ' Décommentez les lignes ci-dessous si vous voulez créer la feuille automatiquement
        'Set wsTickets = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        'wsTickets.Name = "TICKETS"
        'wsTickets.Range("A1:E1").Value = Array("N°", "Status", "Title", "QID", "IP")
        'wsTickets.Range("A1:E1").Font.Bold = True
    End If
    
    ' Trouver la dernière ligne utilisée
    lastRow = wsTickets.Cells(wsTickets.Rows.Count, 1).End(xlUp).Row + 1
    
    ' Ajouter les données dans la feuille
    wsTickets.Cells(lastRow, 1).value = pNumber        ' N°
    wsTickets.Cells(lastRow, 2).value = "nouveau"         ' Status (par défaut "nouveau")
    wsTickets.Cells(lastRow, 3).value = pTitle           ' Title
    wsTickets.Cells(lastRow, 4).NumberFormat = "@"
    wsTickets.Cells(lastRow, 5).NumberFormat = "@"
    wsTickets.Cells(lastRow, 4).value = Join(pQidsDict.Keys, ",")           ' QID
    wsTickets.Cells(lastRow, 5).value = Join(pTargetsDict.Keys, ",")             ' IP/Environment
    wsTickets.Cells(lastRow, 6).value = Format(Date, "dd/mm/yyyy")
    wsTickets.Cells(lastRow, 7).value = pMaxSeverityScore
End Sub
Public Sub Export(Optional ByVal FilePath As String = "", Optional ByVal showDetails As Boolean = False)
    Dim Key As Variant
    Dim i As Long
    Dim items() As String
    Dim fileContent As String
    Dim fileNum As Integer
    Dim FileName As String
    Dim defaultPath As String
    
    On Error GoTo ErrorHandler
    
    ' Générer le contenu du fichier
    fileContent = String(80, "=") & vbCrLf
    fileContent = fileContent & pTitle & vbCrLf
    
    If pMaxSeverityScore >= 4 Then
        fileContent = fileContent & "Priority: 1" & vbCrLf
    ElseIf pMaxSeverityScore >= 2 Then
        fileContent = fileContent & "Priority: 3" & vbCrLf
    Else
        fileContent = fileContent & "Priority: 5" & vbCrLf
    End If
    
    fileContent = fileContent & "Ticket: " & pNumber & vbCrLf
    fileContent = fileContent & String(80, "=") & vbCrLf
    fileContent = fileContent & pHeader & vbCrLf
    
    fileContent = fileContent & vbCrLf & "QID:" & vbCrLf
    For Each Key In pQidsDict.Keys
        fileContent = fileContent & "  " & Key & " " & pQidsDict(Key) & vbCrLf
    Next Key
    
    fileContent = fileContent & vbCrLf & "TARGETS:" & vbCrLf
    For Each Key In pTargetsDict.Keys
        If StrComp(pTargetsDict(Key), "()", 1) = 0 Or StrComp(pTargetsDict(Key), "(No registered hostname)", 1) = 0 Then
            fileContent = fileContent & "  " & Key & vbCrLf
        Else
            fileContent = fileContent & "  " & Key & " " & pTargetsDict(Key) & vbCrLf
        End If
    Next Key
    
    If pResultsDict.Count > 0 Then
        fileContent = fileContent & vbCrLf & "RESULTS:" & vbCrLf
        For Each Key In pResultsDict.Keys
            If pResultsDict.Count > 1 Then
                ReDim items(pResultsDict(Key).Count - 1)
                For i = 1 To pResultsDict(Key).Count
                     items(i - 1) = pResultsDict(Key)(i)
                Next i
                fileContent = fileContent & "  " & Join(items, ", ") & vbCrLf
            End If
            fileContent = fileContent & Key & vbCrLf & vbCrLf
        Next Key
    End If
    
    If pThreatsDict.Count > 0 Then
        fileContent = fileContent & vbCrLf & "THREATS:" & vbCrLf
        For Each Key In pThreatsDict.Keys
            If pThreatsDict.Count > 1 Then
                ReDim items(pThreatsDict(Key).Count - 1)
                For i = 1 To pThreatsDict(Key).Count
                     items(i - 1) = pThreatsDict(Key)(i)
                Next i
                fileContent = fileContent & "  " & Join(items, ", ") & vbCrLf
            End If
            fileContent = fileContent & Key & vbCrLf & vbCrLf
        Next Key
    End If
    
    If pImpactsDict.Count > 0 Then
        fileContent = fileContent & vbCrLf & "IMPACTS:" & vbCrLf
        For Each Key In pImpactsDict.Keys
            If pImpactsDict.Count > 1 Then
                ReDim items(pImpactsDict(Key).Count - 1)
                For i = 1 To pImpactsDict(Key).Count
                     items(i - 1) = pImpactsDict(Key)(i)
                Next i
                fileContent = fileContent & "  " & Join(items, ", ") & vbCrLf
            End If
            fileContent = fileContent & Key & vbCrLf & vbCrLf
        Next Key
    End If
    
    If pSolutionsDict.Count > 0 Then
        fileContent = fileContent & vbCrLf & "SOLUTIONS:" & vbCrLf
        For Each Key In pSolutionsDict.Keys
            If pSolutionsDict.Count > 1 Then
                ReDim items(pSolutionsDict(Key).Count - 1)
                For i = 1 To pSolutionsDict(Key).Count
                     items(i - 1) = pSolutionsDict(Key)(i)
                Next i
                fileContent = fileContent & "  " & Join(items, ", ") & vbCrLf
            End If
            fileContent = fileContent & Key & vbCrLf & vbCrLf
        Next Key
    End If
    
    If pCveDict.Count > 0 Then
        fileContent = fileContent & vbCrLf & "CVES:" & vbCrLf
        For Each Key In pCveDict.Keys
            fileContent = fileContent & "    " & Key & vbCrLf ' & " (CVSS3:" & pCveDict(key) & ")" & vbCrLf
        Next Key
    End If
    
    fileContent = fileContent & vbCrLf & pFooter
        
    ' Créer un nom de fichier basé sur le titre avec les espaces remplacés par "_"
    FileName = pTitle
    ' Remplacer les espaces par des underscores
    FileName = Replace(FileName, " ", "_")
    ' Supprimer les caractères non valides pour les noms de fichiers
    FileName = CleanFileName(FileName)
    FileName = FileName & "_" & pNumber & "_" & Format(Date, "yyyymmdd") & ".txt"
    ' Sauvegarde du ticket Staging avec le numéro de ticket inclus dans le nom de fichier
    FilePath = Application.GetSaveAsFilename(FileName, "Text Files (*.txt), *.txt")
    If filePathStaging <> "False" Then
        Dim fso As Object, F As Object
        Set fso = CreateObject("Scripting.FileSystemObject")
        Set F = fso.CreateTextFile(FilePath, True)
        F.Write fileContent
        F.Close
        
        Debug.Print "Ticket généré avec succès : " & filePathStaging, vbInformation
    End If
    Exit Sub
    
ErrorHandler:
    Debug.Print "Erreur lors de l'exportation du fichier: " & Err.Description, vbCritical
    ' Fermer le fichier s'il est ouvert
    On Error Resume Next
    Close fileNum
End Sub

' Fonction auxiliaire pour nettoyer le nom de fichier
Private Function CleanFileName(ByVal FileName As String) As String
    Dim invalidChars As String
    Dim i As Integer
    Dim char As String
    
    ' Liste des caractères invalides dans un nom de fichier Windows
    invalidChars = "\/:<>*?|"""
    
    ' Remplacer chaque caractère invalide
    For i = 1 To Len(invalidChars)
        char = Mid(invalidChars, i, 1)
        FileName = Replace(FileName, char, "_")
    Next i
    
    ' Limiter la longueur du nom de fichier (pour éviter les problèmes de chemin trop long)
    If Len(FileName) > 100 Then
        FileName = Left(FileName, 100)
    End If
    
    CleanFileName = FileName
End Function
