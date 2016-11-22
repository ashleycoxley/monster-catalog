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

function checkIfEmpty(field) {
    var value = field.val();
    if (!value) {
        field.closest('.form-group').addClass('has-danger');
    } else {
        field.closest('.form-group').removeClass('has-danger');
        return value;
    }
}

$(document).ready(function(e) {
    var canvas = $('#monster-canvas');
    var context = canvas.get(0).getContext('2d');
    // Check for previously defined image (in edit case)
    var prevImageUrl = canvas.data('previmage');
    if (prevImageUrl) {
        var prevMonsterImage = new Image();
        prevMonsterImage.setAttribute('crossOrigin', 'anonymous');
        prevMonsterImage.src = prevImageUrl;
        prevMonsterImage.onload = function() {
            context.drawImage(prevMonsterImage,0,0);
        };
    }

    var drawing = false;

    $('.pencil-color').click(function(){
        pencilColor = $(this).css('backgroundColor');
        $('.fa-pencil').css('color', pencilColor);
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
        var nameInput = $('input[name=name]');
        var dietInput = $('textarea[name=diet]');
        var enjoysInput = $('textarea[name=enjoys]');
        var intentionsInput = $('select[name=intentions]');

        var name = checkIfEmpty(nameInput);
        var diet = checkIfEmpty(dietInput);
        var enjoys = checkIfEmpty(enjoysInput);
        var intentions = intentionsInput.val(); // Has default value of "Good"

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

        addMonsterUrl = window.location.pathname;

        var postData = $.post(addMonsterUrl, data);

        // Redirect to main page with message once submitted
        postData.done(function(response) {
            if (response['result'] === 'success') {
                if (response['insert_or_update'] === 'insert') {
                    window.location.href = '/?action=monster_add&result=alert-success';
                } else if (response['insert_or_update'] === 'update') {
                    window.location.href = '/?action=monster_edit&result=alert-success';
                } else {
                    window.location.href = '/';
                }
                
            } else {
                if (response['insert_or_update'] === 'insert') {
                    window.location.href = '/?action=monster_add&result=alert-danger';
                } else if (response['insert_or_update'] === 'update') {
                    window.location.href = '/?action=monster_edit&result=alert-danger';
                } else {
                    window.location.href = '/';
                }
            }
        });

        e.preventDefault();
        return false;
    });
});