.PHONY: qa fix clean

qa:               ## lancia tutti i controlli (non modificano nulla)
	ruff check .
	mypy .

fix:              ## auto-fix dove possibile
	ruff check --fix .
	prettier --write "**/*.{js,ts,css,json,md}"

clean:            ## rimuovi cache
	rm -rf .ruff_cache .mypy_cache