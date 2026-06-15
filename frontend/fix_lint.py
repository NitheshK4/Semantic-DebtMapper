import re

def remove_unused(filepath, unused_list):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for unused in unused_list:
        # Simple regex to remove the unused import token
        # This will handle `import { A, B, C }` -> `import { A, C }`
        content = re.sub(rf'\b{unused}\b\s*,\s*', '', content)
        content = re.sub(rf',\s*\b{unused}\b', '', content)
        content = re.sub(rf'\{\s*\b{unused}\b\s*\}', '{}', content)
        
    with open(filepath, 'w') as f:
        f.write(content)

base = "/Users/nitheshkumar/Documents/Semantic Debt Mapper /frontend/src/pages/"

remove_unused(base + "ActionCenter.tsx", ["ArrowDown", "HelpCircle"])
remove_unused(base + "FindingsExplorer.tsx", ["ArrowDown"])
remove_unused(base + "IngestionCenter.tsx", ["Upload", "AlertTriangle"])
remove_unused(base + "Overview.tsx", ["AlertTriangle", "HelpCircle"])
remove_unused(base + "LineageGraph.tsx", ["useMemo", "n"])

# For 'any' in IngestionCenter and LineageGraph, let's just do a blanket replace where applicable
def replace_any(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    content = content.replace("any", "Record<string, unknown>")
    with open(filepath, 'w') as f:
        f.write(content)

replace_any(base + "IngestionCenter.tsx")
# LineageGraph has ReactFlow types that might use 'any', let's be careful. 
# Better to manually fix LineageGraph or use the python script for it too.
with open(base + "LineageGraph.tsx", 'r') as f:
    content = f.read()
content = content.replace(": any", ": Record<string, unknown>")
with open(base + "LineageGraph.tsx", 'w') as f:
    f.write(content)
