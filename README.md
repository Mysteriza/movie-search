# Movie Search
Movie Link Generator (Movie Search) is a Flask-based web application that helps users automatically search for movie links and subtitles from various popular sites. This application is designed to provide fast and accurate search results with a simple and responsive interface.

You can try it in [Movie Search](https://compact-molly-mysteriza-cf4a7a2f.koyeb.app/)

## Key Features
- Automatic Search: Enter a movie title, and the app will generate a list of links from various websites.
- Link Status: Each link is assigned a status (Found or Unsure) to help users determine its availability.
- Responsive Interface: Optimized for both desktop and mobile devices.
- Random User-Agent: Prevents bot detection when making HTTP requests to external sites.
## How to Run Locally

1. **Clone Repository**:
   ```
   git clone https://github.com/Mysteriza/movie-search.git && cd movie-search
   ```
   ```
   pip install -r requirements.txt
   ```
2. Create an .env file in the root directory, then fill it with:
   ```
   OMDB_API_KEY=YOUR_OMDB_API_KEY
   ```
   you can get the API for free [here](https://www.omdbapi.com/apikey.aspx), with a limit of 1000/day.
3. Run the app:
   ```
   python3 app.py
   ```
Open the link: http://127.0.0.1:5000

## Screenshot
![image](https://github.com/user-attachments/assets/8cfa4b07-d5f2-41f2-bf2d-a3c82683fce9)
![image](https://github.com/user-attachments/assets/8c0d385b-396b-4f1b-a1b1-6be1612bb019)
![image](https://github.com/user-attachments/assets/f315b7cd-8b3b-4d0e-a979-0dcc98eb6381)

