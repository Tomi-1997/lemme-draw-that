# 🤝 lemme-draw-that 🎨
Ever wanted to explain something, and it was easier to draw it? <br>
*"Wait a moment, let me draw that"*
#####  <ins> Now you can </ins> <br>
- 👋 Host a room.<br>
- 🤝 Invite others.<br>
- 💡 Share ideas.<br>
- 🎨 Not everyone present? Play a drawing guessing game while waiting. <br>

##### <ins> How it looks </ins>  <br>
![D](https://github.com/Tomi-1997/lemme-draw-that/blob/main/app/misc/demo3.gif) <br>

##### <ins> How to run </ins>  <br>
Requirements: 
+ app.py
+ Files in folder 'src' 
+ Files in folder 'static'
+ Files in folder 'templates'

Dependencies:
```
pip install Flask
pip install flask-socketio
```

Running:
+ Navigate via command line to the folder containting app.py
+ Type 'python app.py'
+ In the browser enter {localip}:{port}

Port is 8000 by default. <br>
You can check your local ip by running 'ipconfig' in the command line.

##### <ins> How to run in a container </ins>  <br>
+ Navigate to the folder containing 'Dockerfile' and build the image
```
docker build -t lemme-draw-that .
```
+ Run the container
```
docker run --rm -p 8000:8000 -e PORT=8000 -e PYTHONUNBUFFERED=1 lemme-draw-that
```

+ In the browser enter {localip}:{port}