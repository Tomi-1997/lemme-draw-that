console.log('JS Starting')


/* Initialize on load */
let canvas = null;
let ctx = null;
let socket = null;

let drawing = false;
let lastX = 0;
let lastY = 0;

/* On load */
window.addEventListener('load', function() 
{
    canvas = document.getElementById('canvas');
    ctx = canvas.getContext('2d');
    socket = io();
    addEvents();
});

function addEvents()
{
    canvas.addEventListener('mousedown', (e) => 
        {
            drawing = true;
            lastX = e.clientX - canvas.offsetLeft;
            lastY = e.clientY - canvas.offsetTop;
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
        });
        
        canvas.addEventListener('mousemove', (e) => 
            {
            if (drawing) 
                {
                    const x = e.clientX - canvas.offsetLeft;
                    const y = e.clientY - canvas.offsetTop;
                    ctx.lineTo(x, y);
                    ctx.stroke();
                    
                    // Emit the drawing data to other clients
                    socket.emit('draw', { x, y, lastX, lastY });
                    
                    // Update lastX and lastY
                    lastX = x;
                    lastY = y;
            }
        });

        /* Leave screen - cancel drawing */
        canvas.addEventListener('mouseleave', () => 
            {
            drawing = false;
            ctx.closePath();
        });
        
        canvas.addEventListener('mouseup', () => 
            {
            drawing = false;
            ctx.closePath();
        });
        
        // Listen for drawing data from other clients
        socket.on('draw', (data) => {
            ctx.beginPath();
            ctx.moveTo(data.lastX, data.lastY);
            ctx.lineTo(data.x, data.y);
            ctx.stroke();
        });
        
}




console.log('JS End')