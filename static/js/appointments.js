function buttonInits(allAppts) {

    $('#editBookingModal').hide();
    
    // Show the booking form when the "Make a Booking" button is clicked
    $('.apptBtn').click(function() {
        console.log("make appt button pressed")
      $('#bookingModal').show();
      $('.nobookings').hide();
    });


    // To hide displayed appt for edit appt form to show up
    /*  $('.editAppt').click(function () {
        
         // Get the parent element's ID attribute, which contains the appointment ID
        var apptId = $(this).closest('.displayAppts').attr('id');

        // Set the appointment ID value in the modal form
        
        $('#editApptId').val(apptId);
        $('#editBookingModal').show();
        $('#apptsRows').hide();


    }); */

}
