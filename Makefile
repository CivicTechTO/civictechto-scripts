PASSWORD = $$ZOOM_API_SECRET

encrypt:
	pipenv run gpg --batch --yes --passphrase="${PASSWORD}" --symmetric --cipher-algo AES256 service-key.json
	pipenv run gpg --batch --yes --passphrase="${PASSWORD}" --symmetric --cipher-algo AES256 client_secret.json
	pipenv run gpg --batch --yes --passphrase="${PASSWORD}" --symmetric --cipher-algo AES256 .youtube-upload-credentials.json

decrypt:
	gpg --batch --yes --passphrase="${PASSWORD}" --decrypt --output service-key.json service-key.json.gpg
	gpg --batch --yes --passphrase="${PASSWORD}" --decrypt --output client_secret.json client_secret.json.gpg
	gpg --batch --yes --passphrase="${PASSWORD}" --decrypt --output .youtube-upload-credentials.json .youtube-upload-credentials.json.gpg

update-shortlinks:
	pipenv run python gsheet2shortlinks.py --yes \
		--domain-name "link.civictech.ca" \
		--gsheet "https://docs.google.com/spreadsheets/d/1LCVxEXuv70R-NozOwhNxZFtTZUmn1FLMPVD5wgIor9o/edit#gid=776462093"

notify-slack-roles:
	pipenv run python notify_slack_roles.py

notify-slack-pitches:
	pipenv run python notify_slack_pitches.py

reset-pitches:
	# Move from list "Tonight's Pitches" to "Recent Pitches"
	pipenv run python move_trello_cards.py --verbose \
		--from-list "58e158f29b0ae02ab71b9a87" \
		--to-list "58e158eba6846a4fb012404c" \

save-pitch-data:
	pipenv run python update_pitch_csv.py

zoom2youtube:
	pipenv run python src/main.py
