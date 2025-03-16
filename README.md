# Backend for Healthcare Translation WebApp


Run 
1. `python -m venv myvenv` to create an environment separate from your local system for your packages
2. ` myvenv/Scripts/activate` to activate the env
3. `pip install requirements.txt`. to install the required packaged. All required packages are included in the requirements file.
4. `python app.py` to run the application. The application is run on http://127.0.0.1:5000/ by default.

### Endpoints
`POST /register`
- Registers a user 
- Returns: A successful or failed registration message.
  Sample: `curl baseUrl/register -X POST -H "Content-Type: application/json" -d {
  "username":"josh",
  "password":"12345678"
  }`

```json
{
  "message": "User registered successfully"
}
```

`POST /login`
- Logs the user into the web app
- Returns: Returns a JWT token.
  Sample: `curl baseUrl/login -X POST -H "Content-Type: application/json" -d {
  "username":"josh",
  "password":"12345678"
  }`

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjEzNTU0NywianRpIjoiOWNkZWE4NGMtMWI1ZC00YWY2LWFlNDktNGM5OWJkMzQ2MGJiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6Impvc2giLCJuYmYiOjE3NDIxMzU1NDcsImNzcmYiOiJlYTk4Yjk4ZC04OTc0LTRlODAtYTQ0My05ZGU2YjA5NGNiMmEiLCJleHAiOjE3NDIxMzY0NDd9.SqjxXIdvth76IeOMBgSwodsRnppAgw_cLlLEPdCZgM4"
}
```

`POST /text-to-speech`
- Convert a text to an audio
- Returns: an audio file.
  Sample: `curl baseUrl/text-to-speech -X POST -H "Content-Type: application/json" -d {
    "text": "Hello, how are you?"
}`

```json
{
  "audio": file
}
```

`POST /audio-to-text`
- Converts a text to an audio.
- Returns: a text extracted from an audio.
  Sample: `curl -X POST \
  baseUrl/speech-to-text \
  -H 'Content-Type: multipart/form-data' \
  -F 'audio=@/path/to/audio/file.wav;type=audio/wav'
`

```json
{
  "message": "holla amigos"
}
```

### Error Handling
Errors are returned as JSON objects in the following format:
```json
{
    "success": False, 
    "error": 400,
    "message": "bad request"
}
```

The API will return three error types when requests fail:

400: Bad Request
401: Unauthorized
500: Internal server error
