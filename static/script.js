console.log('JS Starting')


/* Initialize on load */
let canvas = null;
let ctx = null;
let socket = null;
let info = null;

/* Drawing vars */
let erasing = false;
let drawing = false;
let lastX = 0;
let lastY = 0;
const brushColor = '#dcdcdc';
const brushSize = 2;
const eraserSize = 40;
let userColor = brushColor;
let userSize = brushSize;


/* Work queue, to let other clients paint on screen */
var workQueue = []
var runnable = function(fn, context, params)
{
    return function()
    {
        fn.apply(context, params);
    }
}

/* On HTML load - init divs */
window.addEventListener('load', function() 
{
    canvas = document.getElementById('canvas');
    setCanvasSize(canvas);
    ctx = canvas.getContext('2d');
    info = this.document.getElementById('info-el');

    // Generate a random color for each user
    ctx.strokeStyle = userColor; // Set the stroke color for this user

    socket = io();
    addEvents();
});


// Set canvas size, based on page size (phone / pc)
function setCanvasSize(canvas)
{
    if (window.innerWidth <= 600) 
        {
        canvas.width = 300;
        canvas.height = 200;
    } else 
    {
        canvas.width = 800;
        canvas.height = 500;
    }
}


// Someone else pressed clear
function onClear()
{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.style.animation = 'none'; // Remove the animation
    canvas.offsetHeight; // Trigger reflow
    canvas.style.animation = ''; // Reapply the 
}


// Clear button press
function onClearOrigin(button)
{
    onClear();
    socket.emit('clear', {});
    disableXForYSec(button, 3000);
}


// Disable a button for a certain amount of time
function disableXForYSec(x, y)
{
    x.disabled = true;
    x.opacity = 0.5;
    setTimeout(() => {
        x.disabled = false;
    }, y);
}


// Eraser button press
function onEraser(button)
{
    erasing = !erasing;
    if (erasing)
    {
        userSize = eraserSize;
        button.innerText = "[E]DITOR";
    }
    else
    {
        userSize = brushSize;
        button.innerText = "[E]RASER";
    }

    button.style.animation = 'none';
    button.offsetHeight;
    button.style.animation = "pop 0.2s ease forwards";
}


// Guesser button press
function onGuessOrigin()
{
    let desiredLen = randInt(3, 5); // 3 or 4
    info.innerText = "(\tGENERATING...\t)";
    getRandomWord(desiredLen).then
    (word => 
    {
        let len = word.length;
        info.innerText = "(\tDRAW: " + word + "\t)";
        guessReanimate();
        socket.emit('guess', {len});
    });
}


// Guesser button press
function onGuess(data)
{
    let len = "";
    for (let i = 0; i < data.len; i++)
    {
        len = len + "_ ";
    }
    info.innerText = "(\tGUESS: " + len + "\t)";
    guessReanimate();
}


function guessReanimate()
{
    info.style.animation = 'none';
    info.offsetHeight;
    info.style.animation = "pop 1s ease forwards";
}


// Guess pointer / cursor position on canvas
function getPosition(e) 
{
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches[0].clientX) - rect.left;
    const y = (e.clientY || e.touches[0].clientY) - rect.top;
    return { x, y };
}


// Begin drawing path
function onPress(e)
{
    pos = getPosition(e);
    lastX = pos.x;
    lastY = pos.y;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
}


// Actually draw on canvas, and EMIT on socket
function onMove(e)
{
    ctx.strokeStyle = userColor;
    ctx.lineWidth = userSize;
    pos = getPosition(e);
    x = pos.x;
    y = pos.y;

    if (erasing)
    {
        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath();
        ctx.arc(x, y, userSize / 2, 0, Math.PI * 2, false); // Draw a circle
        ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
    }

    else
    {
        ctx.lineTo(x, y);
        ctx.stroke();
    }

    let normX = x / canvas.width;
    let normY = y / canvas.height;

    let normLX = lastX / canvas.width;
    let normLY = lastY / canvas.height;
    
    // Emit the drawing data to other clients
    socket.emit('draw', { normX, normY, normLX, normLY, 
        userColor, userSize, erasing});
    
    // Update lastX and lastY
    lastX = x;
    lastY = y;
}


// Finished, check if others need to draw
function onUnpress(e)
{
    drawing = false;
    ctx.closePath();
    while (workQueue.length > 0)
    {
        (workQueue.pop())();
    }
    socket.emit('draw_done', {});
}


// Draw others
function otherDraw(data)
{
    ctx.strokeStyle = data.userColor;
    ctx.lineWidth = data.userSize;

    if (data.erasing)
    {
        let r = data.userSize / 2;
        let x = data.normLX * canvas.width;
        let y = data.normY * canvas.height;


        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2, false);
        ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
        return;    
    }


    ctx.beginPath();
    ctx.moveTo(data.normLX * canvas.width, data.normLY * canvas.height);
    ctx.lineTo(data.normX * canvas.width, data.normY * canvas.height);
    ctx.stroke();
    ctx.closePath();
}


// Draw others finished
function otherDrawDone(data)
{

}


// Random integer in range [min, max)
function randInt(min, max) 
{
    if (min === max) return max;
    if (min > max) return randInt(max, min);
    return Math.floor(Math.random() * (max - min) + min);
}


// Request random word by length
async function getRandomWord(len) 
{

    const url = 
    'https://random-word-api.vercel.app/api?words=1&length='
    + len
    + '&type=capitalized';
    const timeout = 2000;

    // Create a promise that fetches the random word
    const fetchPromise = fetch(url)
        .then(response => 
            {
            if (!response.ok) 
                {
                throw new Error('Network response was not ok');
                }
            return response.json();
        });

    // Create a timeout promise
    const timeoutPromise = new Promise((_, reject) => 
        {
        setTimeout(() => 
            {
            reject(new Error('Request timed out'));
            }, timeout);
    });

    try 
    {
        // Wait for either the fetch or the timeout
        const word = await Promise.race([fetchPromise, timeoutPromise]);
        return word[0];
    } 

    catch (error) 
    {
        console.error('Error:', error.message);
        return randomWordHardCoded();
    }
}


// Unable to get from API, get a random word from a list
function randomWordHardCoded()
{
    let words = ['Cat', 'Dog', 'Fish', 'Tree', 'Star',
         'Moon', 'Sun', 'Ball', 'Duck', 'Bear', 'Car',
          'Boat', 'House', 'Bird', 'Frog', 'Cake', 'Hat',
           'Pine', 'Rock', 'Bunny', 'Lion', 'Taco', 'Panda',
            'Sled', 'Skate', 'Ring', 'Flag', 'Wave', 'Cloud',
             'Bee', 'Ant', 'Egg', 'Cup', 'Sock', 'Nose', 'Foot',
              'Mug', 'Pail', 'Kite', 'Pond', 'Park', 'Road', 'Cave',
               'Nest', 'Drum', 'Pillow', 'Rocket', 'Monster', 'Guitar', 'Rainbow']

    return words[randInt(0, words.length)]
}


// Saves image locally
function saveAsPng(button)
{
    const link = document.createElement('a');
    let now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();

    link.download = `image-at-${hours}${minutes}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    disableXForYSec(button, 5000);
}


// Listeners - mouse press, mouse move, mouse up, socker events
function addEvents()
{
    canvas.addEventListener('mousedown', (e) => 
        {
            drawing = true;
            onPress(e);
        });
        
        canvas.addEventListener('mousemove', (e) => 
        {
            if (drawing) onMove(e);
        });

        /* Leave screen - cancel drawing */
        canvas.addEventListener('mouseleave', () => 
        {
            drawing = false;
            ctx.closePath();
        });
        
        canvas.addEventListener('mouseup', () => 
        {
            onUnpress();
        });

        // Touch events for mobile devices
        canvas.addEventListener('touchstart', (e) => 
        {
            e.preventDefault(); // Prevent scrolling
            drawing = true;
            onPress(e);
        });

        canvas.addEventListener('touchmove', (e) => 
        {
            if (!drawing) return;
            e.preventDefault(); // Prevent scrolling
            onMove(e);
        });

        canvas.addEventListener('touchend', () => 
        {
            onUnpress();
        });
        
        // Listen for drawing data from other clients
        socket.on('draw', (data) => 
        {
            var otherFunc = runnable(otherDraw, this, [data]);
            workQueue.push(otherFunc);
            while (!drawing && workQueue.length > 0)
            {
                (workQueue.pop())();
            }
        });

        // Listen for drawing data from other clients
        socket.on('clear', () => 
            {
                var otherFunc = runnable(onClear, this, []);
                workQueue.push(otherFunc);
                while (!drawing && workQueue.length > 0)
                {
                    (workQueue.pop())();
                }
            });

        socket.on('guess', (data) => 
            {
                onGuess(data);
            });


        // Press e, swap brush / eraser modes
        document.addEventListener('keydown', (event) => 
            {
                if (event.code === 'KeyE')
                    { onEraser(document.getElementById('eraser-button'));}
            });

        
}


console.log('JS End')