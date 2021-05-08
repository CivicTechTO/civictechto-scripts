PASSWORD = $$ZOOM_API_SECRET

encrypt:
	openssl aes-256-cbc -k ${PASSWORD} -in service-key.json -out service-key.json.enc

decrypt:
	openssl aes-256-cbc -k ${PASSWORD} -in service-key.json.enc -out service-key.json -d
