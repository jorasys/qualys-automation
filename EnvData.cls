VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "EnvData"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
' Classe EnvData
' Cette classe contient une collection d'objets data
Option Explicit

Private pName As String  ' Nom de l'environnement
Private pDataList As Collection  ' Collection d'objets data

' Initialisation de la classe
Private Sub Class_Initialize()
    pName = ""
    Set pDataList = New Collection
End Sub

' Libération des ressources à la destruction
Private Sub Class_Terminate()
    Set pDataList = Nothing
End Sub

' Propriété Name
Public Property Get Name() As String
    Name = pName
End Property

Public Property Let Name(ByVal vNewValue As String)
    pName = vNewValue
End Property


' Retourne la collection complète d'objets data
Public Property Get DataList() As Collection
    Set DataList = pDataList
End Property

' Ajoute un objet data à la collection
Public Sub AddData(dataObj As Data)
    If Not Me.Contains(dataObj) Then
        pDataList.Add dataObj.clone
    End If
End Sub

' Supprime un objet data de la collection par son index
Public Sub RemoveDataByIndex(index As Long)
    If index > 0 And index <= pDataList.Count Then
        pDataList.Remove index
    End If
End Sub

' Supprime un objet data de la collection qui correspond à certains critères (par exemple IP et QID)
Public Sub RemoveDataByValue(ip As String, qid As String)
    Dim i As Long
    Dim dataObj As Data
    
    For i = pDataList.Count To 1 Step -1
        Set dataObj = pDataList(i)
        If CStr(dataObj.ip) = ip And CStr(dataObj.qid) = qid Then
            pDataList.Remove i
            Exit Sub
        End If
    Next i
End Sub

' Recherche un objet data par IP et QID
Public Function FindData(ip As String, qid As String) As Data
    Dim dataObj As Data
    Dim i As Long
    
    For i = 1 To pDataList.Count
        Set dataObj = pDataList(i)
        If CStr(dataObj.ip) = ip And CStr(dataObj.qid) = qid Then
            Set FindData = dataObj
            Exit Function
        End If
    Next i
    
    ' Si aucun objet correspondant n'est trouvé, retourne Nothing
    Set FindData = Nothing
End Function

' Retourne le nombre d'objets data dans la collection
Public Function Count() As Long
    Count = pDataList.Count
End Function

' Vérifie si un objet data existe déjà dans la collection
Public Function Contains(dataObj As Data) As Boolean
    Dim existingObj As Data
    Dim i As Long
    
    For i = 1 To pDataList.Count
        Set existingObj = pDataList(i)
        ' Utiliser correctement la méthode Equals de l'objet existingObj
        ' dataObj.Show
        ' existingObj.Show
        
        If existingObj.Equals(dataObj) Then
            Contains = True
            Exit Function
        End If
    Next i
    
    Contains = False
End Function

' Crée un clone de l'environnement avec tous ses objets data
Public Function clone() As EnvData
    Dim clone As New EnvData
    Dim dataObj As Data
    Dim i As Long
    
    ' Copier le nom
    clone.Name = Me.Name
    
    ' Copier tous les objets data
    For i = 1 To pDataList.Count
        Set dataObj = pDataList(i)
        clone.AddData dataObj.clone()
    Next i
    
    Set clone = clone
End Function

' Méthode pour fusionner avec un autre environnement
' Ajoute tous les objets data de l'autre environnement s'ils n'existent pas déjà
Public Sub MergeWith(otherEnv As EnvData)
    Dim dataObj As Data
    Dim i As Long
    
    For i = 1 To otherEnv.Count
        Set dataObj = otherEnv.DataList(i)
        If Not Me.Contains(dataObj) Then
            Me.AddData dataObj.clone()
        End If
    Next i
End Sub

' Méthode pour obtenir tous les objets data de sévérité spécifique
Public Function GetDataBySeverity(severity As String) As Collection
    Dim Result As New Collection
    Dim dataObj As Data
    Dim i As Long
    
    For i = 1 To pDataList.Count
        Set dataObj = pDataList(i)
        If CStr(dataObj.Severite) = severity Then
            Result.Add dataObj
        End If
    Next i
    
    Set GetDataBySeverity = Result
End Function

' Méthode pour obtenir tous les objets data d'un type spécifique
Public Function GetDataByType(vulnType As String) As Collection
    Dim Result As New Collection
    Dim dataObj As Data
    Dim i As Long
    
    For i = 1 To pDataList.Count
        Set dataObj = pDataList(i)
        If CStr(dataObj.vulnType) = vulnType Then
            Result.Add dataObj
        End If
    Next i
    
    Set GetDataByType = Result
End Function

' Méthode pour obtenir un objet data par son index
Public Function GetDataByIndex(index As Long) As Data
    If index > 0 And index <= pDataList.Count Then
        Set GetDataByIndex = pDataList(index)
    Else
        Set GetDataByIndex = Nothing
    End If
End Function

' Méthode pour vider la collection
Public Sub Clear()
    Set pDataList = New Collection
End Sub

' Méthode pour trier les objets data par une propriété spécifique
' Cette méthode est plus complexe car VBA ne fournit pas de méthode de tri native pour les collections
' Pour l'instant, nous retournons juste une collection triée sans modifier la collection originale
Public Function SortBy(propertyName As String, ascending As Boolean) As Collection
    ' Implémentation simplifiée - pour un tri plus efficace,
    ' vous pourriez utiliser un algorithme de tri comme QuickSort
    Dim Result As New Collection
    Dim tempArray() As Variant
    Dim i As Long, j As Long
    Dim temp As Variant
    
    ' Ne rien faire si la collection est vide
    If pDataList.Count = 0 Then
        Set SortBy = Result
        Exit Function
    End If
    
    ' Créer un tableau temporaire pour le tri
    ReDim tempArray(1 To pDataList.Count, 1 To 2)
    
    ' Remplir le tableau avec les valeurs à trier et la référence à l'objet
    For i = 1 To pDataList.Count
        Set tempArray(i, 1) = pDataList(i)
        
        ' Obtenir la valeur de la propriété
        Select Case LCase(propertyName)
            Case "ip"
                tempArray(i, 2) = pDataList(i).ip
            Case "qid"
                tempArray(i, 2) = pDataList(i).qid
            Case "severite"
                tempArray(i, 2) = pDataList(i).Severite
            Case "vulntype"
                tempArray(i, 2) = pDataList(i).vulnType
            Case Else
                tempArray(i, 2) = "" ' Propriété non reconnue
        End Select
    Next i
    
    ' Trier le tableau (tri à bulles simple pour démonstration)
    For i = 1 To UBound(tempArray, 1) - 1
        For j = i + 1 To UBound(tempArray, 1)
            If (ascending And tempArray(i, 2) > tempArray(j, 2)) Or _
               (Not ascending And tempArray(i, 2) < tempArray(j, 2)) Then
                ' Échanger les valeurs
                temp = tempArray(i, 2)
                tempArray(i, 2) = tempArray(j, 2)
                tempArray(j, 2) = temp
                
                ' Échanger les références
                Set temp = tempArray(i, 1)
                Set tempArray(i, 1) = tempArray(j, 1)
                Set tempArray(j, 1) = temp
            End If
        Next j
    Next i
    
    ' Créer la collection résultante
    For i = 1 To UBound(tempArray, 1)
        Result.Add tempArray(i, 1)
    Next i
    
    Set SortBy = Result
End Function

' À ajouter dans votre classe envdata
Public Sub Show(Optional ByVal showDetails As Boolean = False)
    Debug.Print "==== Environment Data Summary ===="
    Debug.Print Me.Name
    Debug.Print "Nombre total de vulnérabilités: " & pDataList.Count
    
    ' Afficher des statistiques si nécessaire
    Dim staging As Integer, production As Integer
    Dim i As Integer, d As Data
    
    For i = 1 To pDataList.Count
        Set d = pDataList(i)
        If d.IsStaging Then
            staging = staging + 1
        Else
            production = production + 1
        End If
    Next i
    
'    Debug.Print "Vulnérabilités en Staging: " & staging
'    Debug.Print "Vulnérabilités en Production: " & production
'    Debug.Print "=================================="
    If showDetails Then
        ' Option: Afficher tous les éléments (décommenter si nécessaire)
        For i = 1 To pDataList.Count
            Set d = pDataList(i)
            d.Show
        Next i
    End If
End Sub
