import json
import subprocess
import os
import copy
from datetime import datetime

def run_experiment(base_config, setting_name, storage_config, test_id):
    """
    Configures and runs a single experiment.
    """
    config = copy.deepcopy(base_config)
    
    # 1. Set the current setting and storage paths
    config['setting'] = [setting_name]
    config['test_dir'] = storage_config['test_dir']
    config['faasnap']['base_path'] = storage_config['base_path']

    # 2. Conditionally modify interval_threshold for faasnap on NFS
    if setting_name == 'faasnap' and storage_config['is_nfs']:
        print(f"  -> Detected faasnap on NFS. Modifying interval_threshold to 0.")
        config['settings']['faasnap']['record_regions']['interval_threshold'] = 0
        config['settings']['faasnap']['patch_mincore']['interval_threshold'] = 0

    # Create a temporary config file for the run
    temp_config_filename = f"temp_config_{setting_name}_{storage_config['name']}.json"
    with open(temp_config_filename, 'w') as f:
        json.dump(config, f, indent=4)

    # 3. Use the shared TESTID for results
    # Prepare environment for the subprocess
    env = os.environ.copy()
    env['TESTID'] = test_id
    if 'RESULT_DIR' not in env:
        print("  -> WARNING: RESULT_DIR environment variable not set. Results may not be saved.")
        env['RESULT_DIR'] = '/users/muhan/faasnap/results' # Default to current directory if not set

    print(f"  -> Running sub-test with TESTID: {test_id}")
    print(f"  -> Config file: {temp_config_filename}")
    
    # 4. Execute the test script
    try:
        print("  -> Cleaning up previous main and firecracker processes...")
        subprocess.run(['sudo', 'pkill', '-9', 'main'], check=False)
        subprocess.run(['sudo', 'pkill', '-9', 'firecracker'], check=False)
        
        command = ['sudo', 'python3', 'test.py', temp_config_filename]
        subprocess.run(command, check=True, env=env)
        print(f"  -> Successfully completed sub-test: {setting_name}-{storage_config['name']}")
    except subprocess.CalledProcessError as e:
        print(f"  -> ERROR: Test failed for {setting_name}-{storage_config['name']}. Return code: {e.returncode}")
    except FileNotFoundError:
        print("  -> ERROR: 'sudo' or 'python3' or 'test.py' not found. Make sure they are in your PATH.")
    finally:
        # 5. Clean up the temporary config file
        # os.remove(temp_config_filename)
        print("-" * 40)


if __name__ == "__main__":
    base_config_file = 'test-2inputs.json'

    # Define the matrix of experiments
    # settings_to_run = ["vanilla"]
    settings_to_run = ["vanilla"]
    storage_configs = [
        {
            "name": "local",
            "test_dir": "/mnt/snapshot",
            "base_path": "/mnt/vm",
            "is_nfs": False
        },
        {
            "name": "nfs",
            "test_dir": "/users/muhan/faasnap/nfs-dir/snapshot",
            "base_path": "/users/muhan/faasnap/nfs-dir/vm",
            "is_nfs": True
        }
    ]
    try:
        with open(base_config_file, 'r') as f:
            base_config_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Base config file '{base_config_file}' not found.")
        exit(1)

    # Generate a single TESTID for the entire batch of experiments
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    test_id = f"expr-batch-{timestamp}"
    print(f"Running experiment batch with a single TESTID: {test_id}")
    print("=" * 60)
    
    print("  -> Building faasnap-server...")
    subprocess.run(['go', 'build', 'cmd/faasnap-server/main.go'], check=True)
    print("  -> Build successful.")
    
    # Loop through all combinations and run experiments
    for setting in settings_to_run:
        for storage in storage_configs:
            print(f"Starting sub-experiment: Setting='{setting}', Storage='{storage['name']}'")
            # Remove contents while preserving the directories
            subprocess.run(['sudo', 'rm', '-rf', storage['test_dir']], check=True)
            subprocess.run(['sudo', 'rm', '-rf', storage['base_path']], check=True)
            subprocess.run(['sudo', 'sync'], check=True)
            # Create directories if they don't exist
            print(f"deleting.. {storage['test_dir']}, {storage['base_path']}")
            subprocess.run(['sudo', 'mkdir', storage['test_dir']], check=True)
            subprocess.run(['sudo', 'mkdir', storage['base_path']], check=True)
            run_experiment(base_config_data, setting, storage, test_id)

    print("All experiments finished.")