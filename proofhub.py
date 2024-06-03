import os
import requests
import schedule
from datetime import datetime, timedelta, timezone

# ProofHub API credentials and base URL
proofhub_api_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
proofhub_base_url = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  # Make sure to use the correct API version
headers = {'X-API-KEY': proofhub_api_key, 'Content-Type': 'application/json'}

# Local folder where files will be downloaded
local_folder = 'C:\\'
local_root_folder = os.path.join(local_folder, "Project Files")

# Replace 'project_id' with your specific project ID
project_id = 'xxxxxxxxxxx'
folder_id = 'xxxxxxx'  # id of the root folder "Project Files"

parents ={}
names={}
# Function to get the list of files in a folder
def list_files_in_folder(project_id, folder_id):
    folder_url = f'{proofhub_base_url}projects/{project_id}/folders/{folder_id}/files'
    response = requests.get(folder_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error listing files in folder (Status Code: {response.status_code}): {response.text}")
        return None


# Function to download a file
def download_file(file_info, local_folder_path):
    file_name = file_info['name']
    file_url = file_info["url"]["view"]
    response = requests.get(file_url, headers=headers)

    if response.status_code == 200:
        # Ensure the local folder path exists, creating it if necessary
        os.makedirs(local_folder_path, exist_ok=True)

        with open(os.path.join(local_folder_path, file_name), 'wb') as local_file:
            local_file.write(response.content)
        print(f"Downloaded: {local_file}")
    else:
        print(f"Error downloading file {file_name} (Status Code: {response.status_code}): {response.text}")


# Function to check if a file has been updated in the last 24 hours
def is_file_updated_last_96_hours(file_info):
    updated_at = datetime.strptime(file_info['updated_at'], "%Y-%m-%dT%H:%M:%S+00:00")
    updated_at = updated_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - updated_at < timedelta(hours=96)


# Function to get the files
def get_files(project_id, folder_id, local_folder_path):
    files = list_files_in_folder(project_id, folder_id)

    if files is not None:
        for file_info in files:
            if is_file_updated_last_96_hours(file_info):
                download_file(file_info, local_folder_path)


# Function to traverse the subfolders recursively
def traverse_subfolders(subfolders, subfolder_path):
    parents[subfolders["id"]]=subfolders["parent_id"]
    names[subfolders["id"]]=subfolders["name"]
    if subfolders.get("children", []) == []:
        subfolder_path = os.path.dirname(subfolder_path)
        return subfolder_path
    for subfolder in subfolders.get("children", []):
        subfolder_name = subfolder['name']
        if subfolder_path is None:
            if subfolder["parent_id"] is None:
                subfolder_path = local_root_folder
            else:
                path_c =[]
                parent_id = subfolder["parent_id"]
                while parent_id is not None:
                    path_c.append(names[parent_id])
                    parent_id = parents[parent_id]
                path_c.reverse()
                subfolder_path = os.path.join(local_root_folder, *path_c)
        subfolder_path = os.path.join(subfolder_path, subfolder_name)
        get_files(project_id, subfolder['id'], subfolder_path)
        subfolder_path = traverse_subfolders(subfolder, subfolder_path)


# Function to start looking for all folders inside the project
def traverse_folders(project_id, folder_id, local_folder_path):
    get_files(project_id, folder_id, local_folder_path)

    folders_url = f'{proofhub_base_url}projects/{project_id}/folders'
    response = requests.get(folders_url, headers=headers)

    if response.status_code == 200:
        subfolders = response.json()
        traverse_subfolders(subfolders, local_folder_path)


if not os.path.exists(local_folder):
    os.makedirs(local_folder)

# Start traversal from the root folder (you can specify the root folder ID if needed)
traverse_folders(project_id, folder_id, local_root_folder)
