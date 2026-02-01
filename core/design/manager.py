"""
Design System Manager

Manages personalities, tokens, and frontend scaffolding configurations.
"""

import os
import yaml
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DesignSystemManager:
    """
    Manages NHI Design System (NHIDS).
    Handles personality loading and configuration generation.
    """
    
    def __init__(self, core_path: str = "/opt/nhi-core"):
        self.core_path = Path(core_path)
        self.design_path = self.core_path / "core" / "design"
        self.personalities_path = self.design_path / "personalities"
        self.core_tokens_path = self.design_path / "core" / "tokens.yaml"
    
    def list_personalities(self) -> List[Dict]:
        """List available design personalities."""
        personalities = []
        
        if not self.personalities_path.exists():
            return []
            
        for p_dir in self.personalities_path.iterdir():
            if p_dir.is_dir():
                manifest = p_dir / "manifest.yaml"
                if manifest.exists():
                    try:
                        with open(manifest, 'r') as f:
                            data = yaml.safe_load(f)
                            personalities.append(data.get('meta', {}))
                    except Exception as e:
                        logger.warning(f"Failed to load personality {p_dir.name}: {e}")
                        
        return personalities

    def get_personality(self, personality_id: str) -> Dict:
        """Get full definition of a personality."""
        manifest = self.personalities_path / personality_id / "manifest.yaml"
        if not manifest.exists():
            raise ValueError(f"Personality '{personality_id}' not found")
            
        with open(manifest, 'r') as f:
            return yaml.safe_load(f)

    def get_core_tokens(self) -> Dict:
        """Load core universal tokens."""
        if not self.core_tokens_path.exists():
            return {}
        with open(self.core_tokens_path, 'r') as f:
            return yaml.safe_load(f)

    def generate_tailwind_config(self, personality_id: str, output_path: str) -> None:
        """
        Generate tailwind.config.js for a specific personality.
        Merges core tokens with personality specifics.
        """
        personality = self.get_personality(personality_id)
        core_tokens = self.get_core_tokens()
        
        # Prepare the JS content logic
        # In a real implementation, we would deeply merge dictionaries.
        # Here we generate a simplistic mapping for the specific personality.
        
        colors = personality.get('colors', {})
        fonts = personality.get('typography', {})
        
        config_content = f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: ['./src/**/*.{{html,js,svelte,ts}}'],
  theme: {{
    extend: {{
      colors: {{
        // Base
        background: '{colors.get('base', {}).get('background')}',
        surface: '{colors.get('base', {}).get('surface')}',
        border: '{colors.get('base', {}).get('border')}',
        
        // Text
        'text-primary': '{colors.get('text', {}).get('primary')}',
        'text-secondary': '{colors.get('text', {}).get('secondary')}',
        
        // Brand
        primary: '{colors.get('accent', {}).get('primary')}',
        secondary: '{colors.get('accent', {}).get('secondary', '')}',
      }},
      fontFamily: {{
        sans: [{fonts.get('font-family', 'sans-serif')}],
        display: [{fonts.get('display-font', fonts.get('font-family', 'sans-serif'))}],
      }},
      boxShadow: {{
        // Personality specific shadows
        {''.join([f"'{k}': '{v}'," for k,v in personality.get('effects', {}).get('shadows', {}).items()])}
      }},
      borderRadius: {{
         // Personality specific radius
         {''.join([f"'{k.replace('radius-', '')}': '{v}'," for k,v in personality.get('effects', {}).get('borders', {}).items() if 'radius-' in k])}
      }}
    }},
    // Core Spacing (Injected from Core)
    spacing: {{
      {','.join([f"'{k}': '{v}'" for k,v in core_tokens.get('spacing', {}).get('scale', {}).items()])}
    }},
    screens: {{
      {','.join([f"'{k}': '{v}'" for k,v in core_tokens.get('breakpoints', {}).items()])}
    }}
  }},
  plugins: [],
}}
"""
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            f.write(config_content)
            
        logger.info(f"Generated tailwind.config.js for {personality_id} at {output_path}")

if __name__ == "__main__":
    # Test
    mgr = DesignSystemManager()
    print("Available Personalities:")
    for p in mgr.list_personalities():
        print(f"- {p['id']}: {p['name']}")
