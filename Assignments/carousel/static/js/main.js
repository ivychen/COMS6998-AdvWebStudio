/* Formatting function for row details - modify as you need */
function format ( id ) {
  var div = $('<div/>')
      .addClass( 'loading' )
      .text( 'Loading...' );

  $.ajax( {
      url: '/productDetails',
      data: {
          id: id
      },
      headers: {"Content-Type": "application/json"},
      type: 'GET',
      success: function ( product ) {
        let prod = product.result[0];
        if (prod.description == null) {
          prod.description = "Description coming soon."
        }
        div
            .html('<div class="card"><div class="row "><div class="col-md-4">' +
                  '<a href="/product/' + prod.id + '"><img class="card-img-top product-img" src="' + prod.imgsrc + '" alt="Card image cap"></a>' +
                  '</div>' +
                  '<div class="col-md-8 px-3">' +
                  '<div class="card-block px-3">' +
                  '<h4 class="card-title"><a href="/product/' + prod.id + '">' + prod.name + '</a></h4>' +
                  '<p class="card-text">'+ prod.description + '</p>' +
                  '</div></div></div></div></div>')
            .removeClass( 'loading' );
      }
  });
  return div;
}

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

  // Autocomplete for form inputs
  $(function() {
    $.ajax({
      type: "POST",
      headers: {"Content-Type": "application/json"},
      url: '/autocomplete',
    }).done(function (data) {
      $('#autocomplete').autocomplete({
        source: data.matching_results,
        minLength: 2
      });
    });
  });

  $(function() {
    $.ajax({
      type: "POST",
      headers: {"Content-Type": "application/json"},
      url: '/autocomplete_category',
    }).done(function (data) {
      $('#category').autocomplete({
        source: data.matching_results,
        minLength: 2
      });
    });
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

  // === FORM VALIDATION ===
  window.addEventListener('load', function() {
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.getElementsByClassName('needs-validation');
    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function(form) {
      form.addEventListener('submit', function(event) {
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  }, false);

  // === DataTables ===
  var table = $('#myShelf').DataTable({
    paging: true,
    order: [[ 1, "asc" ]],
    select: {
      style: 'os',
      selector: 'td:first-child',
    },
    // columns: [
    //   {"name" : "brand"},
    //   {"name" : "name"},
    //   {"name" : "quantity"},
    //   {"name" : "rating"},
    // ],
    fnRowCallback: function (nRow, aData, iDisplayIndex, iDisplayIndexFull) {
      var setCell = function(response, newValue) {
        var table = new $.fn.dataTable.Api('.table');
        var cell = table.cell('td.focus');
        var cellData = cell.data();

        var div = document.createElement('div');
        div.innerHTML = cellData;
        var a = div.childNodes;
        a.innerHTML = newValue;

        console.log('inner' + div.innerHTML)
        console.log(a.innerHTML)
        console.log(cell)

        cell.data(a.innerHTML);
        highlightCell($(cell.node()));

        // This is huge cheese, but the a has lost it's editable nature.  Do it again.
        $('td.focus a').editable({
          'mode': 'inline',
          'success' : setCell
          });
      };
      $('.editable').editable(
        {
          'mode': 'inline',
          'success' : setCell
        }
      );
    }
  });

  // editable helpers
  addCellChangeHandler();
  function highlightCell($cell) {
    var originalValue = $cell.attr('data-original-value');
    if (!originalValue) {
        return;
    }
    var actualValue = $cell.text();
    if (!isNaN(originalValue)) {
        originalValue = parseFloat(originalValue);
    }
    if (!isNaN(actualValue)) {
        actualValue = parseFloat(actualValue);
    }
    if ( originalValue === actualValue ) {
        $cell.removeClass('cat-cell-modified').addClass('cat-cell-original');
    } else {
        $cell.removeClass('cat-cell-original').addClass('cat-cell-modified');
    }
  }

  function addCellChangeHandler() {
    $('a[data-pk]').on('hidden', function (e, editable) {
        var $a = $(this);
        var $cell = $a.parent('td');
        highlightCell($cell);
    });
  }

  // Add event listener for opening and closing details
  $('#myShelf tbody').on('click', 'td.details-control', function () {
      var tr = $(this).closest('tr');
      var row = table.row( tr );

      if ( row.child.isShown() ) {
          // This row is already open - close it
          row.child.hide();
          tr.removeClass('shown');
      }
      else {
          // Open this row
          console.log(tr.data('child-value'));
          row.child(format(tr.data('child-value'))).show();
          tr.addClass('shown');
      }
  });

  // rating
  $('.rating > .half, .rating > .full').on('click', function (e) {
    let id = $(this).attr('for');
    let rating = $('#'+id).attr('value');
    let productId = $(this).closest('tr').data('child-value');
    let username = $(this).closest('#myShelf').data('user');

    $.ajax({
      url: '/rateProduct',
      type: "POST",
      dataType:'json',
      contentType: "application/json",
      headers: {"Content-Type": "application/json"},
      data: JSON.stringify({
        username: username,
        rating: rating,
        productId: productId,
      }),
    }).done(function (data) {
      console.log('Successfully updated rating.')
    })
  });

  // editable
  $('#myShelf .editable').editable({
    type: 'text',
    quantity: 'Qty',
    url: '/shelf/updateQty',
    title: 'Updating editable quantity',
  })

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
