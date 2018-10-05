$(document).ready(function() {
  $('.modal-btn').click(function() {
    console.log("Modal clicked")
    var a = $(this).attr('data-target')
    console.log(a)
    $(a).modal('show')
  })
})
