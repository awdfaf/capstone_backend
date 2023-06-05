var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', function() {
    document.getElementById('start_image').addEventListener('click', function() {
        socket.emit('start_checking');
    });
    document.getElementById('stop_image').addEventListener('click', function() {
        socket.emit('stop_checking');
    });
    document.getElementById('clear_image').addEventListener('click', function() {
        socket.emit('clear_images');
    });

    document.getElementById('start_sound').addEventListener('click', function() {
        socket.emit('start_checking_');
    });
    document.getElementById('stop_sound').addEventListener('click', function() {
        socket.emit('stop_checking_');
    });
    document.getElementById('clear_sound').addEventListener('click', function() {
        socket.emit('clear_images_');
    });
});
socket.on('new_image', function(data) {
    var img = document.createElement('img');
    img.src = 'data:image/jpeg;base64,' + data.image;
    var card = document.createElement('div');
    card.className = 'card';
    card.appendChild(img);
    var cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    card.appendChild(cardBody);
    var timeGPS = document.createElement('p');
    timeGPS.className = 'card-text';
    timeGPS.textContent = 'Time: ' + new Date().toLocaleString();  // Update this line once you have actual time and GPS values.
    cardBody.appendChild(timeGPS);
    document.getElementById('images').prepend(card);
});


socket.on('new_result', function(data) {
    document.getElementById('result').innerHTML = "소리가 나는 방향은 " + data.result + " 방향 입니다.";

    // // Create a new audio element
    // const audio = document.createElement('audio');
    // audio.controls = true;

    // // Create a new source element
    // const source = document.createElement('source');
    // source.src = 'data:audio/wav;base64,' + data.data;
    // source.type = 'audio/wav';

    // // Append the source to the audio
    // audio.appendChild(source);

    // // Get the audio player container
    // const playerContainer = document.getElementById('audioPlayerContainer');

    // // Clear the audio player container
    // playerContainer.innerHTML = '';

    // // Append the new audio player
    // playerContainer.appendChild(audio);
});

socket.on('clear_audio', function() {
    // Get the audio player container
    const playerContainer = document.getElementById('audioPlayerContainer');

    // Clear the audio player container
    playerContainer.innerHTML = '';
});
