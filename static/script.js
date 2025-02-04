/* Join & Host */
let numPadInput = '';
let numPadInfo = null;
let roomLocked = false;

/* Canvas, socket, guesser */
let canvas = null;
let otherCanvas = null;
let otherCanvasChanged = false;
let canvasActive = false;
let intervalId = null;
let ctx = null;
let socket = null;
let guessPara = null;
let myNickname = null;

/* Drawing vars */
let erasing = false;
let drawing = false;
let lastX = 0;
let lastY = 0;
const brushColor = '#dcdcdc';
const brushSize = 1;
const eraserSize = 40;
let userColor = brushColor;
let userSize = brushSize;
let eraserRad = 0;

let mobile_width = 300;


/* Work queue, to let other clients erase canvas */
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
    numPadInfo = elem('num-pad-info');
    canvas = document.getElementById('canvas');
    otherCanvas = document.createElement('canvas');
    setCanvasSize(canvas);

    ctx = canvas.getContext('2d');
    otherCtx = otherCanvas.getContext('2d');
    guessPara = this.document.getElementById('info-el');

    // Add bright random color generation (?)
    ctx.strokeStyle = userColor;
    socket = io();
    addEvents();
});


// Set canvas size, based on page size (phone / pc)
function setCanvasSize(canvas)
{
    if (window.innerWidth <= 600) 
    {
        canvas.width = mobile_width;
        canvas.height = 200;
        
    } 
    else 
    {
        canvas.width = 800;
        canvas.height = 600;
    }
    otherCanvas.width = canvas.width;
    otherCanvas.height = canvas.height;
    eraserRad = canvas.width / 32;
}


// Copies otherCanvas into Canvas
// Copies canvas as seen from server locally every X ms
// not exactly merges then
function mergeCanvases()
{
    if (otherCanvasChanged)
    {
        ctx.drawImage(otherCanvas, 0, 0);
        otherCtx.clearRect(0, 0, canvas.width, canvas.height);
        otherCanvasChanged = false;
    }
}


//
function onHost(button)
{
    // button.innerText = 'HOSTING' todo find animation 
    socket.emit('host');
    disableXForYSec(button, 10000);
}


//
function onJoin(button)
{
    let numPad = elem('join-pad');
    if (!(numPad.style.display === 'none')) return;
    numPad.style.display = 'grid';
    divReanimate(numPad);
}


//
function numPadClick(button, num)
{
    buttonPop(button);
    if (num === 10) // DEL
    {
        if (numPadInput.length === 0){ return;}
        numPadInput = numPadInput.substring(0, numPadInput.length - 1);
        numPadInfo.innerText = numPadInput;
        return;
    }
    if (num === 11) // OK
    {
        if (numPadInput.length != 6)
        {
            numPadInfo.innerText = "Six digits required.";
            disableXForYSec(button, 1000);
            return;
        }
        socket.emit('join', {code : numPadInput});
        disableXForYSec(button, 5000);
        return;
    }
    if (num < 0 || num > 9) // UNEXPECTED 
    {
        return;
    }
    if (numPadInput.length >= 6) return;
    numPadInput = numPadInput + num;
    numPadInfo.innerText = numPadInput;
    divReanimate(numPadInfo);
}


//
function onJoinFail(button)
{
    alert("Wrong format.");
    disableXForYSec(button, 2000);
}


// Someone else pressed clear
function onClear()
{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    otherCtx.clearRect(0, 0, canvas.width, canvas.height);
    divReanimate(canvas);
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
        canvas.classList.add('eraser-active');
    }
    else
    {
        userSize = brushSize;
        button.innerText = "[E]RASER";
        canvas.classList.remove('eraser-active');
    }

    // todo replace with buttonPop()
    button.style.animation = 'none';
    button.offsetHeight;
    button.style.animation = "pop 0.2s ease forwards";
}


// Guesser button press
function onGuessOrigin(button)
{
    let desiredLen = randInt(3, 7); // 3, 4, 5, 6
    guessPara.innerText = "(\tGENERATING...\t)";
    getRandomWord(desiredLen).then
    (word => 
    {
        let len = word.length;
        guessPara.innerText = "(\tDRAW: " + word + "\t)";
        guessReanimate();
        socket.emit('guess', {len});
    });
    disableXForYSec(button, 1000);
}


// Guesser button press
function onGuess(data)
{
    let len = "";
    for (let i = 0; i < data.len; i++)
    {
        len = len + "_ ";
    }
    guessPara.innerText = "(\tGUESS: " + len + "\t)";
    guessReanimate();
}


// Todo, maybe delete?
function guessReanimate()
{
    guessPara.style.animation = 'none';
    guessPara.offsetHeight;
    guessPara.style.animation = "pop 1s ease forwards";
}


// Gives a pop animation to a div
function divReanimate(div)
{
    div.style.animation = 'none';
    div.offsetHeight;
    div.style.animation = "pop 0.5s ease forwards";
}


// DRAW - Guess pointer / cursor position on canvas
function getPosition(e) 
{
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches[0].clientX) - rect.left;
    const y = (e.clientY || e.touches[0].clientY) - rect.top;
    return { x, y };
}


// DRAW - Begin drawing path
function onPress(e)
{
    pos = getPosition(e);
    lastX = pos.x;
    lastY = pos.y;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
}


// DRAW - Actually draw on canvas, and EMIT on socket
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
        ctx.arc(x, y, eraserRad, 0, Math.PI * 2, false);
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


// DRAW - Finished, check if others need to draw
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


// DRAW - Draw others
function otherDraw(data)
{
    // Erasing, push work to queue
    if (data.erasing)
    {
        var otherFunc = runnable(otherErase, this, [data]);
        workQueue.push(otherFunc);
        return;    
    }

    // Drawing, can draw on the hidden canvas at the same time
    otherCtx.strokeStyle = data.userColor;
    otherCtx.lineWidth = data.userSize;
    otherCtx.beginPath();
    otherCtx.moveTo(data.normLX * canvas.width, data.normLY * canvas.height);
    otherCtx.lineTo(data.normX * canvas.width, data.normY * canvas.height);
    otherCtx.stroke();
    otherCtx.closePath();
    otherCanvasChanged = true;
}


function otherErase(data)
{
    let x = data.normLX * canvas.width;
    let y = data.normY * canvas.height;
    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.arc(x, y, eraserRad, 0, Math.PI * 2, false);
    ctx.fill();
    ctx.globalCompositeOperation = 'source-over';
    return;    
}


// DRAW - Draw others finished
function otherDrawDone(data)
{

}


// GUESSER - Random integer in range [min, max)
function randInt(min, max) 
{
    if (min === max) return max;
    if (min > max) return randInt(max, min);
    return Math.floor(Math.random() * (max - min) + min);
}


// GUESSER - Request random word by length
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


// GUESSER - Unable to get from API, get a random word from a list
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


// SAVE - Saves image locally
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


// LEAVE - Leaves room
function leaveRoom(button)
{
    // Reset buttons
    elem('lock-but').innerText = 'LOCK';

    // Canvas & Info
    elem('content').style.display = 'none';
    elem('content-info').style.display = 'none';
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvasActive = false;
    clearInterval(intervalId);

    // Host & Join 
    elem('starter-div').style.display = 'block';
    elem('room-info-el').innerText = '';

    // Notify others
    socket.emit('leave');
}


// LOCK - reques to lock or unlock room 
function onLockOrigin(button)
{
    socket.emit('lock');
}

// LOCK - handle request from others
function onLock(data)
{
    roomLocked = data.lock;
    button = elem('lock-but');
    if (roomLocked)
    {
        button.innerText = 'UNLOCK';
    }
    else
    {
        button.innerText = 'LOCK';
    }
    divReanimate(button);
    disableXForYSec(button, 5000);
}


// HOST, OTHERS JOIN, OTHERS LEAVE
function initializeUserList(userList)
{
    let div = '<div> [User List]\n';
    userList.forEach((val) => 
        {
            item = val + '</div>\n';
            if (val === myNickname)
            {
                div = div + '  <div style="font-weight:bold;">' + item; 
            }
            else
            {
                div = div + '  <div>' + item;
            }
        });
    div = div + '</div>'
    
    let ul = elem('user-list');
    ul.innerHTML = div;
    ul.style.color = 'gainsboro';
}


// SOCKET EVENTS
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
            // Draw on hidden canvas & Queue deletion
            otherDraw(data);

            // Queue for deletion
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


        // Start actual content
        socket.on('room_code', (data) => 
            {

                // Error
                if (data.code === '-1') 
                {
                    numPadInfo.innerText = data.message;
                    divReanimate(numPadInfo);
                    return;
                }


                // Get code + my nick
                currentRoom = data.code;
                myNickname = data.my_nick;
                
                // Get users
                let userList = data.users;
                initializeUserList(userList);

                // Display divs
                elem('room-info-el').innerText = "Room code: " + currentRoom;

                // Host & Join hide
                elem('starter-div').style.display = 'none';

                // Canvas + info show
                elem('content').style.display = 'flex';
                if (canvas.width <= mobile_width)
                {
                    elem('content').style.flexDirection = 'column';
                }
                elem('content-info').style.display = 'block';
                canvasActive = true;
                intervalId = setInterval(mergeCanvases, 20);
        });

        // Other join / left
        socket.on('room_update', (data) =>
        {
            let userList = data.users;
            let myIndex = data.my_index;
            initializeUserList(userList, myIndex);
        });

        // Lock request
        socket.on('lock', (data) =>
            {
                onLock(data);
            });

        // Press e, swap brush / eraser modes
        document.addEventListener('keydown', (event) => 
            {
                if (event.code === 'KeyE')
                    { onEraser(document.getElementById('eraser-button'));}
            });
}


// Returns element by id
function elem(str)
{
    return document.getElementById(str);
}


// Returns element by class
function elemC(str)
{
    return document.getElementsByClassName(str);
}


//
function buttonPop(button)
{
    button.style.animation = 'none';
    button.offsetHeight;
    button.style.animation = "pop 0.2s ease forwards";
}
