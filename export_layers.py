# -*- coding: utf-8 -*-
"""
Выгружает все векторные слои из QGIS-проекта в GeoJSON.
Запускается через python-qgis.bat, который идёт с QGIS.
"""

import os
import sys

# --- Пути (поправь под себя при необходимости) ---
PROJECT_PATH = r"C:\Users\user\Desktop\СхемаФермыQGIS\Единая_схема_фермы.qgz"
OUT_DIR      = r"C:\Users\user\Desktop\farm-map\data"

# Слои, которые НЕ нужно выгружать (подложки, декор)
SKIP_NAMES = ["Общий фон", "План фермы", "подложка"]

# --- Настройка QGIS ---
QGIS_PREFIX = r"C:\Program Files\QGIS 4.2.3\apps\qgis"
os.environ["QGIS_PREFIX_PATH"] = QGIS_PREFIX
sys.path.insert(0, os.path.join(QGIS_PREFIX, "python"))

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem
)

QgsApplication.setPrefixPath(QGIS_PREFIX, True)
qgs = QgsApplication([], False)
qgs.initQgis()

try:
    project = QgsProject.instance()
    if not project.read(PROJECT_PATH):
        print("НЕ УДАЛОСЬ открыть проект:", PROJECT_PATH)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    exported = 0
    for layer in project.mapLayers().values():
        if not isinstance(layer, QgsVectorLayer):
            continue
        name = layer.name()
        if any(skip.lower() in name.lower() for skip in SKIP_NAMES):
            continue

        safe_name = "".join(
            c if c.isalnum() or c in "_-" else "_" for c in name
        )
        out_path = os.path.join(OUT_DIR, safe_name + ".geojson")

        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = "GeoJSON"
        opts.fileEncoding = "UTF-8"
        opts.layerOptions = ["COORDINATE_PRECISION=8"]

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            out_path,
            project.transformContext(),
            opts
        )

        code = result[0] if isinstance(result, tuple) else result
        if code == QgsVectorFileWriter.NoError:
            print(f"OK: {name} -> {safe_name}.geojson")
            exported += 1
        else:
            print(f"ОШИБКА: {name} -> код {code}")

    print(f"\nВсего выгружено слоёв: {exported}")

finally:
    qgs.exitQgis()