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
const brushSize = 1;
const eraserColor = 'rgb(30, 30, 30)';
const eraserSize = 10;
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

function onClear()
{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.style.animation = 'none'; // Remove the animation
    canvas.offsetHeight; // Trigger reflow
    canvas.style.animation = ''; // Reapply the 
}

function onClearOrigin()
{
    onClear();
    socket.emit('clear', {});
}

function onEraser(button)
{
    erasing = !erasing;
    if (erasing)
    {
        userColor = eraserColor;
        userSize = eraserSize;
        button.innerText = "BRUSH";
    }
    else
    {
        userColor = brushColor;
        userSize = brushSize;
        button.innerText = "ERASER";
    }
}

function getPosition(e) 
{
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches[0].clientX) - rect.left;
    const y = (e.clientY || e.touches[0].clientY) - rect.top;
    return { x, y };
}

function onPress(e)
{
    pos = getPosition(e);
    lastX = pos.x;
    lastY = pos.y;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
}

function onMove(e)
{
    ctx.strokeStyle = userColor;
    ctx.lineWidth = userSize;
    pos = getPosition(e);
    x = pos.x;
    y = pos.y;
    ctx.lineTo(x, y);
    ctx.stroke();

    let normX = x / canvas.width;
    let normY = y / canvas.height;

    let normLX = lastX / canvas.width;
    let normLY = lastY / canvas.height;
    
    // Emit the drawing data to other clients
    socket.emit('draw', { normX, normY, normLX, normLY, userColor, userSize});
    
    // Update lastX and lastY
    lastX = x;
    lastY = y;
}

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

function otherDraw(data)
{
    ctx.strokeStyle = data.userColor;
    ctx.lineWidth = data.userSize;
    ctx.beginPath();
    ctx.moveTo(data.normLX * canvas.width, data.normLY * canvas.height);
    ctx.lineTo(data.normX * canvas.width, data.normY * canvas.height);
    ctx.stroke();
    ctx.closePath();
}

function otherDrawDone(data)
{

}

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

        
}




console.log('JS End')