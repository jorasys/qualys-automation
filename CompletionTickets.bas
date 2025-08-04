Attribute VB_Name = "CompletionTickets"
Sub CompleterTickets()
    Dim wsMain As Worksheet
    Dim wsTickets As Worksheet
    Dim lastRowMain As Long
    Dim lastRowTickets As Long
    Dim i As Long, j As Long
    Dim foundMatch As Boolean
    Dim ipArray() As String
    Dim qidArray() As String
    Dim k As Long, m As Long
    Dim currentIP As String
    Dim currentQID As String
    
    ' Définir les feuilles de travail
    Set wsMain = ActiveSheet ' Feuille principale active
    Set wsTickets = Worksheets("TICKETS") ' Feuille TICKETS
    
    ' Déterminer la dernière ligne de chaque feuille
    lastRowMain = wsMain.Cells(wsMain.Rows.Count, "D").End(xlUp).Row
    lastRowTickets = wsTickets.Cells(wsTickets.Rows.Count, "E").End(xlUp).Row
    
    Application.ScreenUpdating = False ' Désactiver la mise à jour de l'écran pour améliorer les performances
    
    ' Parcourir chaque ligne de la feuille principale
    For i = 2 To lastRowMain ' Commencer à la ligne 2 en supposant que la ligne 1 est un en-tête
        foundMatch = False
        
        ' Vérifier si la ligne est masquée
        If wsMain.Rows(i).Hidden Then
            GoTo NextMainRow
        End If
        
        ' Vérifier si la cellule B contient déjà une valeur
        If Not IsEmpty(wsMain.Cells(i, "B").value) Then
            ' Si la cellule B contient déjà une valeur, passer à la ligne suivante
            GoTo NextMainRow
        End If
        
        ' Récupérer l'adresse IP et le QID de la ligne actuelle
        currentIP = Trim(wsMain.Cells(i, "D").value)
        currentQID = Trim(wsMain.Cells(i, "J").value)
        
        ' Vérifier que les valeurs ne sont pas vides
        If currentIP = "" Or currentQID = "" Then
            GoTo NextMainRow
        End If
        
        ' Parcourir chaque ligne de la feuille TICKETS pour trouver une correspondance
        For j = 2 To lastRowTickets ' Commencer à la ligne 2 en supposant que la ligne 1 est un en-tête
            ' Récupérer les données de la feuille TICKETS
            Dim ticketIPs As String
            Dim ticketQIDs As String
            
            ticketIPs = wsTickets.Cells(j, "E").value
            ticketQIDs = wsTickets.Cells(j, "D").value
            
            ' Vérifier que les valeurs ne sont pas vides
            If ticketIPs = "" Or ticketQIDs = "" Then
                GoTo NextTicketRow
            End If
            
            ' Récupérer et diviser les adresses IP de la feuille TICKETS
'            Dim tempTicketIPs As String
'            tempTicketIPs = Replace(ticketIPs, ":", ",")
            ipArray = Split(ticketIPs, ",")

            ' Récupérer et diviser les QID de la feuille TICKETS
            qidArray = Split(ticketQIDs, ",")
            
            ' Vérifier chaque combinaison d'IP et de QID
            For k = 0 To UBound(ipArray)
                Dim trimmedIP As String
                trimmedIP = Trim(ipArray(k))
'                Debug.Print trimmedIP
                For m = 0 To UBound(qidArray)
                    Dim trimmedQID As String
                    trimmedQID = Trim(qidArray(m))
                    
'                    Debug.Print "Comparing: IP=" & trimmedIP & " vs " & currentIP & ", QID=" & trimmedQID & " vs " & currentQID & ", " & (StrComp(trimmedQID, currentQID, 1) = 0)
'                    Debug.Print InStr("192.168.202.25", "192.168.202.25:5031/tcp")
                    If (InStr(trimmedIP, currentIP) > 0 Or InStr(currentIP, trimmedIP) > 0) And StrComp(trimmedQID, Trim(currentQID), 1) = 0 Then
                        Debug.Print "Comparing: IP=" & trimmedIP & " vs " & currentIP & ", QID=" & trimmedQID & " vs " & currentQID
                        ' Correspondance trouvée, copier le numéro de ticket dans la colonne B
                        wsMain.Cells(i, "B").value = wsTickets.Cells(j, "A").value
                        foundMatch = True
                        Exit For ' Sortir de la boucle une fois la correspondance trouvée
                    End If
                Next m
                
                If foundMatch Then Exit For
            Next k
            
            If foundMatch Then Exit For ' Sortir de la boucle principale si une correspondance est trouvée
NextTicketRow:
        Next j
        
        ' Pas d'action si aucune correspondance n'est trouvée
NextMainRow:
    Next i
    
    Application.ScreenUpdating = True ' Réactiver la mise à jour de l'écran
    
    MsgBox "Remplissage des numéros de ticket terminé!", vbInformation
End Sub
