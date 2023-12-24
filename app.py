import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build	
from googleapiclient.errors import HttpError
from termcolor import colored


class Drive:
	def __init__(self) -> None:
		self.drive = None
		self.file_tree = []
		self.subfolderlist = [] 

	def build(self):
		creds = None
		SCOPES = ["https://www.googleapis.com/auth/drive"]
		try:
			if os.path.exists("token.json"):
				creds = Credentials.from_authorized_user_file("token.json", SCOPES)
			if not creds or not creds.valid:
				if creds and creds.expired and creds.refresh_token:
					creds.refresh(Request())
				else:
					flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
					creds = flow.run_local_server(port=0)
				with open("token.json", "w") as token:
					token.write(creds.to_json())
			self.drive = build("drive", "v3", credentials=(creds))
			return 0
		except Exception as error:
				print(colored(error,"red"))
		return -1
	def display(self):
		self.D(self.file_tree,0)
	
	def D(self, tree, depth):
		for branch in tree:
			pre = "    " * depth
			if depth != 0: pre = pre + "┗━━━"
			if branch["type"] == "folder":
				print(colored(pre + " ", 'green'), colored(branch['name'], 'light_blue'))
			else:
				print(colored(pre + " ", 'green'), colored(branch['name'], 'light_red'))
			self.D(branch["subfiles"], depth+1)

	def search_for_subfolders(self,file):
		query = f"'me' in owners and '{file['id']}' in parents"

		response = self.drive.files().list(
			q = query,
			supportsAllDrives=False).execute()
		items = response.get("files")
		files = []
		for item in items:
			file  = {"id": item["id"],"name": item["name"],"subfiles": [], "type": self.get_file_type(item)}
			self.subfolderlist.append(file["id"])
			file["subfiles"] = self.search_for_subfolders(file)
			files.append(file)
		return files

	def get_file_type(self,file):
		type = file["mimeType"]
		if "folder" in type:
			return "folder"
		if "photo" in type or "image" in type:
			return "image"
		if "pdf" in type:
			return "pdf"
		if "document" in type:
			return "document"
		return type


	def get_all_files_data(self):
		try:
			query = "'me' in owners and mimeType='application/vnd.google-apps.folder'"
			orderBy = "folder"

			response = self.drive.files().list(
				orderBy=orderBy,
				q = query,
				supportsAllDrives=False).execute()

			items = response.get("files")

			for item in items:
				file  = {"id": item["id"],"name": item["name"],"subfiles": [], "type": self.get_file_type(item)}
				if file["type"] == "folder":
					file["subfiles"] = self.search_for_subfolders(file)
				self.file_tree.append(file)

		except HttpError as error:
			print(f"An error occurred: {error}")

	def cleanlist(self):
		temp_tree = self.file_tree
		for item in self.file_tree:
			if item["id"] in self.subfolderlist:
				temp_tree.remove(item)
		self.file_tree = temp_tree
	
	def execute(self):
		if os.path.exists("drive_cache.json"):
			self.uncache()
		else:	
			self.get_all_files_data()
			self.cleanlist()
			self.cleanlist()

	def uncache(self):
		res = []
		if os.path.exists("drive_cache.json"):
			with open("drive_cache.json", 'r') as file:
				res = file.readlines()
		for r in res:
			f = json.loads(r[:len(r)-2])
			self.file_tree.append(f)
	
	def refresh(self):
		if os.path.exists("drive_cache.json"):
			os.remove("drive_cache.json")
			self.execute()

	def cache(self):
		with open("drive_cache.json", "a") as c:
			for file in self.file_tree:
				json.dump(file, c)
				c.write(",\n")

# drive = Drive()
# drive.build()
# drive.execute()
# drive.display()