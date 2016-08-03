# creates PTC accounts
# by anonymous_scripter

import random
import time
import os
import sys

# these are all external modules you'll need to download
# note: faker is installed via pip as "fake-factory" at the moment
import requests
from faker import Factory
from tempmail import TempMail
from simplejson import scanner
from bs4 import BeautifulSoup

fake = Factory.create('en_GB')
countries = [x.replace('\n', '').split('|') for x in open('./countries.txt').readlines()]

start = 0
stop = 100
randompostfix = True

if len(sys.argv) == 2:
    stop = int(sys.argv[1])
elif len(sys.argv) == 3:
	start = int(sys.argv[1])
	stop = int(sys.argv[2]) + 1
	randompostfix = False

for i in range(start, stop):
    # get names, DOB
	fname, lname = fake.first_name(), fake.last_name()
	dob = fake.date_time_between('-40y', '-20y')
	dob = [x.zfill(2) for x in map(str, [dob.year, dob.month, dob.day])]
	rand_country = random.choice(countries)
	ua = fake.user_agent()

	# first part of email, also used for username currently
	if randompostfix:
		postfix = str(random.randint(0, 999)).zfill(3)
	else:
		postfix = str(i).zfill(3)
    
	emailprefix = 'REPLACEME' + postfix
	
	print "email prefix is " + emailprefix

    tm = TempMail(login=emailprefix)
	
    # full email
    try:
        email = tm.get_email_address()
    except scanner.JSONDecodeError:
        # this generally doesn't fall through unless you try and get the email before
        # the TempMail call finishes...
        time.sleep(0.5)
        email = tm.get_email_address()

    password = 'REPLACEME'

    print "%s : %s - %s %s - %s - %s" % (email, password, fname, lname, '-'.join(dob), rand_country[0])

    highload = True

    sess = requests.Session()

    print 'First request...'
    r = sess.get('https://club.pokemon.com/us/pokemon-trainer-club/sign-up/')
    while highload or 'csrftoken' not in dict(r.cookies):
        if 'try again in an hour' in r.text or 'csrftoken' not in dict(r.cookies):
            print 'High load.'
            time.sleep(2)
            r = sess.get('https://club.pokemon.com/us/pokemon-trainer-club/sign-up/')
        else:
            highload = False

    time.sleep(2)

    print 'Second request...'
    # second request
    csrf = dict(r.cookies)['csrftoken']
    year = dob[0]
    month = dob[1]
    day = dob[2]
    country = rand_country[1]
    s = sess.post("https://club.pokemon.com/us/pokemon-trainer-club/sign-up/",
        data='csrfmiddlewaretoken={0}&dob={1}-{2}-{3}&undefined={5}&undefined={1}&country={4}&country={4}'.format(csrf, year, month, day, country, str(int(month) - 1)),
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://club.pokemon.com",
            "Referer": "https://club.pokemon.com/us/pokemon-trainer-club/sign-up/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "%s" % ua,
        },
    )

    if 'I accept the Pokemon.com Terms of Use.' in s.text:
        print 'Second worked!'
    else:
        print 'Second did not work.'
        #break

    time.sleep(2)

    print 'Third request...'
    t = sess.post("https://club.pokemon.com/us/pokemon-trainer-club/parents/sign-up",
        data='csrfmiddlewaretoken={0}&username={1}&password={2}&confirm_password={2}&email={3}&confirm_email={3}&public_profile_opt_in=True&screen_name={1}&terms=on'.format(csrf, emailprefix, password, email),
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://club.pokemon.com",
            "Referer": "https://club.pokemon.com/us/pokemon-trainer-club/parents/sign-up",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "%s" % ua,
        },
    )

    time.sleep(2)

    print 'Last request...'

    u = sess.get("https://club.pokemon.com/us/pokemon-trainer-club/parents/email",
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Referer": "https://club.pokemon.com/us/pokemon-trainer-club/parents/sign-up",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "%s" % ua,
        },
    )

    print 'Getting mail...'

    time.sleep(1)
    mail = False
    tries = 1

    while not mail and tries < 5:
        mail = tm.get_mailbox()
        try:
            print 'Attempt %s.' % tries
            bs = BeautifulSoup(mail[0]['mail_html'])
            mail = True

            activation_url = bs.find_all('a')[1]['href']

            print 'Activating account...'

            r = requests.get(activation_url)
            if 'Thank you for signing up!' in r.text:
                print "Worked!"

                if os.path.exists("accounts.txt"):
                    f = open('./accounts.txt', 'a+b')
                else:
                    f = open('./accounts.txt', 'w+b')

                f.write("%s:%s - %s - %s %s - %s - %s\n" % (emailprefix, password, email, fname, lname, '-'.join(dob), rand_country[0]))

                f.close()
            else:
                print "It didn't seem to work. If you like, here's the info so you can check yourself.\n%s : %s - %s %s - %s" % (email, password, fname, lname, '-'.join(dob))

        except KeyError:
            print 'Attempt %s didn\'t work.' % tries
            mail = False
            tries += 1
            time.sleep(1)