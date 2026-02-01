
import yaml
import os

CONFIG_PATH = '/var/lib/nhi/config.yaml'

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f) or {}
    
    changed = False
    if 'backup' not in config:
        print("Adding backup section...")
        config['backup'] = {
            'enabled': False,
            'storage': {
                'primary': {'type': None},
                'offsite': {'type': None, 'encrypt': True}
            },
            'policy': {
                'mode': 'core+infra',
                'include': [],
                'exclude': []
            },
            'schedule': {
                'enabled': False,
                'daily': '03:00'
            }
        }
        changed = True
    
    if changed:
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print("Config updated successfully.")
    else:
        print("Config already has backup section.")
else:
    print(f"Config file not found at {CONFIG_PATH}")
