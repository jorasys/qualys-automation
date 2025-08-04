Attribute VB_Name = "GenerationTickets"
Public Sub GenerationTickets()
    Dim ws As Worksheet
    Dim lastRow As Long
    
    ' Initialisation
    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, 4).End(xlUp).Row
    Dim stagingEnvData As New EnvData
    stagingEnvData.Name = "PREPROD"
    Dim prodEnvData As New EnvData
    prodEnvData.Name = "PROD"
    ' Parcourir les lignes visibles
    For Each ligne In ws.Range("D2:D" & lastRow).Rows
        If Not ligne.EntireRow.Hidden Then
            Dim dataInstance As New Data
            dataInstance.Initialize (ligne)
            dataInstance.Format
            If dataInstance.IsStaging Then
                stagingEnvData.AddData dataInstance
            Else
                prodEnvData.AddData dataInstance
            End If
        End If
    Next
    If stagingEnvData.Count > 0 Then
        Dim stagingTicket As New Ticket
        stagingTicket.Initialize stagingEnvData
        stagingTicket.AjouterLigneTicket
        stagingTicket.Export
    End If
    If prodEnvData.Count > 0 Then
        Dim prodTicket As New Ticket
        prodTicket.Initialize prodEnvData
        prodTicket.AjouterLigneTicket
        prodTicket.Export
    End If
   
End Sub
