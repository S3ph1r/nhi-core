#!/usr/bin/env python3
"""
NHI CLI

Command-line interface for NHI-CORE operations.
Entry point for the 'nhi' command.

Usage:
    nhi backup status
    nhi backup enable
    nhi backup now
    nhi backup add <service>
    nhi backup list
    nhi service list
    nhi service register <name>
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path

# Resolve symlink and add NHI-CORE to path
# When run as symlink from /usr/local/bin/nhi, __file__ resolves to the target
script_path = Path(__file__).resolve()
nhi_core_path = script_path.parent.parent  # cli/nhi.py -> cli -> nhi-core

# Fallback to /opt/nhi-core if not found
if not (nhi_core_path / 'core').exists():
    nhi_core_path = Path('/opt/nhi-core')

sys.path.insert(0, str(nhi_core_path))

from core.backup import BackupManager, DependencyResolver


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=level
    )


def cmd_backup_status(args):
    """Show backup status."""
    manager = BackupManager()
    status = manager.status()
    
    print("\n" + "="*60)
    print("NHI Backup Status")
    print("="*60)
    
    # Enabled status
    enabled_icon = "✅" if status['enabled'] else "❌"
    print(f"\n{enabled_icon} Backup: {'ENABLED' if status['enabled'] else 'DISABLED'}")
    
    # Policy
    print(f"📋 Policy: {status['policy']}")
    
    # Storage
    storage = status['storage']
    if storage['configured']:
        print(f"💾 Storage: {storage['type']} (configured)")
    else:
        print(f"⚠️  Storage: Not configured")
    
    # Targets
    print(f"\n📦 Backup Targets ({status['target_count']}):")
    if status['targets']:
        for target in status['targets']:
            print(f"   • {target['name']} (LXC {target['vmid']}) - {target['reason']}")
    else:
        print("   No targets configured")
    
    # Schedule
    schedule = status.get('schedule', {})
    if schedule.get('enabled'):
        print(f"\n⏰ Schedule: {schedule.get('daily', 'Not set')}")
    else:
        print(f"\n⏰ Schedule: Disabled")
    
    # Last backup
    if status.get('last_backup'):
        print(f"📅 Last Backup: {status['last_backup']}")
    
    print()
    return 0


def cmd_backup_enable(args):
    """Enable backup with optional storage config."""
    manager = BackupManager()
    
    print("\n🔧 Enabling NHI Backup...")
    
    # Interactive setup if no args
    if not args.storage_type:
        print("\nStorage will be configured later via config.yaml or 'nhi backup config'")
        print("For now, backup is enabled with default policy 'core+infra'\n")
    
    manager.enable(
        storage_type=args.storage_type if hasattr(args, 'storage_type') else None,
        storage_path=args.storage_path if hasattr(args, 'storage_path') else None
    )
    
    print("✅ Backup enabled!")
    print("\nNext steps:")
    print("  1. Configure storage in /var/lib/nhi/config.yaml")
    print("  2. Add Proxmox storage ID to backup.storage.primary.proxmox_storage")
    print("  3. Run 'nhi backup status' to verify")
    print("  4. Run 'nhi backup now' to test")
    print()
    return 0


def cmd_backup_disable(args):
    """Disable backup."""
    manager = BackupManager()
    manager.disable()
    print("✅ Backup disabled")
    return 0


def cmd_backup_now(args):
    """Execute backup immediately."""
    manager = BackupManager()
    
    if not manager.is_enabled():
        print("❌ Backup is not enabled. Run 'nhi backup enable' first.")
        return 1
    
    print("\n🚀 Starting backup...")
    print("="*60)
    
    try:
        results = manager.backup_now(storage=args.storage if hasattr(args, 'storage') else None)
        
        if not results:
            print("⚠️  No targets to backup")
            return 0
        
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        
        print(f"\n{'='*60}")
        print(f"Backup Complete: {success_count} success, {fail_count} failed")
        print("="*60)
        
        for result in results:
            icon = "✅" if result.success else "❌"
            print(f"{icon} {result.name} (LXC {result.vmid}): {result.message}")
        
        print()
        return 0 if fail_count == 0 else 1
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return 1


def cmd_backup_add(args):
    """Add service to backup policy."""
    manager = BackupManager()
    
    if not manager.is_enabled():
        print("⚠️  Backup not enabled. Enabling now...")
        manager.enable()
    
    result = manager.add_service(args.service)
    
    print(f"\n✅ Added '{args.service}' to backup policy")
    
    if result['dependencies']:
        print(f"\n📦 Dependencies auto-included:")
        for dep in result['dependencies']:
            print(f"   • {dep}")
    
    print(f"\nTotal backup targets: {result['total_targets']}")
    print()
    return 0


def cmd_backup_remove(args):
    """Remove service from backup policy."""
    manager = BackupManager()
    
    if manager.remove_service(args.service):
        print(f"✅ Removed '{args.service}' from backup policy")
    else:
        print(f"⚠️  '{args.service}' was not in backup policy")
    
    return 0


def cmd_backup_list(args):
    """List available backups."""
    manager = BackupManager()
    
    backups = manager.list_backups()
    
    if not backups:
        print("No backups found")
        return 0
    
    print(f"\n📦 Available Backups ({len(backups)}):")
    print("="*60)
    
    for backup in backups:
        volid = backup.get('volid', '')
        size = backup.get('size', 0)
        size_gb = size / (1024**3) if size else 0
        
        print(f"  {volid}")
        print(f"    Size: {size_gb:.2f} GB | Created: {backup.get('ctime', 'unknown')}")
        print()
    
    return 0


def cmd_deps_show(args):
    """Show dependency graph."""
    resolver = DependencyResolver()
    resolver.print_graph()
    return 0


def cmd_deps_resolve(args):
    """Resolve dependencies for a service."""
    resolver = DependencyResolver()
    
    deps = resolver.resolve(args.service, include_optional=args.optional)
    
    print(f"\nDependencies for '{args.service}':")
    for dep in sorted(deps):
        marker = " (self)" if dep == args.service else ""
        print(f"  • {dep}{marker}")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='nhi',
        description='NHI-CORE Command Line Interface'
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backup commands
    backup_parser = subparsers.add_parser('backup', help='Backup management')
    backup_sub = backup_parser.add_subparsers(dest='subcommand')
    
    # backup status
    backup_sub.add_parser('status', help='Show backup status')
    
    # backup enable
    enable_parser = backup_sub.add_parser('enable', help='Enable backup')
    enable_parser.add_argument('--storage-type', help='Storage type (nfs, local, s3)')
    enable_parser.add_argument('--storage-path', help='Storage path/URL')
    
    # backup disable
    backup_sub.add_parser('disable', help='Disable backup')
    
    # backup now
    now_parser = backup_sub.add_parser('now', help='Execute backup immediately')
    now_parser.add_argument('--storage', help='Override storage ID')
    
    # backup add
    add_parser = backup_sub.add_parser('add', help='Add service to backup policy')
    add_parser.add_argument('service', help='Service name to add')
    
    # backup remove
    remove_parser = backup_sub.add_parser('remove', help='Remove service from backup policy')
    remove_parser.add_argument('service', help='Service name to remove')
    
    # backup list
    backup_sub.add_parser('list', help='List available backups')
    
    # Dependencies commands
    deps_parser = subparsers.add_parser('deps', help='Dependency management')
    deps_sub = deps_parser.add_subparsers(dest='subcommand')
    
    # deps show
    deps_sub.add_parser('show', help='Show dependency graph')
    
    # deps resolve
    resolve_parser = deps_sub.add_parser('resolve', help='Resolve service dependencies')
    resolve_parser.add_argument('service', help='Service to resolve')
    resolve_parser.add_argument('--optional', action='store_true', help='Include optional deps')

    # Design commands
    design_parser = subparsers.add_parser('design', help='Design System management')
    design_sub = design_parser.add_subparsers(dest='subcommand')
    
    # design list
    design_sub.add_parser('list', help='List available personalities')
    
    # design init
    init_parser = design_sub.add_parser('init', help='Initialize design system in current folder')
    init_parser.add_argument('--personality', help='Personality ID (flux, glass, nexus, forge)')
    
    # Parse args
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Route to command handlers
    if args.command == 'backup':
        handlers = {
            'status': cmd_backup_status,
            'enable': cmd_backup_enable,
            'disable': cmd_backup_disable,
            'now': cmd_backup_now,
            'add': cmd_backup_add,
            'remove': cmd_backup_remove,
            'list': cmd_backup_list,
        }
        handler = handlers.get(args.subcommand)
        if handler:
            return handler(args)
        else:
            backup_parser.print_help()
            return 0
    
    elif args.command == 'deps':
        handlers = {
            'show': cmd_deps_show,
            'resolve': cmd_deps_resolve,
        }
        handler = handlers.get(args.subcommand)
        if handler:
            return handler(args)
        else:
            deps_parser.print_help()
            return 0

    elif args.command == 'design':
        from core.design.manager import DesignSystemManager
        
        mgr = DesignSystemManager(core_path=str(nhi_core_path))
        
        if args.subcommand == 'list':
            print("\n🎨 NHI Design System Personalities")
            print("="*60)
            personalities = mgr.list_personalities()
            if not personalities:
                print("No personalities found.")
            for p in personalities:
                print(f"\n🔹 {p['name']} ({p['id']}) v{p['version']}")
                print(f"   {p['description']}")
            print()
            return 0
            
        elif args.subcommand == 'init':
            if not args.personality:
                print("❌ Please specify a personality with --personality <id>")
                print("Available: " + ", ".join([p['id'] for p in mgr.list_personalities()]))
                return 1
            
            target_path = Path(os.getcwd()) / "tailwind.config.js"
            print(f"\n⚙️  Initializing '{args.personality}' personality...")
            try:
                mgr.generate_tailwind_config(args.personality, str(target_path))
                print(f"✅ Generated tailwind.config.js")
                print(f"   Style: {args.personality}")
                print(f"   Location: {target_path}")
            except Exception as e:
                print(f"❌ Error: {e}")
                return 1
            return 0
        
        else:
            design_parser.print_help()
            return 0
    
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
