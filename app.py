import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build	
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]

drive = None
file_tree = []
subfolderlist = []

def login():
	creds = None
	if os.path.exists("token.json"):
		creds = Credentials.from_authorized_user_file("token.json", SCOPES)
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
					"credentials.json", SCOPES	
			)
			creds = flow.run_local_server(port=0)
		with open("token.json", "w") as token:
			token.write(creds.to_json())
	return creds

def search_for_subfolders(file):
	# 0 -> id
	# 1 -> name
	# 2 -> subfolders

	global drive
	query = f"'me' in owners and '{file['id']}' in parents and mimeType='application/vnd.google-apps.folder'"

	response = drive.files().list(
		q = query,
		supportsAllDrives=False).execute()
	items = response.get("files")
	files = []
	for item in items:
		file  = {"id": item["id"],"name": item["name"],"subfiles": []}
		subfolderlist.append(file["id"])
		file["subfiles"] = search_for_subfolders(file)
		files.append(file)
	return files
	

def get_all_files_data():
	global files, creds
	try:
		query = "mimeType='application/vnd.google-apps.folder' and 'me' in owners"
		orderBy = "folder"

		response = drive.files().list(
			orderBy=orderBy,
			q = query,
			supportsAllDrives=False).execute()

		items = response.get("files")

		for item in items:
			file  = {"id": item["id"],"name": item["name"],"subfiles": []}
			file["subfiles"] = search_for_subfolders(file)
			file_tree.append(file)

	except HttpError as error:
		print(f"An error occurred: {error}")

def cleanlist():
	global file_tree
	for item in file_tree:
		if item["id"] in subfolderlist:
			file_tree.remove(item)

def main():
	global drive
	creds = login()
	drive = build("drive", "v3", credentials=creds)
	get_all_files_data()
	print(subfolderlist)
	cleanlist()
	print("\n\n\n\n")
	print(file_tree)

if __name__ == "__main__":
	main()