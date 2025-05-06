import time
import os
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            try:
                # Get file path and name
                file_path = event.src_path
                filename = os.path.basename(file_path)
                
                # Create backup name with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{filename}_{timestamp}"
                
                # Create backups directory if it doesn't exist
                backup_dir = "backups"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Create backup
                backup_path = os.path.join(backup_dir, backup_name)
                shutil.copy2(file_path, backup_path)
                
                print(f"Change detected! Backup created: {backup_name}")
            
            except Exception as e:
                print(f"Error creating backup: {str(e)}")

def start_monitoring(path="."):
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    print(f"Started monitoring directory: {os.path.abspath(path)}")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nMonitoring stopped!")
    
    observer.join()

if __name__ == "__main__":
    start_monitoring()































import time
import os
import shutil
import json
import hashlib
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AutoSaveConfig:
    def __init__(self):
        self.config_file = "autosave_config.json"
        self.load_config()

    def load_config(self):
        default_config = {
            "ignore_patterns": [".git/*", "*.pyc", "__pycache__/*", "backups/*"],
            "backup_dir": "backups",
            "max_backups_per_file": 5,
            "min_time_between_saves": 5  # seconds
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

class AdvancedChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.config = AutoSaveConfig()
        self.last_save_times = {}
        self.file_hashes = {}

    def should_ignore(self, path):
        from fnmatch import fnmatch
        return any(fnmatch(path, pattern) for pattern in self.config.config["ignore_patterns"])

    def get_file_hash(self, file_path):
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def cleanup_old_backups(self, file_path):
        backup_dir = self.config.config["backup_dir"]
        filename = os.path.basename(file_path)
        backups = []
        
        # Get all backups for this file
        for f in os.listdir(backup_dir):
            if f.startswith(filename + "_"):
                backups.append(os.path.join(backup_dir, f))
        
        # Remove oldest backups if exceeding max limit
        max_backups = self.config.config["max_backups_per_file"]
        if len(backups) > max_backups:
            backups.sort(key=lambda x: os.path.getctime(x))
            for backup in backups[:-max_backups]:
                os.remove(backup)

    def on_modified(self, event):
        if event.is_directory or self.should_ignore(event.src_path):
            return

        try:
            file_path = event.src_path
            current_time = time.time()
            
            # Check if enough time has passed since last save
            if (file_path in self.last_save_times and 
                current_time - self.last_save_times[file_path] < 
                self.config.config["min_time_between_saves"]):
                return

            # Check if file content has actually changed
            current_hash = self.get_file_hash(file_path)
            if file_path in self.file_hashes and current_hash == self.file_hashes[file_path]:
                return
            
            self.file_hashes[file_path] = current_hash
            self.last_save_times[file_path] = current_time

            # Create backup
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{filename}_{timestamp}"
            
            backup_dir = self.config.config["backup_dir"]
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_path = os.path.join(backup_dir, backup_name)
            shutil.copy2(file_path, backup_path)
            
            # Cleanup old backups
            self.cleanup_old_backups(file_path)
            
            print(f"✓ Backup created: {backup_name}")
            
        except Exception as e:
            print(f"❌ Error creating backup: {str(e)}")

def start_monitoring(path="."):
    event_handler = AdvancedChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    print(f"📂 Monitoring directory: {os.path.abspath(path)}")
    print("⚡ Auto-save is active")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Monitoring stopped!")
    
    observer.join()

if __name__ == "__main__":
    start_monitoring()
