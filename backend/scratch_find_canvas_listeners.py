with open(r"c:\Users\ianache\Desktop\DATA\01-DOCUMENTOS\02-PROYECTOS\102-concesionarias\dashboardstudio\dashboard-app\src\views\FlowEditorView.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "isdirty" in line.lower() or "canvasRef" in line or "@" in line:
        safe_line = line.strip().encode('ascii', errors='replace').decode('ascii')
        print(f"{i+1}: {safe_line}")
