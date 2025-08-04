VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Data"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Private pIp As String
Private pDns As String
Private pQid As String
Private pSeverite As String
Private pTitle As String
Private pVulnType As String
Private pTypeFormate As String
Private pThreat As String
Private pImpact As String
Private pSolution As String
Private pResult As String
Private pPort As String
Private pProtocole As String ' Nouvelles variables pour port et protocole
Private pIsStaging As Boolean
Private pCve As String


Private Sub Class_Initialize()
    pIp = ""
    pDns = ""
    pQid = ""
    pTitle = ""
    pVulnType = ""
    pTypeFormate = ""
    pSeverite = ""
    pPort = ""
    pProtocole = ""
    pThreat = ""
    pImpact = ""
    pSolution = ""
    pResult = ""
    pIsStaging = False
    pCve = ""
End Sub

Public Sub Initialize(ByVal ligne As Range)
    pIp = ligne.Cells(1, 1).text
    pDns = ligne.Cells(1, 2).text
    pQid = ligne.Cells(1, 7).text
    pTitle = ligne.Cells(1, 8).text
    pVulnType = ligne.Cells(1, 10).text
    pSeverite = ligne.Cells(1, 11).text
    pPort = ligne.Cells(1, 12).text
    pProtocole = ligne.Cells(1, 13).text
    pCve = Trim(ligne.Cells(1, 20).text)
    pThreat = ligne.Cells(1, 23).text
    pImpact = ligne.Cells(1, 24).text
    pSolution = ligne.Cells(1, 25).text
    pResult = ligne.Cells(1, 27).text
    
    ' Déterminer si c'est Staging ou Production
    pIsStaging = False
    If Len(pDns) > 0 Then
        If Left(pDns, 1) = "s" Then
            If Left(pDns, 4) = "srvn" Then
            Else
                pIsStaging = True
            End If
        End If
    End If
    
    ' Conversion du type selon les correspondances demandées
    Select Case pVulnType
        Case "Vuln"
            pTypeFormate = "Confirmed"
        Case "Practice"
            pTypeFormate = "Potential"
        Case "IG"
            pTypeFormate = "Information"
        Case Else
            pTypeFormate = pVulnType
    End Select
    
End Sub
Public Property Get cve() As String
   cve = pCve
End Property

Public Property Let cve(ByVal vNewValue As String)
    pCve = vNewValue
End Property

Public Property Get qid() As String
    qid = pQid
End Property

Public Property Let qid(ByVal vNewValue As String)
    pQid = vNewValue
End Property
Public Property Get ip() As String
    ip = pIp
End Property

Public Property Let ip(ByVal vNewValue As String)
    pIp = vNewValue
End Property
Public Property Get Dns() As String
    Dns = pDns
End Property

Public Property Let Dns(ByVal vNewValue As String)
    pDns = vNewValue
End Property
Public Property Get Title() As String
    Title = pTitle
End Property

Public Property Let Title(ByVal vNewValue As String)
    pTitle = vNewValue
End Property
Public Property Get Severite() As String
    Severite = pSeverite
End Property

Public Property Let Severite(ByVal vNewValue As String)
    pSeverite = vNewValue
End Property
Public Property Get vulnType() As String
    vulnType = pVulnType
End Property

Public Property Let vulnType(ByVal vNewValue As String)
    pVulnType = vNewValue
End Property
Public Property Get Threat() As String
    Threat = pThreat
End Property

Public Property Let Threat(ByVal vNewValue As String)
    pThreat = vNewValue
End Property
Public Property Get Impact() As String
    Impact = pImpact
End Property

Public Property Let Impact(ByVal vNewValue As String)
    pImpact = vNewValue
End Property
Public Property Get Solution() As String
    Solution = pSolution
End Property

Public Property Let Solution(ByVal vNewValue As String)
    pSolution = vNewValue
End Property
Public Property Get Result() As String
    Result = pResult
End Property

Public Property Let Result(ByVal vNewValue As String)
    pResult = vNewValue
End Property
Public Property Get Port() As String
    Port = pPort
End Property

Public Property Let Port(ByVal vNewValue As String)
    pPort = vNewValue
End Property
Public Property Get Protocole() As String
    Protocole = pProtocole
End Property

Public Property Let Protocole(ByVal vNewValue As String)
    pProtocole = vNewValue
End Property
Public Property Get IsStaging() As Boolean
    IsStaging = pIsStaging
End Property

Public Property Let IsStaging(ByVal vNewValue As Boolean)
    pIsStaging = vNewValue
End Property
Public Property Get TypeFormate() As String
    TypeFormate = pTypeFormate
End Property

Public Property Let TypeFormate(ByVal vNewValue As String)
    pTypeFormate = vNewValue
End Property

Public Function Equals(obj As Data) As Boolean
    Equals = (Me.qid = obj.qid) And (Me.ip = obj.ip) And (Me.Port = obj.Port) And (Me.Protocole = obj.Protocole)
End Function

Public Function clone() As Data  ' Remplacez VotreNomDeClasse par le nom réel de votre classe
    ' Créer une nouvelle instance
    Dim copie As New Data
    
    ' Copier toutes les propriétés
    copie.ip = Me.ip
    copie.Dns = Me.Dns
    copie.qid = Me.qid
    copie.Title = Me.Title
    copie.vulnType = Me.vulnType
    copie.TypeFormate = Me.TypeFormate
    copie.Severite = Me.Severite
    copie.Port = Me.Port
    copie.Protocole = Me.Protocole
    copie.Threat = Me.Threat
    copie.Impact = Me.Impact
    copie.Solution = Me.Solution
    copie.Result = Me.Result
    copie.IsStaging = Me.IsStaging
    copie.cve = Me.cve
    
    ' Retourner la copie créée
    Set clone = copie
End Function

Public Sub Show(Optional ByVal showDetails As Boolean = False)
    Debug.Print "---- Data ----"
    Debug.Print "IP: " & Me.ip
'    Debug.Print "DNS: " & Me.Dns
    Debug.Print "QID: " & Me.qid
'    Debug.Print "Titre: " & Me.Title
'    Debug.Print "Type: " & Me.vulnType & " (" & Me.TypeFormate & ")"
    Debug.Print "Sévérité: " & Me.Severite
'    Debug.Print "Port/Protocole: " & Me.Port & "/" & Me.Protocole
    Debug.Print "Environnement: " & IIf(Me.IsStaging, "Staging", "Production")
    Debug.Print "---------------------------"
End Sub

Function CleanupLineBreaks(text As String) As String
    Dim Result As String
    Result = text
    Result = Replace(Result, vbCr, vbCrLf)
    Result = Replace(Result, vbLf, vbCrLf)
    
    Dim previousResult As String
    Do
        previousResult = Result
        Result = Replace(Result, vbCrLf & " " & vbCrLf, vbCrLf)
    Loop While previousResult <> Result
    
    Do While InStr(Result, vbCrLf & vbCrLf) > 0
        Result = Replace(Result, vbCrLf & vbCrLf, vbCrLf)
    Loop
'    Debug.Print result
    
    CleanupLineBreaks = Result
End Function
Function WrapTextWithIndent(text As String, Optional maxWidth As Long = 80, Optional indent As String = "    ") As String
    Dim Result As String
    Dim paragraphs() As String
    Dim allWords() As String
    Dim newLines As New Collection
    Dim currentLine As String
    Dim currentWord As String
    Dim i As Long, j As Long
    
    ' D'abord, diviser en paragraphes (séparés par des lignes vides)
    paragraphs = Split(text, vbCrLf)
    
    ' Traiter chaque paragraphe séparément
    For j = 0 To UBound(paragraphs)
        ' Nettoyer le paragraphe
        Dim cleanedText As String
        cleanedText = paragraphs(j)
        
        ' Remplacer tous les retours à la ligne simples par des espaces
        cleanedText = Replace(cleanedText, vbCrLf, " ")
        
        ' S'assurer qu'il n'y a pas d'espaces multiples
        Do While InStr(cleanedText, "  ") > 0
            cleanedText = Replace(cleanedText, "  ", " ")
        Loop
        
        ' Diviser en mots
        allWords = Split(cleanedText, " ")
        
        ' Calculer la largeur effective en tenant compte de l'indentation
        Dim effectiveWidth As Long
        effectiveWidth = maxWidth - Len(indent)
        
        ' Initialiser la première ligne du paragraphe avec l'indentation
        currentLine = indent
        
        ' Traiter chaque mot du paragraphe
        For i = 0 To UBound(allWords)
            currentWord = allWords(i)
            ' Vérifier si l'ajout du mot dépasserait la largeur effective
            If Len(currentLine) + Len(currentWord) > maxWidth Then
                ' La ligne serait trop longue, donc ajouter la ligne actuelle et en commencer une nouvelle
''                Debug.Print "->" & currentLine
                If currentLine = indent Then
'                    Debug.Print currentWord & "______" & currentLine
'                    currentLine = indent & currentWord
'                    newLines.Add currentLine
'                    currentLine = indent
                Else
                
                    newLines.Add currentLine
                    
                End If
                currentLine = indent & currentWord
            Else
                ' Ajouter le mot à la ligne actuelle
                If currentLine = indent Then
                    currentLine = currentLine & currentWord
                Else
                    currentLine = currentLine & " " & currentWord
                End If
            End If
        Next i
        
        ' Ajouter la dernière ligne du paragraphe
        If Len(currentLine) > Len(indent) Then
            newLines.Add currentLine
        End If
        
'         Ajouter une ligne vide entre les paragraphes (sauf pour le dernier)
'        If j < UBound(paragraphs) Then
 '           newLines.Add ""
'        End If
    Next j
    
    ' Combiner toutes les nouvelles lignes
    For i = 1 To newLines.Count
        If i < newLines.Count Then
            If newLines(i) = "" Then
                Result = Result & vbCrLf  ' Ligne vide
            Else
                Result = Result & newLines(i) & vbCrLf
            End If
        Else
            Result = Result & newLines(i)  ' Dernière ligne sans retour à la ligne
        End If
    Next i
    
    WrapTextWithIndent = Result
End Function
Public Sub Format()
    Me.Result = CleanupLineBreaks(Me.Result)
    Me.Result = WrapTextWithIndent(Me.Result)
    Me.Threat = CleanupLineBreaks(Me.Threat)
    Me.Threat = WrapTextWithIndent(Me.Threat)
    Me.Impact = CleanupLineBreaks(Me.Impact)
    Me.Impact = WrapTextWithIndent(Me.Impact)
    Me.Solution = CleanupLineBreaks(Me.Solution)
    Me.Solution = WrapTextWithIndent(Me.Solution)
End Sub
