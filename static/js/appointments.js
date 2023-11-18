$(document).ready(function () {

  showAppointmentModal();
  editAppointment();
  deleteAppointment();

});

function showAppointmentModal() {
  // Event delegation for the table with a class "agents-table"
  $('.agents-table').on('click', '.make-appointment-btn', function () {
    const agentName = $(this).data('agent-name');

    // Show the modal form
    $('#appointmentModal').modal('show');

    // Use agentId to fetch the agent's name from the server/database
    // Then, populate the form with the agent's name
    $('#agentName').val(agentName);
  });
}

function editAppointment() {
  $('.bookings-table').on('click', '.edit-appointment-btn', function () {
    // Retrieve data attributes
    var apptId = $(this).data('appointment-id');
    var dateTimeString = $(this).data('date-time');
    var agentName = $(this).data('agent-name');

    // Convert dateTimeString to a JavaScript Date object
    var dateTime = new Date(dateTimeString);

    // Extract date and time components
    var date = dateTime.toISOString().split('T')[0];  // Get the date part
    var time = dateTime.toTimeString().split(' ')[0];  // Get the time part

    // Set values in the form
    $('#agentName').val(agentName);
    $('#apptDate').val(date);
    $('#apptTime').val(time);

    // Set the apptId value in the hidden input field
    $('#apptId').val(apptId);

    // Show the modal form
    $('#editAppointmentModal').modal('show');
  });
}


function deleteAppointment() {

  $('.bookings-table').on('click', '.delete-appointment-btn', function () {
    var apptId = $(this).data('appointment-id');

    $.ajax({
      type: 'POST',
      url: '/delete-appointment',
      data: { 'apptId': apptId },
      success: function (response) {
        if (response.status === 'success') {
          location.reload();  // Reload the page
        } else {
          alert(response.message);  // Display error message
        }
      },
      error: function () {
        alert('Error deleting appointment');
      }
    });

  });

};
