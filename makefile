.PHONY: dev

dev:
	npx concurrently "npm run dev" "cd backend && python main.py"
	