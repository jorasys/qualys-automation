VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "FileManager"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
' Classe pour gérer la sélection de fichiers

Private selectedFiles As Collection

' Constructeur
Public Sub Initialize()
    Set selectedFiles = New Collection
End Sub

' Méthode pour sélectionner des fichiers CSV
Public Function SelectCSVFiles() As Boolean
    On Error GoTo ErrorHandler
    
    Dim fd As FileDialog
    Dim i As Long
    
    ' Vider la collection précédente
    Set selectedFiles = New Collection
    
    ' Créer la boîte de dialogue de sélection de fichiers
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    
    With fd
        .Title = "Sélectionner les fichiers CSV à importer"
        .Filters.Clear
        .Filters.Add "Fichiers CSV", "*.csv"
        .FilterIndex = 1
        .AllowMultiSelect = True
    End With
    
    ' Afficher la boîte de dialogue
    If fd.Show = -1 Then
        ' Ajouter les fichiers sélectionnés à la collection
        For i = 1 To fd.SelectedItems.Count
            selectedFiles.Add fd.SelectedItems(i)
        Next i
        SelectCSVFiles = True
    Else
        SelectCSVFiles = False
    End If
    
    Exit Function
    
ErrorHandler:
    SelectCSVFiles = False
    MsgBox "Erreur lors de la sélection des fichiers : " & Err.Description
End Function

' Propriété pour accéder aux fichiers sélectionnés
Public Property Get Files() As Collection
    Set Files = selectedFiles
End Property

' Méthode pour obtenir le nombre de fichiers sélectionnés
Public Function FileCount() As Long
    FileCount = selectedFiles.Count
End Function
