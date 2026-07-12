import os
import importlib
import sys

# Add path
sys.path.extend([
    r"c:\Users\cacquoc\Downloads\dcm",
    r"c:\Users\cacquoc\Downloads\dcm\modules",
    r"c:\Users\cacquoc\Downloads\dcm\modules\auto",
    r"c:\Users\cacquoc\Downloads\dcm\modules\noprefix"
])

MODULES_DIR = r"c:\Users\cacquoc\Downloads\dcm\modules"
NOPREFIX_MODULES_DIR = r"c:\Users\cacquoc\Downloads\dcm\modules\noprefix"
AUTO_MODULES_DIR = r"c:\Users\cacquoc\Downloads\dcm\modules\auto"

def test_load(module_path, attribute_name, required_keys):
    success_modules, failed_modules = [], []
    for filename in os.listdir(module_path):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            try:
                # Mock import
                rel_path = module_path.replace(r"c:\Users\cacquoc\Downloads\dcm\\", "").replace(r"c:\Users\cacquoc\Downloads\dcm", "").strip(r"\\/")
                import_name = f"{rel_path.replace('/', '.').replace('\\', '.')}.{module_name}".strip(".")
                module = importlib.import_module(import_name)
                
                if hasattr(module, attribute_name) and hasattr(module, 'des'):
                    des = getattr(module, 'des')
                    missing_keys = [key for key in required_keys if key not in des]
                    if not missing_keys:
                        cmds = getattr(module, attribute_name)()
                        success_modules.append((module_name, list(cmds.keys())))
                    else:
                        failed_modules.append((module_name, f"Missing keys in des: {missing_keys}"))
                else:
                    reasons = []
                    if not hasattr(module, attribute_name):
                        reasons.append(f"No {attribute_name}() function")
                    if not hasattr(module, 'des'):
                        reasons.append("No 'des' dict")
                    failed_modules.append((module_name, ", ".join(reasons)))
            except Exception as e:
                failed_modules.append((module_name, f"Import/Execution error: {e}"))
                
    return success_modules, failed_modules

print("--- TESTING MODULES ---")
success, failed = test_load(MODULES_DIR, 'PTA', ['version', 'credits', 'description', 'power'])
print(f"Loaded successfully: {len(success)}")
if failed:
    print(f"Failed to load ({len(failed)}):")
    for name, reason in failed:
        print(f"  - {name}: {reason}")

print("\n--- TESTING NOPREFIX MODULES ---")
success_np, failed_np = test_load(NOPREFIX_MODULES_DIR, 'PTA', ['version', 'credits', 'description'])
print(f"Loaded successfully: {len(success_np)}")
if failed_np:
    print(f"Failed to load ({len(failed_np)}):")
    for name, reason in failed_np:
        print(f"  - {name}: {reason}")
