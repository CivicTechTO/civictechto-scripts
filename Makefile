PASSWORD = $$ZOOM_API_SECRET

encrypt:
	gpg --batch --yes --passphrase="${PASSWORD}" --symmetric --cipher-algo AES256 service-key.json

decrypt:
	gpg --batch --yes --passphrase="${PASSWORD}" --decrypt --output service-key.json service-key.json.gpg

update-shortlinks:
	pipenv run python gsheet2shortlinks.py --yes \
		--domain-name "link.civictech.ca" \
		--gsheet "https://docs.google.com/spreadsheets/d/1LCVxEXuv70R-NozOwhNxZFtTZUmn1FLMPVD5wgIor9o/edit#gid=776462093"

notify-slack-roles:
	pipenv run python notify_slack_roles.py
