import os
import yaml
import json
import time
import boto3
import random
import requests
import humanize

# TODO: A lot of this is just repeat code with different keys and URLs. Try to rewrite this to not duplicate code and to be neater

def load_config():
	with open('config.yml', 'r') as fi:
		return yaml.safe_load(fi)

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

def get_json(url: str, api_key: str):
	url = "%s&api_key=%s" % (url, api_key)
	
	response = requests_session.get(url=url)
	return response.json()

requests_session = requests.Session()
def get_bills():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/bill?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1
		
		for bill in results["bills"]:
			count += 1
			session = bill["congress"]
			bill_type = bill["type"].lower()
			bill_number = bill["number"]
			key = "usa/federal/congress/bills/%s/%s/%s/data.json" % (session, bill_type, bill_number)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=bill["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=bill["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_members():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/member?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for member in results["members"]:
			count += 1
			member_id = member["bioguideId"]
			key = "usa/federal/congress/members/%s/data.json" % member_id
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=member["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=member["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_amendments():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/amendment?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for amendment in results["amendments"]:
			count += 1
			session = amendment["congress"]
			amendment_type = amendment["type"].lower()
			amendment_number = amendment["number"]
			key = "usa/federal/congress/amendments/%s/%s/%s/data.json" % (session, amendment_type, amendment_number)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=amendment["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=amendment["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_committee_reports():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/committee-report?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for committee_report in results["reports"]:
			count += 1
			session = committee_report["congress"]
			committee_report_type = committee_report["type"].lower()
			committee_report_number = committee_report["number"]
			# usa/federal/congress/committee-reports/$congress/$committeeReportType/$committeeReportNumber/data.json
			key = "usa/federal/congress/committee-reports/%s/%s/%s/data.json" % (session, committee_report_type, committee_report_number)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=committee_report["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=committee_report["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_treaties():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/treaty?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for treaty in results["treaties"]:
			count += 1
			session = treaty["congress"]
			treaty_number = treaty["treatyNum"]
			key = "usa/federal/congress/treaties/%s/%s/data.json" % (session, treaty_number)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=treaty["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=treaty["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_committees():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/committee?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for committee in results["committees"]:
			count += 1
			chamber = committee["chamber"].lower()
			systemCode = committee["systemCode"].lower()
			key = "usa/federal/congress/committees/%s/%s/data.json" % (chamber, systemCode)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=committee["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=committee["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_house_communications():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/house-communication?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for houseCommunication in results["houseCommunications"]:
			count += 1
			session = houseCommunication["congress"]
			houseCommunicationCode = houseCommunication["communicationType"]["code"].lower()
			houseCommunicationNumber = houseCommunication["number"]
			key = "usa/federal/congress/house-communications/%s/%s/%s/data.json" % (session, houseCommunicationCode, houseCommunicationNumber)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=houseCommunication["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=houseCommunication["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_senate_communications():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/senate-communication?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for senateCommunication in results["senateCommunications"]:
			count += 1
			session = senateCommunication["congress"]
			senateCommunicationCode = senateCommunication["communicationType"]["code"].lower()
			senateCommunicationNumber = senateCommunication["number"]
			key = "usa/federal/congress/senate-communications/%s/%s/%s/data.json" % (session, senateCommunicationCode, senateCommunicationNumber)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=senateCommunication["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=senateCommunication["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_nominations():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/nomination?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for nomination in results["nominations"]:
			count += 1
			session = nomination["congress"]
			nomination_number = nomination["number"]
			key = "usa/federal/congress/nominations/%s/%s/data.json" % (session, nomination_number)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=nomination["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=nomination["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_house_requirements():
	offset: int = 0
	limit: int = 250
	loop: bool = True
	
	global api_key
	while loop:
		url = "https://api.congress.gov/v3/house-requirement?api_key=%s&offset=%s&limit=%s&format=json" % (next(api_key), offset, limit)
		response = requests_session.get(url=url)
		results = response.json()
		
		rate_limit, rate_limit_remaining = get_rate_limit(response)
		if response.status_code != 200:
			print(results["error"]["message"])
			print("Waiting 60 Minutes To Try Again...")
			time.sleep(60*60)
			
			response = requests_session.get(url=url)
			results = response.json()
		
		# We are at the end of the results, stop looping
		if ("next" not in results["pagination"]):
			loop = False
		
		total = results["pagination"]["count"]
		count = offset-1

		for house_requirement in results["houseRequirements"]:
			count += 1
			house_requirement_number = house_requirement["number"]
			key = "usa/federal/congress/house-requirements/%s/data.json" % (house_requirement_number)
			
			# TODO: Make Better Restart Check
			if (os.path.exists("local/%s" % key)):
				continue
			
			data = get_json(url=house_requirement["url"], api_key=next(api_key))
			
			if "error" in data:
				error = data["error"]
				if "message" in error:
					print(error["message"])
					print("Waiting 60 Minutes To Try Again...")
					time.sleep(60*60)
				
					data = get_json(url=house_requirement["url"], api_key=next(api_key))
				elif "matches the given query" in error:
					print("Error: %s" % error)
					with open('error.log', 'a') as fi:
						fi.write("%s,%s://%s%s\n" % (error, scheme, netloc, path))
				else:
					print("Response: %s" % response.text)
			
			yield key, data, count, total

		offset += limit

def get_config():
	config = load_config()
	s3 = load_s3_client(config['s3'])
	
	api_key = get_api_key(config["congress"])
	
	return config, s3, api_key

def download_bills(config):
	for key, bill, count, total in get_bills():
		bill_text = json.dumps(bill)
		
		print("Uploading Bill (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=bill_text)
		upload_file(config=config['s3'], key=key, body=bill_text)

def download_members(config):
	for key, member, count, total in get_members():
		member_text = json.dumps(member)
		
		print("Uploading Member (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=member_text)
		upload_file(config=config['s3'], key=key, body=member_text)

def download_amendments(config):
	for key, amendment, count, total in get_amendments():
		amendment_text = json.dumps(amendment)
		
		print("Uploading Amendment (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=amendment_text)
		upload_file(config=config['s3'], key=key, body=amendment_text)

def download_committee_reports(config):
	for key, report, count, total in get_committee_reports():
		report_text = json.dumps(report)
		
		print("Uploading Committee Report (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=report_text)
		upload_file(config=config['s3'], key=key, body=report_text)

def download_treaties(config):
	for key, treaty, count, total in get_treaties():
		treaty_text = json.dumps(treaty)
		
		print("Uploading Treaty (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=treaty_text)
		upload_file(config=config['s3'], key=key, body=treaty_text)

def download_committees(config):
	for key, committee, count, total in get_committees():
		committee_text = json.dumps(committee)
		
		print("Uploading Committee (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=committee_text)
		upload_file(config=config['s3'], key=key, body=committee_text)

def download_house_communications(config):
	for key, house_communication, count, total in get_house_communications():
		house_communication_text = json.dumps(house_communication)
		
		print("Uploading House Communications (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=house_communication_text)
		upload_file(config=config['s3'], key=key, body=house_communication_text)

def download_senate_communications(config):
	for key, senate_communication, count, total in get_senate_communications():
		senate_communication_text = json.dumps(senate_communication)
		
		print("Uploading Senate Communications (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=senate_communication_text)
		upload_file(config=config['s3'], key=key, body=senate_communication_text)

def download_nominations(config):
	for key, nomination, count, total in get_nominations():
		nomination_text = json.dumps(nomination)
		
		print("Uploading Nominations (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=nomination_text)
		upload_file(config=config['s3'], key=key, body=nomination_text)

def download_house_requirement(config):
	for key, house_requirement, count, total in get_house_requirements():
		house_requirement_text = json.dumps(house_requirement)
		
		print("Uploading House Requirements (%s, %s): %s" % (humanize.intcomma(count), humanize.intcomma(total), key))
		save_local(key="local/%s" % key, body=house_requirement_text)
		upload_file(config=config['s3'], key=key, body=house_requirement_text)

if __name__ == "__main__":
	config, s3, api_key = get_config()
	#download_bills(config)
	#download_members(config)
	#download_committee_reports(config)
	#download_amendments(config)
	#download_treaties(config)
	#download_committees(config)
	#download_house_requirement(config)
	#download_house_communications(config)
	download_senate_communications(config)
	download_nominations(config)
