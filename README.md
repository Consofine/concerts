Flow: run "python spotify.py" to get list of all artists listened to on spotify account. 
(First run requires authentication, then all subsequent runs use refresh tokens.)
Then, run "python tickets.py" to query ticketmaster api and email results to specific addresses. 
Requires api keys in keys.py in directory, as well as email information in emailKeys.py for sending and receiving.
Also uses absolute paths for compatibility with cronjobs
