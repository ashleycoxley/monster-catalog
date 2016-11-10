var xPrev = -1;
var yPrev = -1;
var pencilColor = 'black';

function draw(x, y, context, pencilColor) {
    context.strokeStyle = pencilColor;
    context.lineCap = "round";
    context.beginPath();
    context.moveTo(xPrev, yPrev);
    context.lineTo(x, y);
    // Make white (eraser) wider
    if (pencilColor == 'rgb(255, 255, 255)') {
        context.lineWidth = 6;
    } else {
        context.lineWidth = 3;
    }
    context.stroke();
    context.closePath();
    xPrev = x;
    yPrev = y;
}

$(document).ready(function(e) {
    var canvas = $('#monster-canvas');
    var context = canvas.get(0).getContext('2d');
    var drawing = false;

    $('.pencil-color').click(function(){
        pencilColor = $(this).css('backgroundColor');
    });

    $('#clear-canvas').click(function(e) {
        e.preventDefault();
        context.clearRect(0, 0, canvas.width(), canvas.height());
    });

    canvas.mousedown(function(){
        drawing = true;
    });

    canvas.mousemove(function(event){
        if (!drawing) {
            return;
        }
        x = event.offsetX;
        y = event.offsetY;

        if (xPrev == -1) {
            xPrev = x;
            yPrev = y;
        }

        var context = canvas.get(0).getContext('2d');
        draw(x, y, context, pencilColor);
    });

    canvas.mouseup(function(){
        drawing = false;
        xPrev = -1;
        yPrev = -1;
    });

    canvas.mouseout(function(){
        drawing = false;
        xPrev = -1;
        yPrev = -1;
    });

    $('#create-monster').click(function(e) {
        var name = $('input[name=name]').val();
        var diet = $('textarea[name=diet]').val();
        var enjoys = $('textarea[name=enjoys]').val();
        var intentions = $('select[name=intentions]').val();
        var pictureUrl = canvas[0].toDataURL();
        
        // base64 encoding from http://jsfiddle.net/jasdeepkhalsa/l5hmw/
        var encodedPicture = pictureUrl.replace(/^data:image\/(png|jpg);base64,/, "");
        
        data = {
            'name': name,
            'diet': diet,
            'enjoys': enjoys,
            'intentions': intentions,
            'encoded_picture': encodedPicture
        };

        addMonsterUrl = '/create';

        var postData = $.post(addMonsterUrl, data);

        // Redirect to main page once submitted
        postData.done(function(response) {
            console.log(response);
            if (response['result'] === 'success') {
                window.location.href = '/';
            } else {
                // TODO: better error handling here
                console.log('error');
            }
        });

        e.preventDefault();
        return false;
    });
});