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
            .html('<div class="card"><div class="row "><div class="col-md-4 image">' +
                  '<a href="/product/' + prod.id + '"><img class="card-img-top" src="' + prod.imgsrc + '" alt="Card image cap"></a>' +
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

  // Infinite scroll for messsages
  $('.main.product-container').infiniteScroll({
    // options
    path: '/?page={{#}}',
    append: '.product-item',
    history: false,
    prefill: true,
  });

  $('.browse.product-container').infiniteScroll({
    // options
    path: 'browse?page={{#}}',
    append: '.product-item',
    history: false,
    prefill: true,
  });

  // Autocomplete for form inputs
  // autocomplete brand
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

  $(function() {
    $.ajax({
      type: "POST",
      headers: {"Content-Type": "application/json"},
      url: '/autocomplete_all',
    }).done(function (data) {
      $('#query').autocomplete({
        source: data.matching_results,
        minLength: 2,
        max: 10
      });
    });
  });

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

  $('.recommend').on('click', function (e) {
    e.preventDefault()
    let category = $(this).data('category');

    $.ajax({
      url: '/recommend',
      type: "POST",
      dataType:'json',
      contentType: "application/json",
      headers: {"Content-Type": "application/json"},
      data: JSON.stringify({
        category: category,
      }),
      success: function (data) {
        $('#exampleModalLongTitle').text("Top Picks for " + category)

        let recHTML = '<ul id="products" class="browse product-container card-grid" style="justify-content:space-evenly;">'
        let recs = data.recommendations
        let empty = data.empty

        if (empty) {
          console.log(recs)
          $(".modal-content .psa").html('<div class="row mt-3">Whoops - we don\'t have recommendations, but try some of these!</div>')

          recs.forEach(function (prod) {
            recHTML = recHTML +
            '<li class="product-item">' +
            '<div class="card modal-card">' +
            '<a href="/product/' + prod.id + '">' +
            '<img class="card-img-top" src="' + prod.imgsrc + '"></a>' +
            '<div class="card-body"><p class="card-text">' + prod.brand + '</p>' +
            '<h5 class="card-title"><a href="/product/' + prod.id + '">' + prod.name + '</a></h5><i style="color:#f5a800;" class="fas fa-star"></i><span class="mini">No Ratings</span>' + '</div></div></li>'
          })
          recHTML = recHTML + '</ul>'
        } else {
          recs.forEach(function (prod) {
            recHTML = recHTML +
            '<li class="product-item">' +
            '<div class="card modal-card">' +
            '<a href="/product/' + prod.id + '">' +
            '<img class="card-img-top" src="' + prod.imgsrc + '"></a>' +
            '<div class="card-body"><p class="card-text">' + prod.brand + '</p>' +
            '<h5 class="card-title"><a href="/product/' + prod.id + '">' + prod.name + '</a></h5><i style="color:#f5a800;" class="fas fa-star"></i><span class="mini">' + prod.rating.toFixed(2) + '</span></div></div></li>'
          })
          recHTML = recHTML + '</ul>'
        }

        $("#exampleModalCenter .modal-body").html(recHTML)

      }
    }).done(function (data) {
      console.log('Successfully recommended.')
    })
  })

  // editable
  $('#myShelf .editable').editable({
    type: 'text',
    quantity: 'Qty',
    url: '/shelf/updateQty',
    title: 'Updating editable quantity',
  })
});
