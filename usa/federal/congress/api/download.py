import os
import yaml
import json
import time
import boto3
import dpath
import random
import requests
import humanize

from urllib.parse import urlparse

total: int = 1519722

def load_config():
	with open('config.yml', 'r') as fi:
		return yaml.safe_load(fi)

def get_config():
	config = load_config()
	s3 = load_s3_client(config['s3'])
	
	api_key = get_api_key(config["congress"])
	
	return config, s3, api_key

def load_s3_client(config: dict):
	return boto3.client(
		service_name='s3',
		aws_access_key_id=config['access_key_id'],
		aws_secret_access_key=config['secret_access_key'],
		endpoint_url=config['endpoint']
	)

def upload_file(config: dict, key: str, body: str):
	#data = open('test.jpg', 'rb')
	#s3.Bucket('my-bucket').put_object(Key='test.jpg', Body=data)
	s3.put_object(
		Bucket=config['default_bucket'],
		Body=body,
		Key=key
	)

def save_local(key: str, body: str):
	key: str = "local/%s" % key
	path: str = os.path.dirname(key)
	if not os.path.exists(path):
		os.makedirs(path)
	
	file = open(key, 'w')
	file.write(body)
	file.close()

def get_rate_limit(response):
	# Monitor Rate Limit - 1,000 Requests Per Hour
	rate_limit = response.headers["x-ratelimit-limit"]
	rate_limit_remaining = response.headers["x-ratelimit-remaining"]
	#print("Rate Limit: %s/%s" % (rate_limit_remaining, rate_limit))
	
	return rate_limit, rate_limit_remaining

def get_api_key(config):
	#return config["api_key"]
	
	#return random.choice(config["keys"])
	
	total = len(config["keys"])
	current = 0
	while True:
		yield config["keys"][current]
		
		if current >= total-1:
			current = 0
		else:
			current += 1

def get_key(url: str):
	path: str = urlparse(url).path
	
	split = path.split("/")[2:]
	
	# TODO: Consider Moving Paths Back To Original Names
	if split[0] == "amendment":
		split[0] = "amendments"
	elif split[0] == "bill":
		split[0] = "bills"
	elif split[0] == "member":
		split[0] = "members"
	elif split[0] == "committee-report":
		split[0] = "committee-reports"
	elif split[0] == "treaty":
		split[0] = "treaties"
	
	#summaries
	#committees
	#nominations
	#house-communication
	#senate-communication
	#congressional-record
	#house-requirement
	
	partial = "/".join(split)
	key = "usa/federal/congress/%s/data.json" % partial
	
	return key

def exists(key: str):
	return os.path.exists("local/%s" % key)

session = requests.Session()
def get_json(api_key: str, url: str):
	global session
	
	# https://api.congress.gov/v3/member/A000217?format=json
	parsed: str = urlparse(url)
	scheme: str = parsed.scheme
	netloc: str = parsed.netloc
	path: str = parsed.path
	url: str = "%s://%s%s?api_key=%s&format=json" % (scheme, netloc, path, api_key)
	
	response = session.get(url=url)
	try:
		results = response.json()
	except:
		print("Read JSON Error: %s" % response.text)
		with open('json-error.log', 'a') as fi:
			fi.write("%s,%s://%s%s\n" % (response.text, scheme, netloc, path))
		return None
		
	
	rate_limit, rate_limit_remaining = get_rate_limit(response)
	if response.status_code != 200:
		error = results["error"]
		
		if "message" in error:
			print(error["message"])
			print("Paused at %s://%s%s" % (scheme, netloc, path))
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
		
			response = session.get(url=url)
			return response.json()
		elif "matches the given query" in error:
			print("Error: %s" % error)
			with open('error.log', 'a') as fi:
				fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
		else:
			print("Response: %s" % response.text)
	
	return results

download_count: int = 0
def download_file(url: str):	
	global api_key
	global config
	global download_count
	global total
	
	if url is None:
		return
	
	key: str = get_key(url=url)
	
	if exists(key=key):
		return
	
	download_count += 1
	#return
	
	results = get_json(api_key=next(api_key), url=url)
	
	# For When Failing To Retrieve JSON At All
	if results is None:
		return
	
	text = json.dumps(results)
	
	print("Uploading File (%s/%s) - %s%% - %s" % (humanize.intcomma(download_count), humanize.intcomma(total), humanize.intcomma((download_count/total)*100), key))
	#print(results)
	save_local(key=key, body=text)
	upload_file(config=config['s3'], key=key, body=text)

def download_data(path: str):
	with open(file=path, mode="r") as f:
		contents: dict = json.load(f)
		
		#print("Path: %s" % path)
		if "bill" in contents:
			bill: dict = contents["bill"]
			actions: str = bill["actions"]["url"] if "actions" in bill else None
			textVersions: str = bill["textVersions"]["url"] if "textVersions" in bill else None
			titles: str = bill["titles"]["url"] if "titles" in bill else None
			committees: str = bill["committees"]["url"] if "committees" in bill else None
			cosponsors: str = bill["cosponsors"]["url"] if "cosponsors" in bill else None
			subjects: str = bill["subjects"]["url"] if "subjects" in bill else None
			summaries: str = bill["summaries"]["url"] if "summaries" in bill else None
			relatedBills: str = bill["relatedBills"]["url"] if "relatedBills" in bill else None
			amendments: str = bill["amendments"]["url"] if "amendments" in bill else None
			
			# Array
			sponsors: str = bill["sponsors"][0]["url"] if "sponsors" in bill else None
			committeeReports: str = bill["committeeReports"][0]["url"] if "committeeReports" in bill else None
			notes: str = bill["notes"][0] if "notes" in bill else {}
			notes: str = notes["links"][0]["url"] if "links" in notes and len(notes["links"]) > 0 else None
			cboCostEstimates: str = bill["cboCostEstimates"][0]["url"] if "cboCostEstimates" in bill else None
			
			#bill.pop('actions', None)
			#bill.pop('textVersions', None)
			#bill.pop('titles', None)
			#bill.pop('committees', None)
			#bill.pop('cosponsors', None)
			#bill.pop('subjects', None)
			#bill.pop('summaries', None)
			#bill.pop('relatedBills', None)
			#bill.pop('amendments', None)
			
			# Array
			#bill.pop('sponsors', None)
			#bill.pop('committeeReports', None)
			#bill.pop('notes', None)
			#bill.pop('cboCostEstimates', None)
			
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Bill - %s: %s" % (path, value))
			
			download_file(url=actions)
			download_file(url=textVersions)
			download_file(url=titles)
			download_file(url=committees)
			download_file(url=cosponsors)
			download_file(url=subjects)
			download_file(url=summaries)
			download_file(url=relatedBills)
			download_file(url=amendments)
			
			# TODO: Implement Reading Arrays
			#download_file(url=sponsors)
			#download_file(url=committeeReports)
			#download_file(url=notes)
			#download_file(url=cboCostEstimates)
			
		elif "committeeReports" in contents:
			committeeReports: dict = contents["committeeReports"]
			committees: str = committeeReports[0]["committees"][0]["url"] if "committees" in committeeReports else None
			associatedBill: str = committeeReports[0]["associatedBill"][0]["url"] if "associatedBill" in committeeReports else None
			associatedTreaties: str = committeeReports[0]["associatedTreaties"][0]["url"] if "associatedTreaties" in committeeReports else None
			
			#committeeReports[0].pop('committees', None)
			#committeeReports[0].pop('associatedBill', None)
			#committeeReports[0].pop('associatedTreaties', None)
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Committee Reports - %s: %s" % (path, value))
				
			# TODO: Implement Reading Arrays
			#download_file(url=committees)
			#download_file(url=associatedBill)
			#download_file(url=associatedTreaties)
		elif "amendment" in contents:
			amendment: dict = contents["amendment"]
			actions: str = amendment["actions"]["url"] if "actions" in amendment else None
			cosponsors: str = amendment["cosponsors"]["url"] if "cosponsors" in amendment else None
			amendedBill: str = amendment["amendedBill"]["url"] if "amendedBill" in amendment else None
			amendedAmendment: str = amendment["amendedAmendment"]["url"] if "amendedAmendment" in amendment else None
			amendmentsToAmendment: str = amendment["amendmentsToAmendment"]["url"] if "amendmentsToAmendment" in amendment else None
			amendedTreaty: str = amendment["amendedTreaty"]["url"] if "amendedTreaty" in amendment else None
			
			# Array
			sponsors: str = amendment["sponsors"][0]["url"] if "sponsors" in amendment else None
			latestAction: str = amendment["latestAction"] if "latestAction" in amendment else {}
			latestAction: str = latestAction["links"][0]["url"] if "links" in latestAction else None
			links: str = amendment["links"][0]["url"] if "links" in amendment else None
			notes: str = amendment["notes"][0] if "notes" in amendment else {}
			notes: str = notes["links"][0]["url"] if "links" in notes and len(notes["links"]) > 0 else None
			
			#amendment.pop('actions', None)
			#amendment.pop('cosponsors', None)
			#amendment.pop('amendedBill', None)
			#amendment.pop('amendedAmendment', None)
			#amendment.pop('amendmentsToAmendment', None)
			#amendment.pop('amendedTreaty', None)
			
			# Array
			#amendment.pop('sponsors', None)
			#amendment.pop('latestAction', None)
			#amendment.pop('links', None)
			#amendment.pop('notes', None)
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Amendment - %s: %s" % (path, value))
				
			download_file(url=actions)
			download_file(url=cosponsors)
			download_file(url=amendedBill)
			download_file(url=amendedAmendment)
			download_file(url=amendmentsToAmendment)
			download_file(url=amendedTreaty)
			
			# TODO: Implement Reading Arrays
			#download_file(url=sponsors)
			#download_file(url=latestAction)
			#download_file(url=links)
			#download_file(url=notes)
		elif "member" in contents:
			member: dict = contents["member"]
			actions: str = member["actions"]["url"] if "actions" in member else None
			sponsoredLegislation: str = member["sponsoredLegislation"]["url"] if "sponsoredLegislation" in member else None
			cosponsoredLegislation: str = member["cosponsoredLegislation"]["url"] if "cosponsoredLegislation" in member else None
			
			#member.pop('actions', None)
			#member.pop('sponsoredLegislation', None)
			#member.pop('cosponsoredLegislation', None)
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Member - %s: %s" % (path, value))
				
			download_file(url=actions)
			download_file(url=sponsoredLegislation)
			download_file(url=cosponsoredLegislation)
		elif "treaty" in contents:
			treaty: dict = contents["treaty"]
			actions: str = treaty["actions"]["url"] if "actions" in treaty else None
			
			#treaty.pop('actions', None)
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Treaty - %s: %s" % (path, value))
		elif "summaries" in contents:
			summaries: dict = contents["summaries"]
			
			#summaries.pop('actions', None)
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Summaries - %s: %s" % (path, value))
		elif "committees" in contents:
			committees: dict = contents["committees"]
			
			#committees.pop('actions', None)
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Committees - %s: %s" % (path, value))
		elif "nominations" in contents:
			nominations: dict = contents["nominations"]
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Nominations - %s: %s" % (path, value))
		elif "house-communication" in contents:
			houseCommunication: dict = contents["house-communication"]
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("House Communication - %s: %s" % (path, value))
		elif "senate-communication" in contents:
			senateCommunication: dict = contents["senate-communication"]
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Senate Communication - %s: %s" % (path, value))
		elif "congressional-record" in contents:
			congressionalRecord: dict = contents["congressional-record"]
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Congressional Record - %s: %s" % (path, value))
		elif "house-requirement" in contents:
			houseRequirement: dict = contents["house-requirement"]
			
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("House Requirement - %s: %s" % (path, value))
		else:
			# TODO: Find URLs From Other Files and Check If Already Downloaded
			#for (path, value) in dpath.search(contents, '**/url', yielded=True):
				#print("Other - %s: %s" % (path, value))
				#download_file(url=value)
				
			pass

def read_bills():
	path: str = 'local'
	
	for (dirpath, dirnames, filenames) in os.walk(path):
		for filename in filenames:
			if filename.endswith('.json'):
				file_path: str = os.sep.join([dirpath, filename])
				download_data(path=file_path)

if __name__ == "__main__":
	config, s3, api_key = get_config()
	read_bills()
	#print("Total Bill Count: %s" % download_count)
