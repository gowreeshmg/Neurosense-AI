import sys

try:
    with open('c:/Users/HP/Desktop/Mental health - Copy/NeuroSense_AI/frontend/index.html', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    lines = html.split('\n')
    
    start_idx = 0
    end_idx = len(lines)
    for i, line in enumerate(lines):
        if 'id="viewCheckin"' in line:
            start_idx = i
        if 'id="viewCBT"' in line:
            end_idx = i
            break
            
    for i in range(start_idx, end_idx):
        line = lines[i]
        if '<div id=' in line or '<div class=' in line:
            if 'style=' in line:
                line = line.split('style=')[0] + '>'
            print(f'{i+1}: {line.strip()}')
            
except Exception as e:
    print(e)
