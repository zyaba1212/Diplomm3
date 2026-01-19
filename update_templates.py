import os

templates_dir = 'templates'
i18n_load = '{% load i18n %}\n'

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Добавляем {% load i18n %} после extends если его нет
            if '{% load i18n %}' not in content:
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if line.strip().startswith('{% extends'):
                        new_lines.append(i18n_load)
                
                new_content = '\n'.join(new_lines)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated: {filepath}")