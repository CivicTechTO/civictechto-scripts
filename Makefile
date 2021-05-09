PASSWORD = $$ZOOM_API_SECRET

encrypt:
	openssl aes-256-cbc -k ${PASSWORD} -in service-key.json -out service-key.json.enc

decrypt:
	openssl aes-256-cbc -k ${PASSWORD} -in service-key.json.enc -out service-key.json -d

encrypt-gpg:
	gpg --batch --yes --passphrase="${PASSWORD}" --symmetric --cipher-algo AES256 service-key.json

decrypt-gpg:
	gpg --batch --yes --passphrase="${PASSWORD}" --decrypt --output service-key.json service-key.json.gpg
