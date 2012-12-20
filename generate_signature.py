#!/usr/bin/python
import gdata.apps.emailsettings.client
import gdata.contacts.client
import gdata.contacts.service
from threading import Thread
from Queue import Queue
from datetime import datetime

# get these values from your cpanel
CONSUMER_KEY = ''
CONSUMER_SECRET = ''
company_name = ''
admin_username = ''

# request a 2-legged OAuth token
requestor_id = admin_username + '@' + CONSUMER_KEY
two_legged_oauth_token = gdata.gauth.TwoLeggedOAuthHmacToken(CONSUMER_KEY, CONSUMER_SECRET, requestor_id)

# Email Settings API client
email_settings_client = gdata.apps.emailsettings.client.EmailSettingsClient(domain=CONSUMER_KEY)
email_settings_client.auth_token = two_legged_oauth_token

# User Profiles API client
profiles_client = gdata.contacts.client.ContactsClient(domain=CONSUMER_KEY)
profiles_client.auth_token = two_legged_oauth_token

# helper class used to build signatures
class SignatureBuilder(object):
	def HtmlSignature(self):
		signature =' <div>'
		signature +='Kind Regards,<br/>'
		signature +='%s<br/>'% self.name 
		signature +='%s | %s<br/>'% (self.title, self.officelocation)
		signature +='Telephone: %s<br/>' % self.PhoneNumber
		signature +='Mobile: %s<br/>' % self.MobileNumber
		signature +='Fax: %s<br/>' % self.FaxNumber
		signature +='Website: %s<br/>' % self.Website
		signature +=' </div>'
		return signature
	def __init__(self, name, email='', title='', officelocation='', Website='', PhoneNumber='', FaxNumber='', MobileNumber=''):
		self.name = name
		self.email = email
		self.title = title
		self.officelocation = officelocation
		self.PhoneNumber = PhoneNumber
		self.FaxNumber = FaxNumber
		self.MobileNumber = MobileNumber 
		self.Website = Website
		self.uname = uname
# function to get Profiles from Directory
def getProfiles():
	# get all user profiles for the domain
	profiles = []
	feed_uri = profiles_client.GetFeedUri('profiles')
	print '\nGetting User Profiles (This may take a while)\n'
	while feed_uri:
		feed = profiles_client.GetProfilesFeed(uri=feed_uri)
		profiles.extend(feed.entry)
		feed_uri = feed.FindNextLink()
		print len(profiles)
	return profiles
# function that does all the magic
def genSignature():
	global pass_count
	global fail_count
	global log
	while True: 
		try:
			entry = q.get()
			uname = entry.id.text[entry.id.text.rfind('/')+1:]
			st = str(entry)
			soup = BeautifulSoup(st)
			for tag in soup.findAll('ns1:name'):
				fname = tag.find('ns1:familyname').text
				lname = tag.find('ns1:givenname').text
			name = "%s %s" % (fname,lname)
			builder = SignatureBuilder(name)
			builder.uname = uname
			for tag in soup.findAll('ns1:organization'):
				if tag.find('ns1:orgtitle'):
					builder.title = tag.find('ns1:orgtitle').text
				builder.officelocation = "Head Office"
				builder.PhoneNumber = "+254 20 999 999"
				builder.FaxNumber = "+254 20 111 111" 
				builder.MobileNumber = "+254 720 949 668"
				builder.email= uname + '@' + CONSUMER_KEY
				builder.Website= CONSUMER_KEY
			#build signature
			signature = builder.HtmlSignature()
			#upload signature
			email_settings_client.UpdateSignature(username=builder.email,signature=signature)
			print "Signature Added for: %s" % builder.email
			log.append("Signature Added for: %s" % builder.email)
			pass_count=pass_count+1
			print "Success:%d , Fail:%d \n" %(pass_count,fail_count)
			q.task_done()
		except Exception,e:
			print e
			log.append("Signature Failed for: %s \n %s" % (builder.email,e))
			fail_count = fail_count+1
			print "Success:%d , Fail:%d \n" %(pass_count,fail_count)
			q.task_done()
pass_count =0
fail_count =0
q =Queue()
log = []
# Main function whose responsibility is handling the queue with some awesome threads
def main():
	global pass_count
	global fail_count
	global log
	print '\nGenerating Signatures for your Domain\n\n'
	for i in range(40): # Number of threads to run
		t = Thread(target=genSignature)
		t.daemon = True
		t.start()		
	for entry in getProfiles():
		q.put(entry)
	q.join()
	text_file = open("log.txt", "w")
	for i in log:
		text_file.write("%s \n" % (i))
	text_file.write("\nSuccess:%d , Fail:%d \n" % (pass_count,fail_count))
	text_file.write("script done on: %s \n" % (datetime.now()))
	text_file.close()
	print "\nSuccess:%d , Fail:%d \n" %(pass_count,fail_count)
	print "Script done at :%s"% (datetime.now())	
main()
#Enjoy