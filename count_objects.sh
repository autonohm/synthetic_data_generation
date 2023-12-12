#!/bin/bash

# Verzeichnis mit den TXT-Dateien im YOLO-Label-Format
verzeichnis="Test_CPU/bbox_labels"

# Schleife über alle TXT-Dateien im Verzeichnis
for datei in $verzeichnis/*.txt; do
    echo "Verarbeite Datei: $datei"
    
    # Lesen und Zählen der Objekte in der aktuellen Datei
    while IFS=' ' read -r klasse rest; do
        # Erste Spalte enthält die Klasse des Objekts
        # Restliche Spalten (optional) könnten die Koordinaten usw. enthalten
        
        # Objekt zur Zählung hinzufügen
        ((objekte["$klasse"]++))
    done < "$datei"
done

# Ausgabe der Anzahl jedes Objekts
echo "Anzahl der Objekte:"
for klasse in "${!objekte[@]}"; do
    anzahl=${objekte["$klasse"]}
    echo "$klasse: $anzahl"
done
