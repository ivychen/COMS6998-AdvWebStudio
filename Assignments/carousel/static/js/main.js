$(document).ready(function() {
  var socket = io.connect('http://127.0.0.1:5000');

  socket.on('connect', function() {
    // console.log('User has connected!');
  });

  socket.on('message', function(msg) {
    $("#messages").prepend('<li><a href="/messages/' + msg.sender + '">' + msg.sender + '</a>' + " [" + msg.timestamp + "]: " + msg.message +
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
      "replyto": $('#to').val(),
    }
    socket.emit('message', payload);
    $('#myReply').val('');
  });

  // Infinite scroll for messsages
  $('.main.product-container').infiniteScroll({
    // options
    path: '/?page={{#}}',
    append: '.product-item',
    history: false,
    prefill: true,
  });

  // Save message to user's personal list
  $('#messages').on('click', ".save", function(e) {
    e.stopPropagation();
    e.stopImmediatePropagation();
    let messageId = $(this).attr('data-id');
    let payload = {
      "messageId": messageId,
      "user": $('#sender').val(),
    }
    console.log(payload);
    socket.emit('save', payload);
  });

  // === MUURI
  var itemContainers = [].slice.call(document.querySelectorAll('.board-column-content'));
  var columnGrids = [];
  var boardGrid;

  // Define the column grids so we can drag those
  // items around.
  itemContainers.forEach(function (container) {

    // Instantiate column grid.
    var grid = new Muuri(container, {
      items: '.board-item',
      layoutDuration: 400,
      layoutEasing: 'ease',
      dragEnabled: true,
      dragSort: function () {
        return columnGrids;
      },
      dragSortInterval: 0,
      dragContainer: document.body,
      dragReleaseDuration: 400,
      dragReleaseEasing: 'ease'
    })
    .on('dragStart', function (item) {
      // Let's set fixed widht/height to the dragged item
      // so that it does not stretch unwillingly when
      // it's appended to the document body for the
      // duration of the drag.
      item.getElement().style.width = item.getWidth() + 'px';
      item.getElement().style.height = item.getHeight() + 'px';
    })
    .on('dragReleaseEnd', function (item) {
      // Let's remove the fixed width/height from the
      // dragged item now that it is back in a grid
      // column and can freely adjust to it's
      // surroundings.
      item.getElement().style.width = '';
      item.getElement().style.height = '';
      // Just in case, let's refresh the dimensions of all items
      // in case dragging the item caused some other items to
      // be different size.
      columnGrids.forEach(function (grid) {
        grid.refreshItems();
      });
    })
    .on('layoutStart', function () {
      // Let's keep the board grid up to date with the
      // dimensions changes of column grids.
      boardGrid.refreshItems().layout();
    });

    // Add the column grid reference to the column grids
    // array, so we can access it later on.
    columnGrids.push(grid);

  });

  // Instantiate the board grid so we can drag those
  // columns around.
  boardGrid = new Muuri('.board', {
    layoutDuration: 400,
    layoutEasing: 'ease',
    dragEnabled: true,
    dragSortInterval: 0,
    dragStartPredicate: {
      handle: '.board-column-header'
    },
    dragReleaseDuration: 400,
    dragReleaseEasing: 'ease'
  });

});
