with open(r"c:\Users\ianache\Desktop\DATA\01-DOCUMENTOS\02-PROYECTOS\102-concesionarias\dashboardstudio\dashboard-app\src\components\editor\FlowEditorCanvas.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "nodes.value.push" in line or "push(" in line:
        if "node" in line.lower():
            safe_line = line.strip().encode('ascii', errors='replace').decode('ascii')
            print(f"{i+1}: {safe_line}")
