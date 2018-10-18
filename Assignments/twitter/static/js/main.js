$(document).ready(function() {
  var socket = io.connect('http://127.0.0.1:5000');
  socket.on('connect', function() {
    console.log('User has connected!');
  });
  socket.on('message', function(msg) {
    $("#messages").append('<li><a href="/messages/' + msg.sender + '">' + msg.sender + '</a>' + " [" + msg.timestamp + "]: " + msg.message +
    '<p><button data-username="' + msg.sender + '" data-id="' + msg.id +
    '" data-message="' + msg.message + '" class="btn btn-outline-secondary reply">Reply</button></p>' +
    '</li>');
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
  $('#messages').on('click', ".reply", function(e) {
    e.stopPropagation();
    e.stopImmediatePropagation();
    $('#replyto').val($(this).attr('data-id'));
    $('#to').text("To: " + $(this).attr('data-username') + ' "' + $(this).attr('data-message') + '"')
  });
  $('#replyButton').on('click', function() {
    let payload = {
      "message": $('#myReply').val(),
      "timestamp": new Date(),
      "sender": $('#sender').val(),
      "replyto": $('#replyto').val(),
    }
    socket.emit('message', payload);
    $('#myReply').val('');
  });
});
