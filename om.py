import os

# Define the list of scripts in the desired execution order
execution_order = [
    'generate_data.py',
    'generate_query.py',
    'query_u.py',
    'data_owner.py',
    'query_u.py',  # This duplicates query_u.py as per your original order
    'cloud_server.py'
]

# Function to execute scripts in the specified order
def execute_scripts_in_order(execution_order):
    for script_name in execution_order:
        # Remove any leading or trailing whitespace characters
        script_name = script_name.strip()
        # Execute the script
        print(f"Executing {script_name}...")
        os.system(f"python {script_name}")

# Execute scripts in the specified order
execute_scripts_in_order(execution_order)
