$(document).ready(function() {
  var socket = io.connect('http://127.0.0.1:5000');
  socket.on('connect', function() {
    console.log('User has connected!');
  });
  socket.on('message', function(msg) {
    $("#messages").append('<li><a href="/messages/' + msg.sender + '">' + msg.sender + '</a>' + " [" + msg.timestamp + "]: " + msg.message+'</li>');
    console.log('Received message');
  });
  $('#sendbutton').on('click', function() {
    let payload = {
      "message": $('#myMessage').val(),
      "timestamp": new Date(),
      "sender": $('#sender').val(),
      "replyto": "",
    }
    socket.emit('message', payload);
    $('#myMessage').val('');
  });
});
